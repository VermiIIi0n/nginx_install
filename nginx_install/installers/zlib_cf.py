from os.path import relpath
from .base import BuiltinInstaller


class ZlibCFInstaller(BuiltinInstaller):
    enabled: bool = False

    async def prepare(self, ctx):
        logger = ctx.logger
        logger.debug("%s: Preparing Zlib Cloudflare installer", self)
        task = ctx.progress.add_task("Prepare Zlib Cloudflare", total=2)

        path = ctx.build_dir / "cloudflare-zlib"

        await ctx.git_clone(
            "https://github.com/cloudflare/zlib.git",
            path,
        )

        ctx.progress.update(task, advance=1)

        rs = await ctx.run_cmd(
            "./configure",
            cwd=path.resolve(),
        )
        rs.raise_for_returncode()

        ctx.core.configure_opts.append(
            f"--with-zlib={relpath(path, ctx.nginx_src_dir)}")
        ctx.progress.update(task, advance=1)

    async def build(self, ctx):
        ...

    async def install(self, ctx):
        ...

    async def uninstall(self, ctx):
        ...

    async def clean(self, ctx):
        ...
