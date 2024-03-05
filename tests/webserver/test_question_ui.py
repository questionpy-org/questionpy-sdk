#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from pathlib import Path

import pytest

from questionpy_sdk.webserver.question_ui import QuestionUIRenderer, QuestionMetadata, QuestionDisplayOptions
from tests.webserver.conftest import compare_xhtml


def test_should_extract_correct_metadata() -> None:
    metadata_path = Path(__file__).parent / 'question_uis/metadata.xhtml'
    with metadata_path.open() as xml:
        ui_renderer = QuestionUIRenderer(xml.read(), {})
        question_metadata = ui_renderer.get_metadata()

        expected_metadata = QuestionMetadata()
        expected_metadata.correct_response = {"my_number": "42", "my_select": "1", "my_radio": "2",
                                              "my_text": "Lorem ipsum dolor sit amet."}
        expected_metadata.expected_data = {"my_number": "Any", "my_select": "Any", "my_radio": "Any", "my_text": "Any",
                                           "my_button": "Any", "only_lowercase_letters": "Any",
                                           "between_5_and_10_chars": "Any"}
        expected_metadata.required_fields = ["my_number"]

        assert question_metadata.correct_response == expected_metadata.correct_response
        assert question_metadata.expected_data == expected_metadata.expected_data
        assert question_metadata.required_fields == expected_metadata.required_fields


def test_should_resolve_placeholders() -> None:
    placeholder_path = Path(__file__).parent / 'question_uis/placeholder.xhtml'
    with placeholder_path.open() as xml:
        renderer = QuestionUIRenderer(xml=xml.read(), placeholders={
            "param": "Value of param <b>one</b>.<script>'Oh no, danger!'</script>",
            "description": "My simple description."})
        result = renderer.render_formulation()

    # TODO: remove <string> surrounding the resolved placeholder
    expected = """
    <div xmlns="http://www.w3.org/1999/xhtml">
        <div><string>My simple description.</string></div>
        <span>By default cleaned parameter: <string>Value of param <b>one</b>.</string></span>
        <span>Explicitly cleaned parameter: <string>Value of param <b>one</b>.</string></span>
        <span>Noclean parameter: <string>Value of param <b>one</b>.<script>'Oh no, danger!'</script></string></span>
        <span>Plain parameter:
            <string><![CDATA[Value of param <b>one</b>.<script>'Oh no, danger!'</script>]]></string>
        </span>
    </div>
    """

    assert compare_xhtml(result, expected)


def test_should_hide_inline_feedback() -> None:
    options = QuestionDisplayOptions()
    options.general_feedback = False
    options.feedback = False

    feedback_path = Path(__file__).parent / 'question_uis/feedbacks.xhtml'
    with feedback_path.open() as xml:
        renderer = QuestionUIRenderer(xml=xml.read(), placeholders={})
        result = renderer.render_formulation(options=options)

    expected = """
    <div xmlns="http://www.w3.org/1999/xhtml">
    <span>No feedback</span>
    </div>
    """
    assert compare_xhtml(result, expected)


def test_should_show_inline_feedback() -> None:
    options = QuestionDisplayOptions()

    feedback_path = Path(__file__).parent / 'question_uis/feedbacks.xhtml'
    with feedback_path.open() as xml:
        renderer = QuestionUIRenderer(xml=xml.read(), placeholders={})
        result = renderer.render_formulation(options=options)

    expected = """
    <div xmlns="http://www.w3.org/1999/xhtml">
    <span>No feedback</span>
    <span>General feedback</span>
    <span>Specific feedback</span>
    </div>
    """
    assert compare_xhtml(result, expected)


@pytest.mark.parametrize("user_context, expected", [('guest', """
     <div xmlns="http://www.w3.org/1999/xhtml"></div>
     """), ('admin', """
     <div xmlns="http://www.w3.org/1999/xhtml">
         <div>You're a teacher!</div>
         <div>You're a developer!</div>
         <div>You're a scorer!</div>
         <div>You're a proctor!</div>
         <div>You're any of the above!</div>
     </div>
     """), ])
def test_element_visibility_based_on_role(user_context: str, expected: str) -> None:
    options = QuestionDisplayOptions()
    options.context['role'] = user_context

    feedback_path = Path(__file__).parent / 'question_uis/if-role.xhtml'
    with feedback_path.open() as xml:
        renderer = QuestionUIRenderer(xml=xml.read(), placeholders={})
        result = renderer.render_formulation(options=options)

    assert compare_xhtml(result, expected)


def test_should_soften_validations() -> None:
    options = QuestionDisplayOptions()

    validation_path = Path(__file__).parent / 'question_uis/validations.xhtml'
    with validation_path.open() as xml:
        renderer = QuestionUIRenderer(xml=xml.read(), placeholders={})
        result = renderer.render_formulation(options=options)

    expected = """
    <div xmlns="http://www.w3.org/1999/xhtml">
        <input data-qpy_required="true" aria-required="true"/>
        <input data-qpy_pattern="^[a-z]+$"/>
        <input data-qpy_minlength="5"/>
        <input data-qpy_minlength="10"/>
        <input data-qpy_min="17" aria-valuemin="17"/>
        <input data-qpy_max="42" aria-valuemax="42"/>
        <input data-qpy_pattern="^[a-z]+$" data-qpy_required="true" aria-required="true"
               data-qpy_minlength="5" data-qpy_maxlength="10" data-qpy_min="17"
               aria-valuemin="17" data-qpy_max="42" aria-valuemax="42"/>
    </div>
    """

    assert compare_xhtml(result, expected)


def test_should_defuse_buttons() -> None:
    options = QuestionDisplayOptions()

    feedback_path = Path(__file__).parent / 'question_uis/buttons.xhtml'
    with feedback_path.open() as xml:
        renderer = QuestionUIRenderer(xml=xml.read(), placeholders={})
        result = renderer.render_formulation(options=options)

    expected = '''
    <div xmlns="http://www.w3.org/1999/xhtml">
        <button class="btn btn-primary qpy-input" type="button">Submit</button>
        <button class="btn btn-primary qpy-input" type="button">Reset</button>
        <button class="btn btn-primary qpy-input" type="button">Button</button>

        <input class="btn btn-primary qpy-input" type="button" value="Submit"/>
        <input class="btn btn-primary qpy-input" type="button" value="Reset"/>
        <input class="btn btn-primary qpy-input" type="button" value="Button"/>
    </div>
    '''
    assert compare_xhtml(result, expected)


@pytest.mark.skip("""1. The text directly in the root of <qpy:formulation> is not copied in render_part.
                    2. format_floats adds decimal 0 to numbers without decimal part""")
def test_should_format_floats_in_en() -> None:
    options = QuestionDisplayOptions()

    feedback_path = Path(__file__).parent / 'question_uis/format-floats.xhtml'
    with feedback_path.open() as xml:
        renderer = QuestionUIRenderer(xml=xml.read(), placeholders={})
        result = renderer.render_formulation(options=options)

    expected = '''
    <div xmlns="http://www.w3.org/1999/xhtml">
        Just the decsep: <span>1.23456</span>
        Thousands sep without decimals: <span>1,000,000,000</span>
        Thousands sep with decimals: <span>10,000,000,000.123</span>
        Round down: <span>1.11</span>
        Round up: <span>1.12</span>
        Pad with zeros: <span>1.10000</span>
        Strip zeros: <span>1.1</span>
    </div>
    '''
    assert compare_xhtml(result, expected)


def test_should_shuffle_the_same_way_in_same_attempt() -> None:
    feedback_path = Path(__file__).parent / 'question_uis/shuffle.xhtml'
    with feedback_path.open() as xml:
        input_xml = xml.read()

    renderer = QuestionUIRenderer(xml=input_xml, placeholders={}, seed=42)
    first_result = renderer.render_formulation()
    for _ in range(10):
        renderer = QuestionUIRenderer(xml=input_xml, placeholders={}, seed=42)
        result = renderer.render_formulation()
        assert first_result == result, "Shuffled order should remain consistent across renderings with the same seed"


def test_should_replace_shuffled_index() -> None:
    feedback_path = Path(__file__).parent / 'question_uis/shuffled-index.xhtml'
    with feedback_path.open() as xml:
        input_xml = xml.read()

    renderer = QuestionUIRenderer(xml=input_xml, placeholders={}, seed=42)
    result = renderer.render_formulation()

    expected = """
        <div xmlns="http://www.w3.org/1999/xhtml"><fieldset>
            <label>
                <input type="radio" name="choice" value="B"/>
                <span>i</span>. B
            </label>
            <label>
                <input type="radio" name="choice" value="A"/>
                <span>ii</span>. A
            </label>
            <label>
                <input type="radio" name="choice" value="C"/>
                <span>iii</span>. C
            </label>
        </fieldset>
    </div>
        """
    assert compare_xhtml(result, expected)


def test_clean_up() -> None:
    xml_content = '''
    <qpy:question xmlns:qpy="http://questionpy.org/ns/question">
        <qpy:formulation>
            <qpy:element>Text</qpy:element>
            <element qpy:attribute="value">Content</element>
            <!-- Comment -->
            <regular xmlns:qpy="http://questionpy.org/ns/question">Normal Content</regular>
        </qpy:formulation>
    </qpy:question>
    '''
    renderer = QuestionUIRenderer(xml=xml_content, placeholders={})
    result = renderer.render_formulation()

    expected = """
    <div xmlns="http://www.w3.org/1999/xhtml">
        <element>Content</element>
        <regular>Normal Content</regular>
    </div>
    """
    assert compare_xhtml(result, expected)
