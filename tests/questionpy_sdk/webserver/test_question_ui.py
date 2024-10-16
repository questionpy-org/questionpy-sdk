#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from importlib import resources
from typing import Any

import pytest

from questionpy_sdk.webserver.question_ui import (
    InvalidAttributeValueError,
    QuestionDisplayOptions,
    QuestionDisplayRole,
    QuestionFormulationUIRenderer,
    QuestionMetadata,
    QuestionUIRenderer,
    XMLSyntaxError,
)
from questionpy_sdk.webserver.question_ui.errors import (
    ConversionError,
    InvalidCleanOptionError,
    PlaceholderReferenceError,
    RenderError,
    UnknownElementError,
)
from tests.questionpy_sdk.webserver.conftest import assert_html_is_equal


@pytest.fixture
def xml_content(request: pytest.FixtureRequest) -> str | None:
    marker = request.node.get_closest_marker("ui_file")

    if marker is None:
        return None

    filename = f"{marker.args[0]}.xhtml"
    ui_files = resources.files("tests.questionpy_sdk.webserver.test_data")

    try:
        return next(path for path in ui_files.iterdir() if path.name == filename).read_text()
    except StopIteration as err:
        raise FileNotFoundError(ui_files / filename) from err


@pytest.fixture
def renderer(request: pytest.FixtureRequest, xml_content: str | None) -> QuestionUIRenderer:
    renderer_kwargs: dict[str, Any] = {
        "placeholders": {},
        "xml": xml_content,
        "options": QuestionDisplayOptions(),
    }

    marker = request.node.get_closest_marker("render_params")
    if marker is not None:
        renderer_kwargs |= marker.kwargs

    return QuestionUIRenderer(**renderer_kwargs)


@pytest.mark.ui_file("metadata")
def test_should_extract_correct_metadata(xml_content: str) -> None:
    ui_renderer = QuestionFormulationUIRenderer(xml_content, {}, QuestionDisplayOptions())
    question_metadata = ui_renderer.metadata

    expected_metadata = QuestionMetadata()
    expected_metadata.correct_response = {
        "my_number": "42",
        "my_select": "1",
        "my_radio": "2",
        "my_text": "Lorem ipsum dolor sit amet.",
    }
    expected_metadata.expected_data = {
        "my_number": "Any",
        "my_select": "Any",
        "my_radio": "Any",
        "my_text": "Any",
        "my_button": "Any",
        "only_lowercase_letters": "Any",
        "between_5_and_10_chars": "Any",
    }
    expected_metadata.required_fields = ["my_number"]

    assert question_metadata.correct_response == expected_metadata.correct_response
    assert question_metadata.expected_data == expected_metadata.expected_data
    assert question_metadata.required_fields == expected_metadata.required_fields


@pytest.mark.ui_file("placeholder")
@pytest.mark.render_params(
    placeholders={
        "param": "Value of param <b>one</b>.<script>'Oh no, danger!'</script>",
        "description": "My simple description.",
    }
)
def test_should_resolve_placeholders(renderer: QuestionUIRenderer) -> None:
    expected = """
    <div>
        <div>My simple description.</div>
        <span>By default cleaned parameter: Value of param <b>one</b>.</span>
        <span>Explicitly cleaned parameter: Value of param <b>one</b>.</span>
        <span>Noclean parameter: Value of param <b>one</b>.<script>'Oh no, danger!'</script></span>
        <span>Plain parameter:
            Value of param &lt;b>one&lt;/b>.&lt;script>'Oh no, danger!'&lt;/script>
        </span>
    </div>
    """
    html, errors = renderer.render()
    assert len(errors) == 0
    assert_html_is_equal(html, expected)


@pytest.mark.ui_file("feedbacks")
@pytest.mark.render_params(options=QuestionDisplayOptions(general_feedback=False, feedback=False))
def test_should_hide_inline_feedback(renderer: QuestionUIRenderer) -> None:
    expected = """
        <div>
            <span>No feedback</span>
        </div>
    """
    html, errors = renderer.render()
    assert len(errors) == 0
    assert_html_is_equal(html, expected)


@pytest.mark.ui_file("feedbacks")
def test_should_show_inline_feedback(renderer: QuestionUIRenderer) -> None:
    expected = """
        <div>
            <span>No feedback</span>
            <span>General feedback</span>
            <span>Specific feedback</span>
        </div>
    """
    html, errors = renderer.render()
    assert len(errors) == 0
    assert_html_is_equal(html, expected)


@pytest.mark.parametrize(
    ("options", "expected"),
    [
        (
            QuestionDisplayOptions(roles=set()),
            "<div></div>",
        ),
        (
            QuestionDisplayOptions(roles={QuestionDisplayRole.SCORER}),
            """
                <div>
                    <div>You're a scorer!</div>
                    <div>You're any of the above!</div>
                </div>
            """,
        ),
        (
            QuestionDisplayOptions(),
            """
                <div>
                    <div>You're a teacher!</div>
                    <div>You're a developer!</div>
                    <div>You're a scorer!</div>
                    <div>You're a proctor!</div>
                    <div>You're any of the above!</div>
                </div>
            """,
        ),
    ],
)
@pytest.mark.ui_file("if-role")
def test_element_visibility_based_on_role(options: QuestionDisplayOptions, expected: str, xml_content: str) -> None:
    html, errors = QuestionUIRenderer(xml_content, {}, options).render()
    assert len(errors) == 0
    assert_html_is_equal(html, expected)


@pytest.mark.ui_file("inputs")
@pytest.mark.render_params(
    attempt={
        "my_text": "text user input",
        "my_select": "2",
        "my_textarea": "textarea user input",
        "my_checkbox": "checkbox_value",
        "my_radio": "radio_value_2",
    }
)
def test_should_set_input_values(renderer: QuestionUIRenderer) -> None:
    expected = """
        <div>
            <button name="my_button" type="button" class="btn btn-primary qpy-input">Button</button>
            <input type="button" value="Submit" class="btn btn-primary qpy-input"/>
            <input name="my_text" type="text" value="text user input" class="form-control qpy-input"/>
            <select name="my_select" class="form-control qpy-input">
                <option value="1">One</option>
                <option value="2" selected="selected">Two</option>
            </select>
            <textarea name="my_textarea" class="form-control qpy-input">textarea user input</textarea>
            <input name="my_checkbox" type="checkbox" value="checkbox_value" class="qpy-input" checked="checked"/>
            <input name="my_radio" type="radio" value="radio_value_1" class="qpy-input"/>
            <input name="my_radio" type="radio" value="radio_value_2" class="qpy-input" checked="checked"/>
        </div>
    """
    html, errors = renderer.render()
    assert len(errors) == 0
    assert_html_is_equal(html, expected)


@pytest.mark.ui_file("inputs")
@pytest.mark.render_params(options=QuestionDisplayOptions(readonly=True))
def test_should_disable_inputs(renderer: QuestionUIRenderer) -> None:
    expected = """
        <div>
            <button name="my_button" type="button" disabled="disabled" class="btn btn-primary qpy-input">Button</button>
            <input type="button" value="Submit" disabled="disabled" class="btn btn-primary qpy-input"/>
            <input name="my_text" type="text" value="some_value" disabled="disabled" class="form-control qpy-input"/>
            <select name="my_select" disabled="disabled" class="form-control qpy-input">
                <option value="1">One</option>
                <option value="2">Two</option>
            </select>
            <textarea name="my_textarea" disabled="disabled" class="form-control qpy-input"/>
            <input name="my_checkbox" type="checkbox" value="checkbox_value" disabled="disabled" class="qpy-input"/>
            <input name="my_radio" type="radio" value="radio_value_1" disabled="disabled" class="qpy-input"/>
            <input name="my_radio" type="radio" value="radio_value_2" disabled="disabled" class="qpy-input"/>
        </div>
    """
    html, errors = renderer.render()
    assert len(errors) == 0
    assert_html_is_equal(html, expected)


@pytest.mark.ui_file("validations")
def test_should_soften_validations(renderer: QuestionUIRenderer) -> None:
    expected = """
        <div>
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
    html, errors = renderer.render()
    assert len(errors) == 0
    assert_html_is_equal(html, expected)


@pytest.mark.ui_file("buttons")
def test_should_defuse_buttons(renderer: QuestionUIRenderer) -> None:
    expected = """
        <div>
            <button class="btn btn-primary qpy-input" type="button">Submit</button>
            <button class="btn btn-primary qpy-input" type="button">Reset</button>
            <button class="btn btn-primary qpy-input" type="button">Button</button>

            <input class="btn btn-primary qpy-input" type="button" value="Submit"/>
            <input class="btn btn-primary qpy-input" type="button" value="Reset"/>
            <input class="btn btn-primary qpy-input" type="button" value="Button"/>
        </div>
    """
    html, errors = renderer.render()
    assert len(errors) == 0
    assert_html_is_equal(html, expected)


@pytest.mark.skip("""1. The text directly in the root of <qpy:formulation> is not copied in render_part.
                     2. format_floats adds decimal 0 to numbers without decimal part""")
@pytest.mark.ui_file("format-floats")
def test_should_format_floats_in_en(renderer: QuestionUIRenderer) -> None:
    expected = """
        <div>
            Just the decsep: <span>1.23456</span>
            Thousands sep without decimals: <span>1,000,000,000</span>
            Thousands sep with decimals: <span>10,000,000,000.123</span>
            Round down: <span>1.11</span>
            Round up: <span>1.12</span>
            Pad with zeros: <span>1.10000</span>
            Strip zeros: <span>1.1</span>
        </div>
    """
    html, errors = renderer.render()
    assert len(errors) == 0
    assert_html_is_equal(html, expected)


@pytest.mark.ui_file("shuffle")
@pytest.mark.render_params(seed=42)
def test_should_shuffle_the_same_way_in_same_attempt(renderer: QuestionUIRenderer, xml_content: str) -> None:
    expected_html, _ = renderer.render()
    for _ in range(10):
        html, errors = QuestionUIRenderer(xml_content, {}, QuestionDisplayOptions(), seed=42).render()
        assert len(errors) == 0
        assert html == expected_html, "Shuffled order should remain consistent across renderings with the same seed"


@pytest.mark.ui_file("shuffled-index")
@pytest.mark.render_params(seed=42)
def test_should_replace_shuffled_index(renderer: QuestionUIRenderer) -> None:
    expected = """
        <div>
            <fieldset>
                <label>
                    <input type="radio" name="choice" value="B" class="qpy-input"/>
                    <span>i</span>. B
                </label>
                <label>
                    <input type="radio" name="choice" value="A" class="qpy-input"/>
                    <span>ii</span>. A
                </label>
                <label>
                    <input type="radio" name="choice" value="C" class="qpy-input"/>
                    <span>iii</span>. C
                </label>
            </fieldset>
        </div>
        """
    html, errors = renderer.render()
    assert len(errors) == 0
    assert_html_is_equal(html, expected)


@pytest.mark.render_params(
    xml="""
        <div xmlns:qpy="http://questionpy.org/ns/question">
            <element qpy:attribute="value">Content</element>
            <!-- Comment -->
            <regular xmlns:qpy="http://questionpy.org/ns/question">Normal Content</regular>
        </div>
    """
)
def test_clean_up(renderer: QuestionUIRenderer) -> None:
    expected = """
        <div>
            <element>Content</element>
            <regular>Normal Content</regular>
        </div>
    """
    html, errors = renderer.render()
    assert len(errors) == 0
    assert_html_is_equal(html, expected)


@pytest.mark.ui_file("qpy-urls")
def test_should_replace_qpy_urls(renderer: QuestionUIRenderer) -> None:
    expected = """
        <div>
            <link rel="stylesheet" href="/worker/foo/bar/file/static/style.css"/>
            <script src="/worker/foo/bar/file/static/script.js"></script>
            <img src="/worker/acme/example/file/static-private/some/nested/path/img.png"/>
            <p>/worker/acme/example/file/static/some/link</p>
            <p>/worker/acme/example/file/static-private/some/other/link</p>
            <p>qpy://test/acme/example/broken/qpy-url</p>
            <p>qpy://static/broken/example</p>
        </div>
    """
    html, errors = renderer.render()
    assert len(errors) == 0
    assert_html_is_equal(html, expected)


@pytest.mark.ui_file("faulty")
def test_errors_should_be_collected(renderer: QuestionUIRenderer) -> None:
    expected = """
        <div>
            <fieldset><label>Invalid shuffle format. . A</label></fieldset>
            <div>Missing placeholder.</div>
            <div>Empty placeholder.</div>
            <span>Missing attribute value.</span>
        </div>
    """
    html, errors = renderer.render()
    assert len(errors) == 11

    expected_errors: list[tuple[type[RenderError], int]] = [
        # Even though the syntax error occurs after all the other errors, it should be listed first.
        (XMLSyntaxError, 14),
        (InvalidAttributeValueError, 2),
        (UnknownElementError, 3),
        (InvalidAttributeValueError, 4),
        (ConversionError, 5),
        (ConversionError, 5),
        (InvalidAttributeValueError, 5),
        (InvalidAttributeValueError, 9),
        (InvalidCleanOptionError, 12),
        (PlaceholderReferenceError, 12),
        (PlaceholderReferenceError, 13),
    ]

    for actual_error, expected_error in zip(errors, expected_errors, strict=True):
        error_type, line = expected_error
        assert isinstance(actual_error, error_type)
        assert actual_error.line == line

    assert_html_is_equal(html, expected)
