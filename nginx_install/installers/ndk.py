from pydantic import Field
from .general_git import GeneralGitInstaller


class NginxDevKitInstaller(GeneralGitInstaller):
    enabled: bool = False
    dynamic: bool = False
    name: str = Field(default="ngx-dev-kit", exclude=True)
    post_cmds: list = Field(
        default_factory=list, exclude=True)
    url: str = Field(
        default="https://github.com/vision5/ngx_devel_kit.git", exclude=True)
    ngx_modulenames: list = Field(
        default_factory=lambda: ["ndk_http_module"], exclude=True)
