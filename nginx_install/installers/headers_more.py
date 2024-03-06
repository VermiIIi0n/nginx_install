from .base import BaseInstaller


class HeadersMoreInstaller(BaseInstaller):
    enabled: bool = False
    dynamic: bool = False

    async def prepare(self, ctx):
        logger = ctx.logger
        path = ctx.build_dir / "headers-more-nginx-module"
        logger.debug("%s: Cloning Headers More into %s", self, path)

        await ctx.git_clone(
            "https://github.com/openresty/headers-more-nginx-module.git",
            path,
            title="Clone Headers More",
        )

        ctx.core.configure_opts.append(
            f"--add{'-dynamic' if self.dynamic else ''}-module={path.resolve()}"
        )

    async def build(self, ctx):
        ...

    async def install(self, ctx):
        ...

    async def uninstall(self, ctx):
        ...

    async def clean(self, ctx):
        ...
