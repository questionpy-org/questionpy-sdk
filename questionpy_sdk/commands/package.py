import inspect
import logging
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Optional

import click
import yaml
from questionpy_common.manifest import Manifest

import questionpy
from questionpy_sdk.package import PackageBuilder

log = logging.getLogger(__name__)


def validate_out_path(context: click.Context, _parameter: click.Parameter, value: Optional[Path]) -> Optional[Path]:
    if value and value.suffix != '.qpy':
        raise click.BadParameter("Packages need the extension '.qpy'.", ctx=context)
    return value


@click.command()
@click.argument("source", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--manifest", "-m", "manifest_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--out", "-o", "out_path", callback=validate_out_path,
              type=click.Path(exists=False, dir_okay=False, path_type=Path))
def package(source: Path, manifest_path: Optional[Path], out_path: Optional[Path]) -> None:
    if not out_path:
        out_path = source.with_suffix(".qpy")

    if not manifest_path:
        manifest_path = source / "qpy_manifest.yml"

    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)

    with manifest_path.open() as manifest_f:
        manifest = Manifest.parse_obj(yaml.safe_load(manifest_f))

    with PackageBuilder(out_path, manifest) as out_file:
        _copy_package(out_file, questionpy)
        _install_dependencies(out_file, manifest_path, manifest)
        out_file.write_glob(source, "**/python/*.py")
        out_file.write_manifest()


def _install_dependencies(target: PackageBuilder, manifest_path: Path, manifest: Manifest) -> None:
    if isinstance(manifest.requirements, str):
        # treat as a relative reference to a requirements.txt and read those
        pip_args = ["-r", str(manifest_path.parent / manifest.requirements)]
    elif isinstance(manifest.requirements, list):
        # treat as individual dependency specifiers
        pip_args = manifest.requirements
    else:
        # no dependencies specified
        return

    with TemporaryDirectory(prefix=f"qpy_{manifest.short_name}") as tempdir:
        subprocess.run(["pip", "install", "--target", tempdir, *pip_args], check=True)
        target.write_glob(Path(tempdir), "**/*", prefix="dependencies/site-packages")


def _copy_package(target: PackageBuilder, pkg: ModuleType) -> None:
    # inspect.getfile returns the path to the package's __init__.py
    package_dir = Path(inspect.getfile(pkg)).parent
    target.write_glob(package_dir, "**/*.py", prefix=f"dependencies/site-packages/{pkg.__name__}")
