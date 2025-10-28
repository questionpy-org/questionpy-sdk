#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from questionpy_common.manifest import Bcp47LanguageTag, SourceManifest
from questionpy_sdk.models import PackageConfig


def test_package_config_strips_config_fields() -> None:
    config = PackageConfig(
        short_name="foo",
        version="0.0.1",
        api_version="0.1",
        author="John Doe",
        build_hooks={"pre": "npm start"},
        name={Bcp47LanguageTag("en"): "Test Package"},
        languages=[Bcp47LanguageTag("en")],
    )
    exp = SourceManifest(
        short_name="foo",
        version="0.0.1",
        api_version="0.1",
        author="John Doe",
        name={Bcp47LanguageTag("en"): "Test Package"},
        languages=[Bcp47LanguageTag("en")],
    )
    assert dict(config.to_manifest()) == dict(exp)
