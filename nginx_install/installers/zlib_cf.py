from .base import BaseInstaller


class ZlibCFInstaller(BaseInstaller):
    enabled: bool = False

    async def prepare(self, ctx):
        logger = ctx.logger
        logger.debug("%s: Preparing Zlib Cloudflare installer", self)

        path = ctx.build_dir / "cloudflare-zlib"

        await ctx.git_clone(
            "https://github.com/cloudflare/zlib.git",
            path,
        )

        rs = await ctx.run_cmd(
            "./configure",
            cwd=path.resolve(),
        )
        rs.raise_for_returncode()

        ctx.core.configure_opts.append(f"--with-zlib='{path.resolve()}'")

    async def build(self, ctx):
        ...

    async def install(self, ctx):
        ...

    async def uninstall(self, ctx):
        ...

    async def clean(self, ctx):
        ...
