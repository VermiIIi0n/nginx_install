import yaml
import argparse
from pathlib import Path
from nginx_install.installers import GeneralGitInstaller
from nginx_install.config import Config
from nginx_install.utils import model_dump_yaml


parser = argparse.ArgumentParser("ConGen", description="Generate test config")
parser.add_argument("output", type=str, help="Output file")
parser.add_argument("mods", type=str, nargs="*",
                    help="What modules to enable (by classname), use `all` to enable all modules")
parser.add_argument("-c", "--config", type=str,
                    help="Path to source config file", default=None)
parser.add_argument("-v", "--version", type=str,
                    help="Version spec of the the nginx to install", default="mainline")
parser.add_argument("--dynamic", action="store_true",
                    help="Enable dynamic modules")

args = parser.parse_args()
path = Path(args.output)
mods = [m.strip().lower() for m in args.mods]

cfg = Config()
cfg.logging.console = True
cfg.logging.level = "DEBUG"
if args.config is not None:
    Config.model_validate(
        yaml.safe_load(Path(args.config).read_text()))

cfg.core.nginx_version = args.version

for i in cfg.installers:
    classname = i.classname.lower()
    if (
        "all" in mods
        or classname in mods
        or f"{classname}installer" in mods
        or (hasattr(i, "name") and i.name.lower() in mods)
    ):
        i.enabled = True
        if isinstance(i, GeneralGitInstaller):
            i.enabled = bool(i.url)
    if hasattr(i, "dynamic"):
        i.dynamic = args.dynamic

path.write_text(model_dump_yaml(cfg))
