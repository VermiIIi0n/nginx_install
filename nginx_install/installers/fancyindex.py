from .base import BaseInstaller


class FancyIndexInstaller(BaseInstaller):
    enabled: bool = False
    dynamic: bool = False

    async def prepare(self, ctx):
        logger = ctx.logger
        logger.debug("%s: Preparing FancyIndex installer", self)

        path = ctx.nginx_src_dir / "ngx-fancyindex"
        logger.debug("%s: Cloning FancyIndex into %s", self, path)

        await ctx.git_clone(
            "https://github.com/aperezdc/ngx-fancyindex.git",
            path,
            title="Clone FancyIndex",
        )

        ctx.core.configure_opts.append(
            f"--add{"-dynamic" if self.dynamic else ''}-module={path.resolve()}"
        )

    async def build(self, ctx):
        ...

    async def install(self, ctx):
        ...

    async def uninstall(self, ctx):
        ...

    async def clean(self, ctx):
        ...