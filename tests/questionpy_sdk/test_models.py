#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from questionpy_common.manifest import SourceManifest
from questionpy_sdk.models import PackageConfig


def test_package_config_strips_config_fields() -> None:
    config = PackageConfig(
        short_name="foo",
        version="0.0.1",
        api_version="0.1",
        author="John Doe",
        build_hooks={"pre": "npm start"},
    )
    exp = SourceManifest(
        short_name="foo",
        version="0.0.1",
        api_version="0.1",
        author="John Doe",
    )
    assert dict(config.manifest) == dict(exp)
