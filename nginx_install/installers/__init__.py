from .base import BaseInstaller, BuiltinInstaller, from_dict
from .core import NginxInstaller
from .openssl import OpenSSLInstaller
from .zlib_cf import ZlibCFInstaller
from .headers_more import HeadersMoreInstaller
from .fancyindex import FancyIndexInstaller
from .http_tls_dyn_size import DynamicResizeTLSInstaller
from .brotli import BrotliInstaller
from .geoip2 import GeoIP2Installer
from .general_git import GeneralGitInstaller
from .subfilter import SubFilterInstaller
from .ndk import NginxDevKitInstaller

_non_core_installer_types: list[type] = [
    OpenSSLInstaller,
    HeadersMoreInstaller,
    FancyIndexInstaller,
    DynamicResizeTLSInstaller,
    BrotliInstaller,
    GeoIP2Installer,
    ZlibCFInstaller,
    GeneralGitInstaller,
    SubFilterInstaller,
    NginxDevKitInstaller,
]

__all__ = [
    "BaseInstaller",
    "BuiltinInstaller",
    "NginxInstaller",
    "OpenSSLInstaller",
    "ZlibCFInstaller",
    "HeadersMoreInstaller",
    "FancyIndexInstaller",
    "DynamicResizeTLSInstaller",
    "BrotliInstaller",
    "GeoIP2Installer",
    "GeneralGitInstaller",
    "SubFilterInstaller",
    "NginxDevKitInstaller",
    "from_dict",
    "_non_core_installer_types",
]
