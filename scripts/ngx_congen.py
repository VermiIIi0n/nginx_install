import yaml
from pathlib import Path
from nginx_install import installers
from nginx_install.config import Config

template = """
worker_processes auto;

{module_loading}

events {{
    worker_connections 768;
    multi_accept on;
}}

http {{

    ##
    # Basic Settings
    ##

    client_max_body_size 128m;
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;

    # server_names_hash_bucket_size 64;
    # server_name_in_redirect off;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    ##
    # SSL Settings
    ##

    ssl_protocols TLSv1.3 TLSv1.2;
    # ssl_stapling on;
    ssl_prefer_server_ciphers on;
    ssl_dhparam /usr/local/tls/dhparam.pem;
    ssl_session_cache shared:SSL:10m;
    ssl_ciphers     HIGH:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!aECDH:!EDH-DSS-DES-CBC3-SHA:!EDH-RSA-DES-CBC3-SHA:!KRB5-DES-CBC3-SHA;
    add_header Strict-Transport-Security "max-age=63072000; includeSubdomains; preload";


{geoip2_cfg}

    ##
    # Logging Settings
    ##

    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    ##
    # Gzip Settings
    ##
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 9;
    gzip_buffers 16 16k;
    gzip_http_version 1.1;
    gzip_types application/atom+xml application/javascript application/json application/rss+xml application/vnd.ms-fontobject application/x-font-opentype application/x-font-truetype application/x-font-ttf application/x-javascript application/xhtml+xml application/xml font/eot font/opentype font/otf font/truetype image/svg+xml image/vnd.microsoft.icon image/x-icon image/x-win-bitmap text/css text/javascript text/plain text/xml;

    #Brotli configs

{brotli_cfg}

    include /etc/nginx/conf.d/*.conf;
    server {{
        listen 80;
        listen [::]:80;
        listen 443 ssl http2;
        listen [::]:443 ssl http2;

        server_name sample.com;
        index index.html;
        root /var/www/sample;
        
        ssl_certificate /usr/local/tls/sample.pem;
        # ssl_trusted_certificate /usr/local/tls/sample.pem;
        ssl_certificate_key /usr/local/tls/sample.key;
    }}
}}

"""

geoip2_cfg = """
    geoip2 /usr/local/share/GeoIP/GeoLite2-City.mmdb{
        $geoip2_data_country_iso_code country iso_code;
        $geoip2_data_continent_code   continent code;
    }

    map $geoip2_data_country_iso_code $allowed_country {
        default yes;
        CN yes;
        HK yes;
        TW yes;
    }
"""

brotli_cfg = """
    brotli_static on;
    brotli on;
    brotli_types application/atom+xml application/javascript application/json application/rss+xml application/vnd.ms-fontobject application/x-font-opentype application/x-font-truetype application/x-font-ttf application/x-javascript application/xhtml+xml application/xml font/eot font/opentype font/otf font/truetype image/svg+xml image/vnd.microsoft.icon image/x-icon image/x-win-bitmap text/css text/javascript text/plain text/xml;
    brotli_buffers 32 16K;
    brotli_comp_level 11;
    brotli_window 4m;
    brotli_min_length 20;
"""

config_path = Path("../config.yaml")
config = Config.model_validate(yaml.safe_load(config_path.read_text()))
module_loading = ""
has_brotli = False
has_geoip2 = False
for installer in filter(lambda x: x.enabled, config.installers):
    ngx_modulename = getattr(installer, "ngx_modulename", None)
    if getattr(installer, "dynamic", False) and ngx_modulename is not None:
        module_loading += f"load_module {config.core.modules_path.resolve() / ngx_modulename}.so;\n"
    if isinstance(installer, installers.BrotliInstaller):
        has_brotli = True
    if isinstance(installer, installers.GeoIP2Installer):
        has_geoip2 = True


conf = template.format(
    module_loading=module_loading,
    geoip2_cfg=geoip2_cfg if has_geoip2 else '',
    brotli_cfg=brotli_cfg if has_brotli else ''
)

print(conf)
