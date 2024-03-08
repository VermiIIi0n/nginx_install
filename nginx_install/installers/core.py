import httpx
import bs4
import re
import multiprocessing as mp
from typing import Literal
from semantic_version import Version, SimpleSpec
from pydantic import Field
from pathlib import Path
from vermils.io import aio
from .base import BuiltinInstaller
from ..context import Context, Result


ver_re = re.compile(r"nginx-(\d+)\.(\d+)\.(\d+)")


class VersionSheet:
    def __init__(self, mainline: Version, stable: Version, legacies: list[Version]):
        self.mainline = mainline
        self.stable = stable
        self.legacies = legacies

    @property
    def all(self) -> list[Version]:
        return [self.mainline, self.stable, *self.legacies]

    @property
    def latest(self) -> Version:
        return max(self.all)

    def get_latest_matching(self, spec: SimpleSpec | None = None) -> Version:
        if spec is None:
            return max(self.all)
        return max(filter(spec.match, self.all))

    def get_matching_version(self, v_spec_str: str) -> Version:
        v_sheet = self
        match v_spec_str.strip():
            case "latest":
                return v_sheet.latest
            case "mainline":
                return v_sheet.mainline
            case "stable":
                return v_sheet.stable
            case _:
                v_spec = SimpleSpec(v_spec_str)
                return v_sheet.get_latest_matching(v_spec)


class NginxInstaller(BuiltinInstaller):
    enabled: Literal[True] = Field(default=True, exclude=True)

    nginx_version: Literal["stable", "mainline", "latest"] | str = "stable"
    config_prefix: Path = Path("/etc/nginx")
    config_name: str = "nginx.conf"
    sbin_path: Path = Path("/usr/sbin/nginx")
    modules_path: Path = Path("/usr/lib/nginx/modules")
    error_log_path: Path = Path("/var/log/nginx/error.log")
    http_log_path: Path = Path("/var/log/nginx/access.log")
    pid_path: Path = Path("/run/nginx.pid")
    lock_path: Path = Path("/run/nginx.lock")
    cache_path: Path = Path("/var/cache/nginx")
    user: str = "www-data"
    group: str = "www-data"
    configure_opts: list[str] = Field(
        default_factory=lambda:
        [
            "--http-client-body-temp-path=/var/cache/nginx/client_temp",
            "--http-proxy-temp-path=/var/cache/nginx/proxy_temp",
            "--http-fastcgi-temp-path=/var/cache/nginx/fastcgi_temp",
            "--http-scgi-temp-path=/var/cache/nginx/scgi_temp",
            "--http-uwsgi-temp-path=/var/cache/nginx/uwsgi_temp",

            "--with-pcre-jit",
            "--with-threads",
            "--with-file-aio",

            "--with-http_ssl_module",
            "--with-http_v2_module",
            # "--with-http_v3_module",
            "--with-http_mp4_module",
            "--with-http_auth_request_module",
            "--with-http_slice_module",
            "--with-http_stub_status_module",
            "--with-http_realip_module",
            "--with-http_addition_module",
            "--with-http_sub_module",
            "--with-http_random_index_module",
            "--with-http_secure_link_module",
            "--with-http_degradation_module",
            "--with-http_gunzip_module",
            "--with-http_gzip_static_module",
            "--with-http_perl_module",
            "--with-http_geoip_module",

            "--with-stream",
            "--with-stream_ssl_module",
            "--with-stream_realip_module",

            "--with-mail=dynamic",
            "--with-mail_ssl_module",
        ]
    )
    cc_opts: list[str] = Field(
        default_factory=lambda:
        [
            "-Wno-deprecated-declarations",
            "-Wno-ignore-qualifiers",
            # "-g",
            "-O3",
            "-march=native",
            "-fPIC",
            "-Wdate-time",
            "-D_FORTIFY_SOURCE=2",
            "-flto",
            "-funroll-loops",
            "-ffunction-sections",
            "-fdata-sections",
            "-Wl,--gc-sections"
        ]
    )

    @property
    def config_path(self) -> Path:
        return self.config_prefix / self.config_name

    @property
    def build_options(self) -> list[str]:
        ret = self.configure_opts.copy()
        for copt in self.cc_opts:
            ret.append(f"--with-cc-opt={copt}")
        ret.append(f"--prefix={self.config_prefix}")
        ret.append(f"--sbin-path={self.sbin_path}")
        ret.append(f"--conf-path={self.config_path}")
        ret.append(f"--modules-path={self.modules_path}")
        ret.append(f"--error-log-path={self.error_log_path}")
        ret.append(f"--http-log-path={self.http_log_path}")
        ret.append(f"--pid-path={self.pid_path}")
        ret.append(f"--lock-path={self.lock_path}")
        ret.append(f"--user={self.user}")
        ret.append(f"--group={self.group}")
        return ret

    @staticmethod
    async def get_versions(client: httpx.AsyncClient | None = None):
        nginx_release_page = "https://nginx.org/en/download.html"
        if client is None:
            client = httpx.AsyncClient()
        r = await client.get(nginx_release_page, follow_redirects=True)
        r.raise_for_status()

        soup = bs4.BeautifulSoup(r.text, "lxml")

        mainline_header = soup.find(string="Mainline version")
        mainline_table = mainline_header.find_next("table")
        mainline_version_a = mainline_table.find_all("a")
        for v in mainline_version_a:
            ver = ver_re.match(v.string)
            if ver is None:
                continue
            mainline_version = Version(
                major=int(ver.group(1)),
                minor=int(ver.group(2)),
                patch=int(ver.group(3))
            )
            break

        stable_header = soup.find(string="Stable version")
        stable_table = stable_header.find_next("table")
        stable_version_a = stable_table.find_all("a")
        for v in stable_version_a:
            ver = ver_re.match(v.string)
            if ver is None:
                continue
            stable_version = Version(
                major=int(ver.group(1)),
                minor=int(ver.group(2)),
                patch=int(ver.group(3))
            )
            break

        legacy_header = soup.find(string="Legacy versions")
        legacy_tables = legacy_header.find_all_next("table")
        legacy_versions = list[Version]()
        for tab in legacy_tables:
            legacy_version_a = tab.find_all("a")
            for v in legacy_version_a:
                ver = ver_re.match(v.string)
                if ver is None:
                    continue
                legacy_versions.append(
                    Version(major=int(ver.group(1)), minor=int(
                        ver.group(2)), patch=int(ver.group(3)))
                )

        return VersionSheet(mainline_version, stable_version, legacy_versions)

    def get_init_script(self) -> str:
        return f"""
[Unit]
Description=The NGINX HTTP and reverse proxy server
After=syslog.target network-online.target remote-fs.target nss-lookup.target
Wants=network-online.target

[Service]
Type=forking
PIDFile={self.pid_path}
ExecStartPre={self.sbin_path} -t
ExecStart={self.sbin_path}
ExecReload={self.sbin_path} -s reload
ExecStop=/bin/kill -s QUIT $MAINPID
TimeoutStopSec=15
PrivateTmp=true

[Install]
WantedBy=multi-user.target
"""

    async def prepare(self, ctx: Context):
        ctx.logger.info("Start preparing nginx")
        task = ctx.progress.add_task("Prepare core", total=3)

        v_sheet = await self.get_versions(ctx.client)
        ctx.logger.debug(
            "Versions: %s (mainline), %s (stable), %s (legacies)",
            v_sheet.mainline, v_sheet.stable, v_sheet.legacies)

        semversion = v_sheet.get_matching_version(self.nginx_version)
        ctx.logger.info("%s: Downloading nginx version %s", self, semversion)

        download_url = f"https://nginx.org/download/nginx-{semversion}.tar.gz"
        ctx.logger.info("%s: Downloading nginx source from %s",
                        self, download_url)

        nginx_version = f"nginx-{semversion}"
        tar_path = ctx.build_dir / f"{nginx_version}.tar.gz"

        ctx.progress.update(task, advance=1)

        ctx.logger.debug("Checking for required packages")
        rs = await ctx.run_cmd("apt-get update")
        rs.raise_for_returncode()

        packages = [
            "build-essential", "ca-certificates", "wget", "curl", "libpcre3",
            "libpcre3-dev", "autoconf", "unzip", "automake", "libtool", "tar",
            "git", "libssl-dev", "zlib1g-dev", "uuid-dev", "lsb-release",
            "libgeoip-dev", "cmake", "libperl-dev"
        ]

        ctx.logger.debug("%s: Installing packages: %s", self, packages)
        rs = await ctx.run_cmd(f"apt-get install -y {' '.join(packages)}")

        ctx.progress.update(task, advance=1)

        if await ctx.has_core_built():
            ctx.logger.info(
                "Nginx source has already been built, skipping download")
        else:
            ctx.logger.debug("%s: Removing directory %s",
                             self, ctx.nginx_src_dir)
            rs = await ctx.run_cmd(f"rm -rf {ctx.nginx_src_dir}")
            rs.raise_for_returncode()

            await ctx.download(download_url, tar_path, title="Get nginx source")

            ctx.logger.debug(
                "%s: Start decompressing nginx source %s", self, tar_path)
            rs = await ctx.run_cmd(
                f"tar -xzf {tar_path} -C {ctx.build_dir}")
            rs.raise_for_returncode()
            rs = await ctx.run_cmd(
                f"mv {ctx.build_dir / nginx_version} {ctx.nginx_src_dir}")
            rs.raise_for_returncode()

        ctx.logger.info("Nginx preparation completed")
        ctx.progress.update(task, advance=1)

    async def build(self, ctx: Context):
        ctx.logger.info("Start building nginx")
        task = ctx.progress.add_task("Build core", total=2)
        rs = await ctx.run_cmd(
            f"./configure {' '.join(self.build_options)}",
            cwd=str(ctx.nginx_src_dir)
        )

        ctx.progress.update(task, advance=1)

        rs.raise_for_returncode()
        rs = await ctx.run_cmd(f"make -j {mp.cpu_count()}", cwd=str(ctx.nginx_src_dir))
        rs.raise_for_returncode()

        ctx.logger.info("Nginx build completed")
        ctx.progress.update(task, advance=1)

    async def install(self, ctx: Context):
        ctx.logger.info("Start installing nginx")
        task = ctx.progress.add_task("Install core", total=3)
        rs = await ctx.run_cmd("make install", cwd=str(ctx.nginx_src_dir))
        rs.raise_for_returncode()

        if not ctx.dry_run:
            init_script_path = "/etc/systemd/system/nginx.service"
            ctx.logger.debug("%s: Creating init script at %s",
                             self, init_script_path)
            init_script = self.get_init_script()
            async with aio.open(init_script_path, "w") as f:
                await f.write(init_script)

            ctx.logger.debug(
                "Creating modules directory at %s", self.modules_path)
            self.modules_path.mkdir(parents=True, exist_ok=True)

            ctx.logger.debug(
                "%s: Creating cache directory at %s", self, self.cache_path)
            self.cache_path.mkdir(parents=True, exist_ok=True)

            sites_available = self.config_prefix / "sites-available"
            sites_enabled = self.config_prefix / "sites-enabled"
            ctx.logger.debug(
                "Creating sites-available and sites-enabled directories")
            sites_available.mkdir(exist_ok=True)
            sites_enabled.mkdir(exist_ok=True)

            confd = self.config_prefix / "conf.d"
            ctx.logger.debug(
                "%s: Creating conf.d directory at %s", self, confd)
            confd.mkdir(exist_ok=True)

        ctx.progress.update(task, advance=1)

        if (await ctx.run_cmd(f"getent group {self.group}")).failed:
            ctx.logger.debug("%s: Creating group %s", self, self.group)
            rs = await ctx.run_cmd(f"addgroup {self.group}")
            rs.raise_for_returncode()

        if (await ctx.run_cmd(f"getent passwd {self.user}")).failed:
            ctx.logger.debug("%s: Creating user %s", self, self.user)
            rs = await ctx.run_cmd(f"adduser --system --no-create-home {self.user}")
            rs.raise_for_returncode()

        ctx.logger.debug("%s: Add group %s to user %s",
                         self, self.group, self.user)
        rs = await ctx.run_cmd(f"usermod -aG {self.group} {self.user}")
        rs.raise_for_returncode()

        ctx.progress.update(task, advance=1)

        ctx.logger.debug("Enabling nginx service")
        rs = await ctx.run_cmd("systemctl enable nginx")
        rs.raise_for_returncode()

        ctx.logger.info("Nginx installation completed")
        ctx.progress.update(task, advance=1)

    async def uninstall(self, ctx: Context):
        ctx.logger.info("Start uninstalling nginx")
        rs = list[Result]()
        paths = (
            self.sbin_path, self.modules_path, self.cache_path,
            self.error_log_path, self.http_log_path,
        )
        task = ctx.progress.add_task("Uninstall core", total=len(paths))
        for d in paths:
            ctx.progress.update(task, advance=1)
            if d.exists():
                ctx.logger.debug("%s: Removing location %s", self, d)
                rs.append(await ctx.run_cmd(f"rm -rf {d}"))
                continue
            ctx.logger.debug("%s: Location %s does not exist", self, d)

        for r in rs:
            r.raise_for_returncode()

        ctx.logger.info("Nginx uninstallation completed")

    async def clean(self, ctx: Context):
        ctx.logger.info("Start cleaning nginx")
        task = ctx.progress.add_task("Clean core", total=1)
        if ctx.build_dir.exists():
            ctx.logger.debug("%s: Removing directory %s", self, ctx.build_dir)
            rs = await ctx.run_cmd(f"rm -rf {ctx.build_dir}")
            rs.raise_for_returncode()

        ctx.logger.info("Nginx cleaning completed")
        ctx.progress.update(task, advance=1)
