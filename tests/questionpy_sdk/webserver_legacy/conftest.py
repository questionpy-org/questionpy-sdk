#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from lxml import etree


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
