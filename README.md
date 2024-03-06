# Auto Nginx Installation Script

This script is designed to install Nginx on modern Ubuntu, other Debian-based systems might also work.

## Supported Modules

- Many common first-party modules (Check auto-generated `config.yaml` for details)
- [Dynamic Record Resizing for TLS](https://github.com/nginx-modules/ngx_http_tls_dyn_size)
- [brotli](https://github.com/google/ngx_brotli)
- [headers-more](https://github.com/openresty/headers-more-nginx-module)
- [geoip2](https://github.com/leev/ngx_http_geoip2_module)
- [fancyindex](https://github.com/aperezdc/ngx-fancyindex)
- OpenSSL from source

Go to discussions to request more modules.

## Installation

```bash
pip install -U nginx_install
```

or

```bash
git clone https://github.com/VermiIIi0n/nginx_install.git
cd nginx_install
pip install -U poetry
poetry install
```

## Quick Start

Create a `config.yaml`, use any `action` as the first argument, it won't actually run if `config.yaml` is not found.

```bash
nginx_install uninstall --dry ## creates a config.yaml file and quits
```

Edit your `config.yaml` and run the following command to install Nginx:

```bash
nginx_install install
```

To uninstall Nginx, use the following command:

```bash
nginx_install uninstall
```

## Usage

### Installed by `pip`

```bash
nginx_install { prepare | build | install | uninstall | clean } [build_dir]
```

When you first run the script, you will be asked to create a `config.yaml` under the current directory. You may not want to run as root when creating the `config.yaml` file.
You can also specify the file using the `-c`/`--config` option.

The first positional argument is the action to be performed.

The second positional argument is optional and is used to specify the build directory. If not specified, the default build directory is used.

When running the script for real business, you might want to run as root, because the script needs to install packages and create directories.

To just build the Nginx binary, use the following command:

```bash
nginx_install build
```

To just install without building, use the following command:

```bash
nginx_install install --no-build
```

To build and install Nginx, use the following command:

```bash
nginx_install install
```

**NOTICE: `build` and `install` both delete the previous build directory and create a new one.**

Currently not supporting cross-compiling. If your target system is the same as the build system, you can copy the build directory to the target system and run `install --no-build` there.

### Installed by `git clone`

If you cloned the repository, use the following command to run the script:

```bash
poetry run `which python` nginx_install <...>
```

## Dry Run

Use `--dry` to run the script in dry-run mode. In this mode, the script will not change anything outside of `build_dir` but will print the commands to be executed.

```bash
nginx_install --dry build
```

**no root should be required if you have access to the build directory.**

## Configuration

The `config.yaml` file is used to specify the version of Nginx to be installed, the modules to be included, and the build options.

Use `-c`/`--config` to specify the path of the `config.yaml` file. By default, it is `config.yaml` under the current directory.

If not specified, the script will search for the `./config.yaml` file, and if not found, it will ask you to create one.

If `-q`/`--quiet` is specified, the script will not ask you to create one and will exit with an error if not found.

Useful options in `config.yaml`:

- `version`: The version of Nginx to be installed. Can be `stable`, `mainline`, `latest`, or a simple spec version (e.g. `1.21.3`, `^1.24.0`, `<=1.26.0`).
- `pymodule_paths`: A list of paths to Python modules. Convenient for adding custom `Installer` classes.

## Customization

You can easily add your own modules to modify the installation of Nginx (e.g. add custom modules, change build options, etc.).

All `Installer` classes are descendants of the `BaseInstaller` class.

Every `Installer` class has 5 `async` methods corresponding to the 5 stages of the installation process:

- `prepare`
- `build`
- `install`
- `uninstall`
- `clean`

They all accept a special [`context`](#context) parameter, which contains useful information about the installation process. You must override these methods in inherited classes.

During installation running, installers go through `prepare`, `build`, `install` and `clean` stages. During uninstallation running, installers go through `uninstall` and `clean` stages.

A special `Installer` called `core` represents the core binary installer of Nginx. In every stage, the core installer methods are called first, and then the methods of other installers are called. The order of the other installers is random. This is done to reduce build time.

You can access `core` through the `context` parameter. Parameters like Nginx `configure options` are stored in `core` and can be modified.

### Context

The `context` parameter is a dictionary containing the following attributes:

- `build_dir`: The build directory.
- `cfg`: The `Config` object from the `config.yaml` file.
- `core`: The `NginxInstaller` object.
- `verbose`: A boolean value indicating whether to print verbose information.
- `dry_run`: A boolean value indicating whether to run the script in dry-run mode. You should respect this value in your custom installers. Don't actually change anything if `dry_run` is `True`.
- `client`: A `httpx.AsyncClient` object. You can use it to download files from the internet.
- `logger`: You can use it to log information.
- `progress`: A `rich.progress.Progress` object. You can use it to show a progress bar.
- `run_cmd`: An `async` function to run shell commands. You should use it to run shell commands in your custom installers. When `dry_run` is `True`, it will only print the command to be executed.
- `download`: An `async` function to download files from the internet. You should use it to download files in your custom installers. It automatically shows a progress bar when downloading files.
