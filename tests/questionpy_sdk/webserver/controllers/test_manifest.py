#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from unittest.mock import Mock

import pytest

from questionpy_common.manifest import Bcp47LanguageTag, Manifest
from questionpy_sdk.webserver.controllers.manifest import ManifestController


@pytest.fixture
def controller(mock_webserver: Mock) -> ManifestController:
    return ManifestController(mock_webserver)


def test_get_manifest(controller: ManifestController, mock_webserver: Mock) -> None:
    test_manifest = Manifest(
        short_name="foo",
        version="0.0.1",
        api_version="0.1",
        author="Jane Doe <jane.doe@example.org>",
        name={Bcp47LanguageTag("en"): "Test Package"},
        languages=[Bcp47LanguageTag("de"), Bcp47LanguageTag("en")],
    )
    mock_webserver.manifest = test_manifest
    manifest = controller.get_manifest()

    assert manifest == test_manifest
