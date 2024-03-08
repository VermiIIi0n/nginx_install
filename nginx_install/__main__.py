import sys
import os
import asyncio
import argparse
import yaml
import tempfile
import shutil
from typing import Literal
from pathlib import Path
from getpass import getuser
from nginx_install.config import Config
from nginx_install.context import Context
from nginx_install.utils import model_dump_yaml
from subprocess import CalledProcessError


async def main() -> int:  # skipcq: PY-R1000
    parser = argparse.ArgumentParser(
        "nginx_install", description="nginx installation script")
    parser.add_argument("action", type=str, help="Action to perform", choices=[
                        "prepare", "build", "install", "uninstall", "clean"])
    parser.add_argument("build_dir", type=str,
                        help="Directory to build in", nargs="?", default=None)
    parser.add_argument("-V", "--version", action="version", version="0.0.1")
    parser.add_argument("-c", "--config", type=str,
                        help="Path to config file", default="config.yaml")
    parser.add_argument("-u", "--user", type=str,
                        help="User to own build_dir", default=getuser())
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Suppress all output unless error occurs")
    parser.add_argument("-r", "--reload", action="store_true",
                        help="Reload Nginx after install")
    parser.add_argument("--keep-build", action="store_true",
                        help="Keep build directory after completion")
    parser.add_argument("--no-build", action="store_true",
                        help="Skip build step in install action")
    parser.add_argument("--dry", action="store_true",
                        help="Dry run, print commands that would be executed")
    parser.add_argument("--verbose", action="store_true",
                        help="Print debug information")
    args = parser.parse_args()

    action: Literal["install", "uninstall", "build", "clean"] = args.action

    if args.build_dir is None:
        if action == "clean":
            sys.stderr.write("No build directory specified")
            return 1
        build_dir = Path(tempfile.mkdtemp())
    else:
        build_dir = Path(args.build_dir)

    config_path = Path(args.config)
    if not config_path.exists():
        if args.quiet:
            return 1
        print(f"Config file {config_path} does not exist")
        user_input = input("Do you want to create it? [Y/n] ").strip() or 'y'
        if user_input.lower() != 'y':
            return 1
        config = Config()
        config_path.write_text(model_dump_yaml(config))
        print(f"Config file {config_path} created")
        return 0

    euid = os.geteuid()
    if euid != 0:
        fwd_args = ["sudo", "-E", sys.executable, *sys.argv, "-u", args.user]
        os.execlpe("/usr/bin/sudo", *fwd_args, os.environ)

    if build_dir.exists() and (not args.no_build or args.keep_build):
        shutil.rmtree(build_dir)
    build_dir.mkdir(exist_ok=True)

    config = Config.model_validate(yaml.safe_load(config_path.read_text()))
    ctx = Context(config, build_dir, args.dry,
                  args.verbose, args.quiet, args.user)
    logger = ctx.logger
    logger.debug("All extra installers in config: %s", config.installers)
    config.installers = [i for i in config.installers if i.enabled]
    installers = config.installers
    logger.info("Enabled extra installers %s", installers)

    try:
        if action in ("prepare", "install", "build"):
            await config.core.prepare(ctx)
            await asyncio.gather(*(i.prepare(ctx) for i in installers))

        if action in ("install", "build") and not args.no_build:
            await config.core.build(ctx)
            await asyncio.gather(*(i.build(ctx) for i in installers))

        if action == "install":
            await config.core.install(ctx)
            await asyncio.gather(*(i.install(ctx) for i in installers))

        if action == "uninstall":
            await config.core.uninstall(ctx)
            await asyncio.gather(*(i.uninstall(ctx) for i in config.installers))

        if action in ("clean", "install", "uninstall") and not args.keep_build:
            await config.core.clean(ctx)
            await asyncio.gather(*(i.clean(ctx) for i in config.installers))

        ctx.print(f"Completed {action} action")

    except CalledProcessError as e:
        err_msg = f"Command {e.cmd} returned status {e.returncode}, error: {e.stderr}"
        logger.critical(err_msg)
        sys.stderr.write(err_msg)
        logger.exception(e)
        logger.debug("Error output: %s", e.output)
        return 1

    except Exception as e:
        err_msg = f"An error occurred: {e}"
        logger.critical(err_msg)
        sys.stderr.write(err_msg)
        logger.exception(e)
        return 1

    else:
        if action == "install" and args.reload:
            rs = await ctx.run_cmd("nginx -t")
            if rs.failed:
                sys.stderr.write("Nginx configuration test failed")
                sys.stderr.write(rs.get_error_str())
                return 1

            rs = await ctx.run_cmd("nginx -s reload")
            if rs.failed:
                sys.stderr.write("Failed to reload Nginx")
                sys.stderr.write(rs.get_error_str())
                return 1

    finally:
        ctx.progress.refresh()
        if build_dir.exists():
            rs = await ctx.run_cmd(
                f"chown -R {ctx.user}:{ctx.user} {build_dir}")

    return 0

sys.exit(asyncio.run(main()))
