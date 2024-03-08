from .base import BaseInstaller, from_dict
from .core import NginxInstaller
from .openssl import OpenSSLInstaller
from .zlib_cf import ZlibCFInstaller
from .headers_more import HeadersMoreInstaller
from .fancyindex import FancyIndexInstaller
from .http_tls_dyn_size import DynamicResizeTLSInstaller
from .brotli import BrotliInstaller
from .geoip2 import GeoIP2Installer
from .general_git import GeneralGitInstaller

_non_core_installer_types: list[type] = [
    OpenSSLInstaller,
    HeadersMoreInstaller,
    FancyIndexInstaller,
    DynamicResizeTLSInstaller,
    BrotliInstaller,
    GeoIP2Installer,
    ZlibCFInstaller,
    GeneralGitInstaller,
]

__all__ = [
    "BaseInstaller",
    "NginxInstaller",
    "OpenSSLInstaller",
    "ZlibCFInstaller",
    "HeadersMoreInstaller",
    "FancyIndexInstaller",
    "DynamicResizeTLSInstaller",
    "BrotliInstaller",
    "GeoIP2Installer",
    "GeneralGitInstaller",
    "from_dict",
    "_non_core_installer_types",
]
