#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from collections.abc import Callable
from pathlib import Path
from shutil import copytree

import pytest

from questionpy_common.constants import DIST_DIR
from questionpy_sdk._package import ZipBuildTarget, build_qpy_package
from questionpy_sdk._package.source import PackageSource


@pytest.fixture
def source_path(request: pytest.FixtureRequest, tmp_path: Path) -> Path:
    marker = request.node.get_closest_marker("source_pkg")
    example_pkg = "minimal" if marker is None else marker.args[0]

    src_path = Path(__file__).parent.parent / "examples" / example_pkg
    dest_path = tmp_path / example_pkg
    copytree(src_path, dest_path, ignore=lambda src, names: (DIST_DIR,))

    return dest_path


@pytest.fixture
def qpy_pkg_path(tmp_path: Path, source_path: Path) -> Path:
    qpy_path = tmp_path / "package.qpy"
    build_qpy_package(PackageSource(source_path), ZipBuildTarget(qpy_path))
    return qpy_path


@pytest.fixture
def port(unused_tcp_port_factory: Callable) -> int:
    return unused_tcp_port_factory()
