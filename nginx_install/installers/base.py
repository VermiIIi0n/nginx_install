from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from importlib import import_module
from pydantic import BaseModel, computed_field, ConfigDict
from ..context import Context


def get_cls_from_dict(data: dict) -> type[BaseInstaller]:
    mod = import_module(data["modulename"])
    return getattr(mod, data["classname"])


def from_dict(data: dict) -> BaseInstaller:
    real_cls = get_cls_from_dict(data)
    return real_cls.model_validate(data)


class BaseInstaller(ABC, BaseModel):
    model_config = ConfigDict(extra="allow")
    enabled: bool

    @computed_field  # type: ignore[misc]
    @property
    def classname(self) -> str:
        return self.__class__.__name__

    @computed_field  # type: ignore[misc]
    @property
    def modulename(self) -> str | None:
        mod = inspect.getmodule(self.__class__)
        if mod is None:
            return None
        return mod.__name__

    @abstractmethod
    async def prepare(self, ctx: Context):
        ...

    @abstractmethod
    async def build(self, ctx: Context):
        ...

    @abstractmethod
    async def install(self, ctx: Context):
        ...

    @abstractmethod
    async def uninstall(self, ctx: Context):
        ...

    @abstractmethod
    async def clean(self, ctx: Context):
        ...

    def __str__(self) -> str:
        return f"{self.classname}()"
