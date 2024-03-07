import bs4
import re
import asyncio
import os
from multiprocessing import cpu_count
from vermils.io import aio
from pydantic import Field
from ..context import Context
from .base import BaseInstaller

ver_re = re.compile(r"^(\d+\.\d+\.\d+)$")


class GeoIP2Installer(BaseInstaller):
    enabled: bool = False
    dynamic: bool = False
    account_id: str = ''
    license_key: str = ''
    edition_ids: list[str] = Field(
        default_factory=lambda:
        ["GeoLite2-ASN", "GeoLite2-City", "GeoLite2-Country"]
    )
    enable_auto_update: bool = True
    auto_update_cron: str = "0 0 * * 0"
    configure_opts: list[str] = Field(default_factory=list)

    @property
    def ngx_modulename(self) -> str:
        return "ngx_http_geoip2_module"

    async def _build_maxminddb(self, ctx: Context):  # skipcq: PY-R1000
        logger = ctx.logger
        client = ctx.client
        r = await client.get(
            "https://github.com/maxmind/libmaxminddb/releases/latest",
            follow_redirects=True,
        )
        r.raise_for_status()

        soup = bs4.BeautifulSoup(r.content, "lxml")
        v = ''
        for h1 in soup.find_all("h1"):
            m = ver_re.match(h1.text.strip())
            if m:
                v = m.group(1)
                break
        if not v:
            raise RuntimeError(f"{self}: Failed to find latest version")

        logger.debug("%s: Latest libmaxminddb version: %s", self, v)
        tar_path = ctx.build_dir / f"libmaxminddb-{v}.tar.gz"
        await ctx.download(
            "https://github.com/maxmind/libmaxminddb/releases/download/"
            f"{v}/libmaxminddb-{v}.tar.gz",
            tar_path,
            title="Get libmaxminddb source",
        )
        rs = await ctx.run_cmd(
            f"tar -xzf '{tar_path}' -C '{ctx.build_dir}' "
            f"&& cd 'build/libmaxminddb-{v}' "
            f"&& ./configure {' '.join(self.configure_opts)} "
            f"&& make -j {cpu_count()} "
            "&& make check "
            "&& make install "
            "&& cd - "
        )
        rs.raise_for_returncode()

        rs = await ctx.run_cmd("ldconfig")
        if rs.failed:
            logger.warning(
                "%s: Failed to run initial ldconfig because of %s, "
                "try to add ld config",
                self, await rs.get_error_str())
            if not ctx.dry_run:
                async with aio.open("/etc/ld.so.conf.d/local.conf", "a+") as f:
                    if "/usr/local/lib" not in await f.read():
                        await f.write("/usr/local/lib\n")
            rs = await ctx.run_cmd("ldconfig")
            rs.raise_for_returncode()

    async def _get_db(
            self, ctx: Context, account_id: str, license_key: str) -> list[str]:
        logger = ctx.logger
        if not account_id or not license_key:
            logger.warning(
                "%s: Account ID and License Key are not set, "
                "skipping downloading GeoIP2 databases", self)
            return []

        logger.debug("%s: Downloading GeoIP2 databases", self)
        edition_ids = self.edition_ids
        downloads = list[asyncio.Task]()
        for eid in edition_ids:
            loop = asyncio.get_running_loop()
            downloads.append(
                loop.create_task(
                    ctx.download(
                        "https://download.maxmind.com/app/geoip_download?"
                        f"edition_id={eid}&license_key={license_key}"
                        "&suffix=tar.gz",
                        ctx.build_dir / f"{eid}.tar.gz",
                        title=f"Get {eid}"
                    ))
            )
        await asyncio.gather(*downloads)

        for eid in edition_ids:
            path_prefix = ctx.build_dir / eid
            rs = await ctx.run_cmd(
                f"tar -xzf '{path_prefix}.tar.gz' -C '{ctx.build_dir}' "
                f"&& cp -rf '{path_prefix}_'* /opt/geoip"
            )
            rs.raise_for_returncode()

        return edition_ids

    async def _enable_auto_update(
            self, ctx: Context, account_id: str,
            license_key: str, edition_ids: list[str]
    ):
        logger = ctx.logger
        logger.debug("%s: Installing geoipupdate", self)
        rs = await ctx.run_cmd(
            "apt update && apt install -y geoipupdate"
        )
        rs.raise_for_returncode()

        conf = (
            f"AccountID {account_id}\n"
            f"LicenseKey {license_key}\n"
            f"EditionIDs {' '.join(edition_ids)}\n"
        )
        logger.debug("%s: Writing GeoIP2.conf", self)
        if not ctx.dry_run:
            async with aio.open("/usr/local/etc/GeoIP.conf", "w") as f:
                await f.write(conf)
        rs = await ctx.run_cmd(
            f"echo \"{self.auto_update_cron} `which geoipupdate`\" "
            "> /etc/cron.d/geoipupdate"
        )
        rs.raise_for_returncode()

    async def prepare(self, ctx):
        logger = ctx.logger
        logger.debug("%s: Preparing GeoIP2 installer", self)

        account_id = os.environ.get("MAXMIND_ID", self.account_id)
        license_key = os.environ.get("MAXMIND_KEY", self.license_key)

        await self._build_maxminddb(ctx)
        edition_ids = await self._get_db(ctx, account_id, license_key)

        if edition_ids and self.enable_auto_update:
            await self._enable_auto_update(
                ctx, account_id, license_key, edition_ids)

        # Download module source
        path = ctx.build_dir / "ngx_http_geoip2_module"
        logger.debug("%s: Cloning GeoIP2 module into %s", self, path)
        await ctx.git_clone(
            "https://github.com/leev/ngx_http_geoip2_module.git",
            path,
            title="Clone GeoIP2 module"
        )

        ctx.core.configure_opts.append(
            f"--add{'-dynamic' if self.dynamic else ''}-module={path.resolve()}"
        )

    async def build(self, ctx):
        ...

    async def install(self, ctx):
        ...

    async def uninstall(self, ctx):
        ctx.print(f"{self}: Cannot determine dependencies to clean. "
                  "You may need to mannually remove "
                  "/opt/geoip, /etc/cron.d/geoipupdate, /usr/local/etc/GeoIP.conf, "
                  "geoipupdate and /usr/local/lib/libmaxminddb.so")

    async def clean(self, ctx):
        ...
