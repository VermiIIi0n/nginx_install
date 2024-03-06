import bs4
import re
from .base import BaseInstaller

ver_re = re.compile(r".*?(\d+\.\d+\.\d+)$")


class OpenSSLInstaller(BaseInstaller):
    enabled: bool = False

    async def prepare(self, ctx):
        logger = ctx.logger
        logger.debug("%s: Preparing OpenSSL installer", self)
        client = ctx.client

        r = await client.get(
            "https://github.com/openssl/openssl/releases/latest",
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

        logger.debug("%s: Latest OpenSSL release version: %s", self, v)
        fpath = ctx.build_dir / f"openssl-{v}.tar.gz"
        await ctx.download(
            "https://github.com/openssl/openssl/releases/download/"
            f"openssl-{v}/openssl-{v}.tar.gz",
            fpath,
            title="Get openssl source",
        )

        rs = await ctx.run_cmd(
            f"tar -xzf '{fpath}' -C '{ctx.build_dir}'",
        )
        rs.raise_for_returncode()

        dpath = ctx.build_dir / f"openssl-{v}"
        rs = await ctx.run_cmd(
            f"cd '{dpath}' && ./config",
        )
        rs.raise_for_returncode()

        ctx.core.configure_opts.append(f"--with-openssl='{dpath.resolve()}'")

    async def build(self, ctx):
        ...

    async def install(self, ctx):
        ...

    async def uninstall(self, ctx):
        ...

    async def clean(self, ctx):
        ...
