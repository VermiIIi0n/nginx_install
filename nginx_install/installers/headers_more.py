from .base import BuiltinInstaller


class HeadersMoreInstaller(BuiltinInstaller):
    enabled: bool = False
    dynamic: bool = False

    @property
    def ngx_modulenames(self) -> tuple[str, ...]:
        return ("ngx_http_headers_more_filter_module",)

    async def prepare(self, ctx):
        logger = ctx.logger
        path = ctx.build_dir / "headers-more-nginx-module"
        logger.debug("%s: Cloning Headers More into %s", self, path)
        task = ctx.progress.add_task("Prepare Headers More", total=1)

        await ctx.git_clone(
            "https://github.com/openresty/headers-more-nginx-module.git",
            path,
            title="Clone Headers More",
        )

        ctx.core.configure_opts.append(
            f"--add{'-dynamic' if self.dynamic else ''}-module="
            "../headers-more-nginx-module"
        )

        ctx.progress.update(task, advance=1)

    async def build(self, ctx):
        ...

    async def install(self, ctx):
        ...

    async def uninstall(self, ctx):
        ...

    async def clean(self, ctx):
        ...
