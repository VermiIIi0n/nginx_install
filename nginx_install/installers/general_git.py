from os.path import relpath
from pydantic import Field
from pathlib import Path
from urllib.parse import urlparse, quote
from .base import BuiltinInstaller, BaseInstaller


class GeneralGitInstaller(BuiltinInstaller):
    """
    # GeneralGitInstaller
    Many modules simply require a git clone and
     add `--add-module` to the `configure` options.

    This class is a general installer for such modules.

    ## Key fields
    - `name`: The name of the module, used for git destination, optional.
    - `url`: The git URL to clone.
    - `post_cmds`: Optional, list of commands to run after `git clone`
      inside the module directory.
    - `ngx_modulenames`: Optional, dynamic *.so names, may be used for testing.
    """
    enabled: bool = False
    dynamic: bool = False
    name: str = ''
    url: str = ''
    post_cmds: list[str] = Field(default_factory=list)
    ngx_modulenames: list[str] = Field(default_factory=list)

    @property
    def git_dest(self) -> Path:
        if self.name:
            return Path(quote(self.name))
        return Path(quote(urlparse(self.url).netloc))

    async def prepare(self, ctx):
        logger = ctx.logger
        if not self.url.strip():
            raise ValueError(f"{self}: url is empty")

        task = ctx.progress.add_task(
            f"Prepare {self.git_dest}",
            total=1+len(self.post_cmds),
        )
        logger.debug("%s: Preparing git for %s", self, self.git_dest)

        path = ctx.build_dir / self.git_dest
        logger.debug("%s: Cloning FancyIndex into %s", self, path)

        await ctx.git_clone(
            self.url,
            path.resolve(),
        )

        for cmd in self.post_cmds:
            logger.debug("%s: Running post command: %s", self, cmd)
            await ctx.run_cmd(
                cmd,
                cwd=path.resolve(),
            )
            ctx.progress.update(task, advance=1)

        ctx.core.configure_opts.append(
            f"--add{'-dynamic' if self.dynamic else ''}-module="
            f"{relpath(path, ctx.nginx_src_dir)}"
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

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseInstaller):
            return NotImplemented
        if not isinstance(other, GeneralGitInstaller):
            return False
        return other.url == self.url
