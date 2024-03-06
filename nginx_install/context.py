import httpx
import subprocess
import logging
import asyncio
import tempfile
from typing import TYPE_CHECKING
from pathlib import Path
from uuid import uuid4
from urllib.request import getproxies
from semantic_version import Version
from rich.progress import Progress
from vermils.asynctools.asinkrunner import AsinkRunner
from vermils.io import aio
from vermils.gadgets.monologger import MonoLogger
if TYPE_CHECKING:
    from .config import Config
else:
    Config = None


class Result:
    def __init__(
            self,
            p: subprocess.CompletedProcess | subprocess.Popen,
            cmds: tuple[str, ...] | list[str],
    ):
        self.returncode = p.returncode
        self.output = p.stdout
        self.error = p.stderr
        self.cmds = cmds

    def raise_for_returncode(self):
        if self.returncode != 0:
            output = self.get_output_str()
            error = self.get_error_str()
            raise subprocess.CalledProcessError(
                self.returncode, ' '.join(self.cmds),
                output, error)

    def get_output_str(self):
        if self.output is not None:
            with open(self.output.fileno(), 'r') as f:
                return f.read()

    def get_error_str(self):
        if self.error is not None:
            with open(self.error.fileno(), 'r') as f:
                return f.read()

    @property
    def ok(self):
        return self.returncode == 0

    @property
    def failed(self):
        return self.returncode != 0


class Context:
    def __init__(
            self,
            cfg: Config,
            build_dir: Path,
            dry_run: bool,
            verbose: bool,
            quiet: bool
    ):
        self.cfg = cfg
        self.core = cfg.core
        """Same as `cfg.core`, the `NginxInstaller` instance"""
        self.build_dir = build_dir
        self.dry_run = dry_run
        self.verbose = verbose
        self.quiet = quiet

        proxy = cfg.network.proxy
        sys_proxies = getproxies()
        if proxy is None:
            if "http" in sys_proxies:
                proxy = sys_proxies["http"]
            if "https" in sys_proxies:
                proxy = sys_proxies["https"]
        elif proxy.strip() == '':
            proxy = None

        self.client = httpx.AsyncClient(
            headers={"User-Agent": cfg.network.user_agent},
            trust_env=False,
            proxy=proxy,
            **cfg.network.extra
        )

        log_level = "DEBUG" if verbose else cfg.logging.level
        formatter = logging.Formatter(cfg.logging.format)
        self.logger = MonoLogger(
            level=log_level,
            path=str(build_dir / "logs"),
            formatter=formatter
        )

        if cfg.logging.console and not quiet:
            self.logger.addHandler(logging.StreamHandler())

        self._sink = AsinkRunner()
        self.progress = Progress()
        if not quiet:
            self.progress.start()

    @property
    def nginx_src_dir(self) -> Path:
        return self.build_dir / "nginx"

    def print(self, *args, **kw):
        if not self.quiet:
            print(*args, **kw)

    async def run_cmd(
        self,
        cmds: str | tuple[str, ...] | list[str],
        cwd: str | None = None,
        *,
        shell: bool = True,
        run_in_dry: bool = False,
        **kw
    ):
        """
        Run a command asynchronously

        :param cmds: Command to run
        :param cwd: Current working directory
        :param shell: Run command in shell
        :param kw: Additional keyword arguments to pass to subprocess.Popen

        :return: Result
        """
        return await self._sink.run(
            self.sync_run_cmd,
            cmds, cwd, shell=shell, run_in_dry=run_in_dry, **kw
        )

    def sync_run_cmd(
        self,
        cmds: str | tuple[str, ...] | list[str],
        cwd: str | None = None,
        *,
        shell: bool = True,
        run_in_dry: bool = False,
        **kw
    ):
        if shell and not isinstance(cmds, str):
            cmds = ' '.join(cmds)
        if isinstance(cmds, str):
            cmds = [cmds]
        if (self.dry_run or self.verbose) and not self.quiet:
            print(f"Issue command: {' '.join(cmds)}")
            if self.dry_run and not run_in_dry:
                return Result(subprocess.CompletedProcess(cmds, 0), cmds)

        if self.verbose and not self.quiet:
            stdout = None
            stderr = None
        else:
            stdout = tempfile.NamedTemporaryFile(delete=False)
            stderr = tempfile.NamedTemporaryFile(delete=False)

        if shell:
            cmds = ["sudo", "-E", "bash", "-c", ' '.join(cmds)]
        p = subprocess.Popen(cmds, cwd=cwd, shell=False, stdin=subprocess.DEVNULL,
                             stdout=stdout, stderr=stderr, **kw)
        p.wait()
        return Result(p, cmds)

    async def download(
            self,
            url: str,
            path: Path | str,
            *,
            title: str = "Downloading",
            run_in_dry: bool = True
    ):
        if self.dry_run and not run_in_dry:
            self.print(f"Download {url} to {path}")
            return

        task = self.progress.add_task(title, total=100000)
        async with (
            self.client.stream("GET", url, follow_redirects=True) as r,
            aio.open(str(path), "wb") as f
        ):
            if r.status_code != 200:
                info = await r.aread()
                self.logger.error(
                    "Failed to download nginx source, status: %d info: %s",
                    r.status_code, info)
                r.raise_for_status()

            self.progress.update(
                task, total=int(r.headers.get("content-length", 100000)))

            async for chunk in r.aiter_bytes():
                await f.write(chunk)
                self.progress.update(task, advance=len(chunk))

            async def delay_delete(task):
                await asyncio.sleep(1)
                self.progress.remove_task(task)
            asyncio.get_running_loop().create_task(  # type: ignore[unused-awaitable]
                delay_delete(task))

    async def git_clone(
            self,
            url: str, path: Path,
            *,
            title: str = "Cloning",
            allow_existing: bool = True,
            run_in_dry: bool = True
    ):
        if await aio.path.exists(path):
            self.logger.debug("%s: Already cloned", path)
            if not allow_existing:
                raise FileExistsError(f"{path} already exists")
            return

        rs = await self.run_cmd(
            f"git clone {url} {path}",
            run_in_dry=run_in_dry,
        )
        rs.raise_for_returncode()
