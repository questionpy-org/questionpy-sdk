#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from importlib import resources
from typing import Any

import pytest
from lxml import etree

from questionpy_sdk.webserver.controllers.attempt.errors import (
    BaseRenderError,
    ConversionError,
    DuplicateNameError,
    ExpectedAncestorError,
    InvalidAttributeValueError,
    InvalidCleanOptionError,
    InvalidContentError,
    PlaceholderReferenceError,
    UnknownAttributeError,
    UnknownElementError,
    XMLSyntaxError,
)
from questionpy_sdk.webserver.controllers.attempt.question_ui import (
    DisplayRole,
    QuestionDisplayOptions,
    QuestionFormulationUIRenderer,
    QuestionMetadata,
    QuestionUIRenderer,
)


def normalize_element(element: etree._Element) -> etree._Element:
    """Recursively normalize an XML element by sorting attributes and normalizing whitespace."""
    if element.text:
        element.text = " ".join(element.text.split())
    if element.tail:
        element.tail = " ".join(element.tail.split())

    if element.attrib:
        attributes = sorted(element.attrib.items())
        element.attrib.clear()
        element.attrib.update(attributes)

    for child in element:
        normalize_element(child)

    return element


def assert_html_is_equal(actual: str, expected: str) -> None:
    parser = etree.HTMLParser(remove_blank_text=True)
    actual_tree = etree.fromstring(actual, parser)
    expected_tree = etree.fromstring(expected, parser)

    normalize_element(actual_tree)
    normalize_element(expected_tree)

    assert etree.tostring(actual_tree, method="c14n") == etree.tostring(expected_tree, method="c14n")


@pytest.fixture
def xml_content(request: pytest.FixtureRequest) -> str | None:
    marker = request.node.get_closest_marker("ui_file")

    if marker is None:
        return None

    filename = f"{marker.args[0]}.xhtml"
    ui_files = resources.files("tests.questionpy_sdk.webserver.controllers.attempt.test_data")

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
        "qpy_url_replacer": lambda _: "",
    }

    marker = request.node.get_closest_marker("render_params")
    if marker is not None:
        renderer_kwargs |= marker.kwargs

    return QuestionUIRenderer(**renderer_kwargs)


@pytest.mark.ui_file("metadata")
def test_should_extract_correct_metadata(xml_content: str) -> None:
    ui_renderer = QuestionFormulationUIRenderer(xml_content, {}, QuestionDisplayOptions(), lambda _: "")
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
    <div xmlns="http://www.w3.org/1999/xhtml">
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
@pytest.mark.render_params(options=QuestionDisplayOptions(general_feedback=False, specific_feedback=False))
def test_should_hide_inline_feedback(renderer: QuestionUIRenderer) -> None:
    expected = """
        <div xmlns="http://www.w3.org/1999/xhtml">
            <span>No feedback</span>
        </div>
    """
    html, errors = renderer.render()
    assert len(errors) == 0
    assert_html_is_equal(html, expected)


@pytest.mark.ui_file("feedbacks")
def test_should_show_inline_feedback(renderer: QuestionUIRenderer) -> None:
    expected = """
        <div xmlns="http://www.w3.org/1999/xhtml">
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
            """
                <div xmlns="http://www.w3.org/1999/xhtml">
                </div>
            """,
        ),
        (
            QuestionDisplayOptions(roles={DisplayRole.SCORER}),
            """
                <div xmlns="http://www.w3.org/1999/xhtml">
                    <div>You're a scorer!</div>
                    <div>You're any of the above!</div>
                </div>
            """,
        ),
        (
            QuestionDisplayOptions(),
            """
                <div xmlns="http://www.w3.org/1999/xhtml">
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
    html, errors = QuestionUIRenderer(xml_content, {}, options, lambda _: "").render()
    assert len(errors) == 0
    assert_html_is_equal(html, expected)


@pytest.mark.ui_file("input-values")
@pytest.mark.render_params(
    attempt={
        "my_text": "new",
        "my_checkbox_value": "value",
        "my_checkbox_on": "on",
        "my_radio": "value1",
        "my_select": "value3",
        "my_hidden": "new",
        "my_button": "should be ignored",
        "my_textarea": "new",
    }
)
def test_should_set_input_values(renderer: QuestionUIRenderer) -> None:
    expected = """
        <div xmlns="http://www.w3.org/1999/xhtml" id="my_div">
            <input class="form-control qpy-input" type="text" name="my_text" value="new"/>

            <input class="qpy-input" type="checkbox" name="my_checkbox_value" value="value" checked="checked"/>
            <input class="qpy-input" type="checkbox" name="my_checkbox_on" checked="checked"/>

            <input class="qpy-input" type="radio" name="my_radio" value="value1" checked="checked"/>
            <input class="qpy-input" type="radio" name="my_radio" value="value2"/>

            <select class="form-control qpy-input" name="my_select">
                <option value="value1"/>
                <option value="value2"/>
                <option value="value3" selected="selected"/>
            </select>

            <input class="form-control qpy-input" type="hidden" name="my_hidden" value="new"/>

            <input class="btn btn-primary qpy-input" name="button_1" type="button" value="value1"/>
            <input class="btn btn-primary qpy-input" name="button_2" type="button" value="value2"/>

            <textarea class="form-control qpy-input" name="my_textarea">new</textarea>
        </div>
    """
    html, errors = renderer.render()
    assert len(errors) == 0
    assert_html_is_equal(html, expected)


@pytest.mark.ui_file("input-values")
@pytest.mark.render_params(options=QuestionDisplayOptions(readonly=True))
def test_should_disable_inputs(renderer: QuestionUIRenderer) -> None:
    expected = """
        <div xmlns="http://www.w3.org/1999/xhtml" id="my_div">
            <input class="form-control qpy-input" type="text" name="my_text" value="original" disabled="disabled"/>

            <input class="qpy-input" type="checkbox" name="my_checkbox_value" value="value" disabled="disabled"/>
            <input class="qpy-input" type="checkbox" name="my_checkbox_on" disabled="disabled"/>

            <input class="qpy-input" type="radio" name="my_radio" value="value1" disabled="disabled"/>
            <input class="qpy-input" type="radio" name="my_radio" value="value2" checked="checked" disabled="disabled"/>

            <select class="form-control qpy-input" name="my_select" disabled="disabled">
                <option value="value1"/>
                <option value="value2" selected="selected"/>
                <option value="value3"/>
            </select>

            <input class="form-control qpy-input" type="hidden" name="my_hidden" value="original" disabled="disabled"/>

            <input class="btn btn-primary qpy-input" name="button_1" type="button" value="value1" disabled="disabled"/>
            <input class="btn btn-primary qpy-input" name="button_2" type="button" value="value2" disabled="disabled"/>

            <textarea class="form-control qpy-input" name="my_textarea" disabled="disabled">original</textarea>
        </div>
    """
    html, errors = renderer.render()
    assert len(errors) == 0
    assert_html_is_equal(html, expected)


@pytest.mark.ui_file("buttons")
def test_should_defuse_buttons(renderer: QuestionUIRenderer) -> None:
    expected = """
        <div xmlns="http://www.w3.org/1999/xhtml">
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


@pytest.mark.skip("format_floats adds decimal 0 to numbers without decimal part")
@pytest.mark.ui_file("format-floats")
def test_should_format_floats_in_en(renderer: QuestionUIRenderer) -> None:
    expected = """
        <div xmlns="http://www.w3.org/1999/xhtml">
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
def test_should_handle_complex_shuffle_scenario(renderer: QuestionUIRenderer, xml_content: str) -> None:
    expected = """
        <div xmlns="http://www.w3.org/1999/xhtml">
            <span>Element 4, shuffled to I</span>
            <span>Element 2, shuffled to 2</span>
            <span>Element 3, shuffled to c</span>
            <div>
                Element 5, shuffled to 4
                <div>
                    <span>Nested element 2, shuffled to 1</span>
                    <span>Nested element 1, shuffled to 2</span>
                </div>
            </div>
            <span>Element 1, shuffled to 5</span>
            <div>
                <span>Nested element 2, shuffled to 1</span>
                <span>Nested element 1, shuffled to 2</span>
            </div>
        </div>
    """
    html, errors = renderer.render()
    assert len(errors) == 0
    assert_html_is_equal(html, expected)


@pytest.mark.render_params(
    xml="""
        <!-- Comment outside of root element. -->
        <div xmlns:qpy="http://questionpy.org/ns/question">
            <element qpy:attribute="value">Content</element>
            <!-- Comment. -->
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
    assert len(errors) == 1  # Undefined attribute.
    assert_html_is_equal(html, expected)


@pytest.mark.ui_file("qpy-urls")
@pytest.mark.render_params(qpy_url_replacer=lambda match: "/".join(match.group(2, 3, 1)))
def test_should_replace_qpy_urls(renderer: QuestionUIRenderer) -> None:
    expected = """
        <div xmlns="http://www.w3.org/1999/xhtml">
            <link rel="stylesheet" href="foo/bar/static/style.css"/>
            <script src="foo/bar/static/script.js"></script>
            <img src="acme/example/static-private/some/nested/path/img.png"/>
            <p>acme/example/static/some/link</p>
            <p>acme/example/static-private/some/other/link</p>
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
        <div xmlns="http://www.w3.org/1999/xhtml">
            <span>&lt;qpy:format-float xmlns:qpy="http://questionpy.org/ns/question" xmlns="http://www.w3.org/1999/xhtml" thousands-separator="maybe" precision="invalid"&gt;Unknown value.&lt;/qpy:format-float&gt;</span>
            <fieldset>
                <label>Invalid shuffle format. 1. A</label>
                Invalid text placement.
            </fieldset>
            <div>Missing placeholder.</div>
            <div>Empty placeholder.</div>
            <div>Unknown attribute.</div>
            <input type="checkbox" name="duplicate" class="qpy-input"></input>
            <input type="radio" name="duplicate" class="qpy-input"></input>
            <span>Missing attribute value.</span>
        </div>
    """  # noqa: E501
    html, errors = renderer.render()

    expected_errors: list[tuple[type[BaseRenderError], int]] = [
        # Even though the syntax error occurs after all the other errors, it should be listed first.
        (XMLSyntaxError, 19),
        (InvalidAttributeValueError, 2),
        (UnknownElementError, 3),
        (InvalidAttributeValueError, 4),
        (ConversionError, 5),
        (ConversionError, 5),
        (InvalidAttributeValueError, 5),
        (InvalidContentError, 6),
        (InvalidAttributeValueError, 9),
        (InvalidCleanOptionError, 13),
        (PlaceholderReferenceError, 13),
        (PlaceholderReferenceError, 14),
        (ExpectedAncestorError, 15),
        (UnknownAttributeError, 16),
        (DuplicateNameError, 18),
    ]

    assert len(errors) == len(expected_errors)

    for actual_error, expected_error in zip(errors, expected_errors, strict=True):
        error_type, line = expected_error
        assert isinstance(actual_error, error_type)
        assert actual_error.line == line

    assert_html_is_equal(html, expected)
