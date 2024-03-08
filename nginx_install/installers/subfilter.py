from pydantic import Field
from .general_git import GeneralGitInstaller


class SubFilterInstaller(GeneralGitInstaller):
    """
    # Substitution Filter Module
    """
    enabled: bool = False
    dynamic: bool = False
    name: str = Field(default="substitution_filter", exclude=True)
    post_cmds: list = Field(
        default_factory=list, exclude=True)
    url: str = Field(
        default="https://github.com/yaoweibin/ngx_http_substitutions_filter_module",
        exclude=True)
    ngx_modulenames: list = Field(
        default_factory=lambda: ["ngx_http_subs_filter_module"], exclude=True)
