import re
from semantic_version import Version
from vermils.io import aio
from .base import BaseInstaller

ver_re = re.compile(r"^nginx__dynamic_tls_records_(\d+\.\d+\.\d+)\+?\.patch$")


class DynamicResizeTLSInstaller(BaseInstaller):
    enabled: bool = False

    async def prepare(self, ctx):
        logger = ctx.logger
        task = ctx.progress.add_task("Prepare DRR TLS", total=2)

        if await ctx.has_core_built():
            logger.debug("%s: Core already built", self)
            ctx.progress.update(task, advance=2)
            return

        path = ctx.build_dir / "ngx_http_tls_dyn_size"
        logger.debug("%s: Cloning DRR TLS into %s", self, path)

        await ctx.git_clone(
            "https://github.com/nginx-modules/ngx_http_tls_dyn_size.git",
            path,
            title="Clone DRR TLS",
            run_in_dry=True,
        )

        ctx.progress.update(task, advance=1)

        v_sheet = await ctx.core.get_versions(ctx.client)
        target_v = v_sheet.get_matching_version(ctx.core.nginx_version)
        versions = list[tuple[Version, str]]()

        for fname in await aio.os.listdir(path):
            m = ver_re.match(fname)
            if m:
                versions.append((Version(m.group(1)), fname))

        if target_v is None:
            raise RuntimeError("Target version not specified")

        versions = [v for v in versions if v[0] <= target_v]
        if not versions:
            raise RuntimeError("No patch found for target version")
        _, pname = max(versions)

        logger.debug("%s: Applying patch %s", self, pname)
        rs = await ctx.run_cmd(
            f"patch -f -p1 < ../ngx_http_tls_dyn_size/{pname}",
            cwd=ctx.nginx_src_dir
        )
        rs.raise_for_returncode()

        ctx.progress.update(task, advance=1)

    async def build(self, ctx):
        ...

    async def install(self, ctx):
        ...

    async def uninstall(self, ctx):
        ...

    async def clean(self, ctx):
        ...
