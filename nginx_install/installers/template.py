from .base import BuiltinInstaller


class TempInstaller(BuiltinInstaller):
    enabled: bool = False

    async def prepare(self, ctx):
        ...

    async def build(self, ctx):
        ...

    async def install(self, ctx):
        ...

    async def uninstall(self, ctx):
        ...

    async def clean(self, ctx):
        ...
