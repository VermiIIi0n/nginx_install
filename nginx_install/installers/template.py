from .base import BaseInstaller


class TempInstaller(BaseInstaller):
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
