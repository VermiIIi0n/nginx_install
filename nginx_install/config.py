import sys
from typing import Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from pydantic import field_serializer, SerializationInfo
from pathlib import Path
from warnings import warn
from .installers import BaseInstaller, NginxInstaller
from .installers import _non_core_installer_types, from_dict


class BaseConfig(BaseModel):
    model_config = ConfigDict(validate_assignment=True, extra="allow")


class Config(BaseConfig):
    class LoggingConfig(BaseConfig):
        level: str = "INFO"
        format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        console: bool = False

    class NetworkConfig(BaseConfig):
        proxy: str | None = None
        user_agent: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        extra: dict[str, Any] = Field(default_factory=dict)

    version: str = "0.0.1"
    network: NetworkConfig = Field(default_factory=NetworkConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    pymodule_paths: list[Path] = []
    core: NginxInstaller = Field(default_factory=NginxInstaller)
    installers: list[BaseInstaller] = Field(
        default_factory=lambda: [t() for t in _non_core_installer_types])

    @field_validator("pymodule_paths", mode="after")
    def add_pymodule_paths(cls, v: list[Path]):
        for path in v:
            path = path.resolve()
            if not path.exists():
                warn(f"Path {path} may not exist", UserWarning)
            sys.path.append(str(path))
        return v

    @field_validator("installers", mode="before")
    def check_installers(cls, v):
        for index, i in enumerate(v):
            if isinstance(i, dict):
                v[index] = from_dict(i)
        return v

    @field_serializer("installers", when_used="always")
    @staticmethod
    def serialize_installers(
            v: list[BaseInstaller], info: SerializationInfo):
        return [i.model_dump(mode=info.mode) for i in v]
