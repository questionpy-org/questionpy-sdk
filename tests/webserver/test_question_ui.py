#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from pathlib import Path

from questionpy_sdk.webserver.question_ui import QuestionUIRenderer, QuestionMetadata


def test_should_extract_correct_metadata() -> None:
    metadata_path = Path(__file__).parent / 'question_uis/metadata.xhtml'
    with metadata_path.open() as xml:
        ui_renderer = QuestionUIRenderer(xml.read(), [])
        question_metadata = ui_renderer.get_metadata()

        expected_metadata = QuestionMetadata()
        expected_metadata.correct_response = {
            "my_number": "42",
            "my_select": "1",
            "my_radio": "2",
            "my_text": "Lorem ipsum dolor sit amet."
        }
        expected_metadata.expected_data = {
            "my_number": "Any",
            "my_select": "Any",
            "my_radio": "Any",
            "my_text": "Any",
            "my_button": "Any",
            "only_lowercase_letters": "Any",
            "between_5_and_10_chars": "Any"
        }
        expected_metadata.required_fields = ["my_number"]

        assert question_metadata.correct_response == expected_metadata.correct_response
        assert question_metadata.expected_data == expected_metadata.expected_data
        assert question_metadata.required_fields == expected_metadata.required_fields
