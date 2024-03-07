from vermils.io import aio
from .base import BaseInstaller


class BrotliInstaller(BaseInstaller):
    enabled: bool = False
    dynamic: bool = False

    @property
    def ngx_modulename(self) -> str:
        return "ngx_http_brotli_filter_module"

    async def prepare(self, ctx):
        logger = ctx.logger
        path = ctx.build_dir / "ngx_brotli"
        logger.debug("%s: Cloning Brotli into %s", self, path)
        task = ctx.progress.add_task("Prepare Brotli", total=2)

        rs = await ctx.run_cmd(
            "apt-get install -y libbrotli-dev"
        )
        rs.raise_for_returncode()

        ctx.progress.update(task, advance=1)

        if not await aio.path.exists(path):
            # git complains if existing repo is not owned by the user
            # so skip clone and submodule update if the directory exists
            await ctx.git_clone(
                "https://github.com/google/ngx_brotli.git",
                path,
                title="Clone Brotli",
            )

            rs = await ctx.run_cmd(
                f"cd '{path}' && git submodule update --init --recursive && cd -"
            )
            rs.raise_for_returncode()

        ctx.core.configure_opts.append(
            f"--add{'-dynamic' if self.dynamic else ''}-module=../ngx_brotli"
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
