from .base import BaseInstaller, from_dict
from .core import NginxInstaller
from .openssl import OpenSSLInstaller
from .headers_more import HeadersMoreInstaller
from .fancyindex import FancyIndexInstaller
from .http_tls_dyn_size import DynamicResizeTLSInstaller
from .brotli import BrotliInstaller
from .geoip2 import GeoIP2Installer

_normal_installer_types: list[type] = [
    OpenSSLInstaller,
    HeadersMoreInstaller,
    FancyIndexInstaller,
    DynamicResizeTLSInstaller,
    BrotliInstaller,
    GeoIP2Installer,
]
