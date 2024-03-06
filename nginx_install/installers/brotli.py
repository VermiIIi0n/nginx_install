from .base import BaseInstaller


class BrotliInstaller(BaseInstaller):
    enabled: bool = False
    dynamic: bool = False

    async def prepare(self, ctx):
        logger = ctx.logger
        path = ctx.build_dir / "ngx_brotli"
        logger.debug("%s: Cloning Brotli into %s", self, path)

        await ctx.git_clone(
            "https://github.com/google/ngx_brotli.git",
            path,
            title="Clone Brotli",
        )

        rs = await ctx.run_cmd(
            "apt-get install -y libbrotli-dev"
        )
        rs.raise_for_returncode()

        rs = await ctx.run_cmd(
            f"cd '{path}' && git submodule update --init --recursive && cd -"
        )
        rs.raise_for_returncode()

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
