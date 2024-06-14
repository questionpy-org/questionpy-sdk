#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from functools import cached_property
from random import Random
from typing import Any

from lxml import etree
from lxml.html.clean import Cleaner
from pydantic import BaseModel


def _assert_element_list(query: Any) -> list[etree._Element]:
    """Checks if the XPath query result is a list of Elements.

    - If it is, returns the list.
    - Otherwise, raises an error.

    Args:
        query: The result of an XPath query.

    Returns:
        list: The result of the XPath query.

    Raises:
        TypeError: If the result is not a list.
    """
    if not isinstance(query, list):
        msg = "XPath query result is not a list."
        raise TypeError(msg)

    return query


def _set_element_value(element: etree._Element, value: str, name: str, xpath: etree.XPathDocumentEvaluator) -> None:
    """Sets value on user input element.

    Args:
        element: XHTML element to set value on.
        value: Value to set.
        name: Element name.
        xpath: XPath evaluator.
    """
    type_attr = element.get("type", "text") if element.tag.endswith("}input") else etree.QName(element).localname

    if type_attr in {"checkbox", "radio"}:
        if element.get("value") == value:
            element.set("checked", "checked")
    elif type_attr == "select":
        # Iterate over child <option> elements to set 'selected' attribute
        for option in _assert_element_list(xpath(f".//xhtml:option[parent::xhtml:select[@name='{name}']]")):
            opt_value = option.get("value") if option.get("value") is not None else option.text
            if opt_value == value:
                option.set("selected", "selected")
                break
    elif type_attr == "textarea":
        element.text = value
    elif type_attr not in {"button", "submit", "hidden"}:
        element.set("value", value)


def _replace_shuffled_indices(element: etree._Element, index: int) -> None:
    for index_element in _assert_element_list(
        element.xpath(".//qpy:shuffled-index", namespaces={"qpy": QuestionUIRenderer.QPY_NAMESPACE})
    ):
        format_style = index_element.get("format", "123")

        if format_style == "123":
            index_str = str(index)
        elif format_style == "abc":
            index_str = _int_to_letter(index).lower()
        elif format_style == "ABC":
            index_str = _int_to_letter(index).upper()
        elif format_style == "iii":
            index_str = _int_to_roman(index).lower()
        elif format_style == "III":
            index_str = _int_to_roman(index).upper()
        else:
            index_str = str(index)

        # Replace the index element with the new index string
        new_text_node = etree.Element("span")  # Using span to replace the custom element
        new_text_node.text = index_str

        if index_element.tail:
            new_text_node.tail = index_element.tail

        parent = index_element.getparent()
        if parent is not None:
            parent.replace(index_element, new_text_node)


def _int_to_letter(index: int) -> str:
    """Converts an integer to its corresponding letter (1 -> a, 2 -> b, etc.)."""
    return chr(ord("a") + index - 1)


def _int_to_roman(index: int) -> str:
    """Converts an integer to its Roman numeral representation. Simplified version."""
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syb = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    roman_num = ""
    i = 0
    while index > 0:
        for _ in range(index // val[i]):
            roman_num += syb[i]
            index -= val[i]
        i += 1
    return roman_num


class QuestionMetadata:
    def __init__(self) -> None:
        self.correct_response: dict[str, str] = {}
        self.expected_data: dict[str, str] = {}
        self.required_fields: list[str] = []


class QuestionDisplayOptions(BaseModel):
    general_feedback: bool = True
    feedback: bool = True
    right_answer: bool = True
    context: dict = {}
    readonly: bool = False


class QuestionUIRenderer:
    XHTML_NAMESPACE: str = "http://www.w3.org/1999/xhtml"
    QPY_NAMESPACE: str = "http://questionpy.org/ns/question"

    def __init__(
        self,
        xml: str,
        placeholders: dict[str, str],
        options: QuestionDisplayOptions,
        seed: int | None = None,
        attempt: dict | None = None,
    ) -> None:
        """General renderer for the question UI except for the formulation part."""
        self._xml = etree.ElementTree(etree.fromstring(xml))
        self._xpath = etree.XPathDocumentEvaluator(self._xml)
        self._xpath.register_namespace("xhtml", self.XHTML_NAMESPACE)
        self._xpath.register_namespace("qpy", self.QPY_NAMESPACE)
        self._placeholders = placeholders
        self._options = options
        self._random = Random(seed)
        self._attempt = attempt

    @cached_property
    def xml(self) -> str:
        self._render()
        return etree.tostring(self._xml, pretty_print=True).decode()

    def _render(self) -> None:
        """Applies transformations to the xml."""
        self._resolve_placeholders()
        self._hide_unwanted_feedback()
        self._hide_if_role()
        self._set_input_values_and_readonly()
        self._soften_validation()
        self._defuse_buttons()
        self._shuffle_contents()
        self._add_styles()
        self._format_floats()
        # TODO: mangle_ids_and_names
        self._clean_up()

    def _resolve_placeholders(self) -> None:
        """Replace placeholder PIs such as `<?p my_key plain?>` with the appropriate value from `self.placeholders`.

        Since QPy transformations should not be applied to the content of the placeholders, this method should be called
        last.
        """
        for p_instruction in _assert_element_list(self._xpath("//processing-instruction('p')")):
            if not p_instruction.text:
                continue
            parts = p_instruction.text.strip().split()
            key = parts[0]
            clean_option = parts[1] if len(parts) > 1 else "clean"

            parent = p_instruction.getparent()
            if parent is None:
                continue

            if key not in self._placeholders:
                parent.remove(p_instruction)
                continue

            raw_value = self._placeholders[key]

            if clean_option.lower() not in {"clean", "noclean"}:
                if clean_option.lower() != "plain":
                    msg = f"clean_option expected to have value 'plain', found '{clean_option}' instead"
                    raise ValueError(msg)
                # Treat the value as plain text
                root = etree.Element("string")
                root.text = etree.CDATA(raw_value)
                parent.replace(p_instruction, root)
                continue

            if clean_option.lower() == "clean":
                cleaner = Cleaner()
                cleaned_value = etree.fromstring(cleaner.clean_html(raw_value))
                # clean_html wraps the result in <p> or <div>
                # Remove the wrapping from clean_html
                content = ""
                if cleaned_value.text:
                    content += cleaned_value.text
                for child in cleaned_value:
                    content += etree.tostring(child, encoding="unicode", with_tail=True)
                replacement = content
            else:
                replacement = raw_value

            p_instruction.addnext(etree.fromstring(f"<string>{replacement}</string>"))
            parent.remove(p_instruction)

    def _hide_unwanted_feedback(self) -> None:
        """Hides elements marked with `qpy:feedback` if the type of feedback is disabled in `options`."""
        for element in _assert_element_list(self._xpath("//*[@qpy:feedback]")):
            feedback_type = element.get(f"{{{self.QPY_NAMESPACE}}}feedback")

            # Check conditions to remove the element
            if (feedback_type == "general" and not self._options.general_feedback) or (
                feedback_type == "specific" and not self._options.feedback
            ):
                parent = element.getparent()
                if parent is not None:
                    parent.remove(element)

    def _hide_if_role(self) -> None:
        """Hides elements based on user role.

        Removes elements with `qpy:if-role` attributes if the user matches none of the given roles in this context.
        """
        if self._options.context.get("role") == "admin":
            return

        for element in _assert_element_list(self._xpath("//*[@qpy:if-role]")):
            attr = element.attrib.get(f"{{{self.QPY_NAMESPACE}}}if-role")
            if attr is None:
                continue
            allowed_roles = attr.split()

            if self._options.context.get("role") not in allowed_roles:
                parent = element.getparent()
                if parent is not None:
                    parent.remove(element)

    def _set_input_values_and_readonly(self) -> None:
        """Transforms input(-like) elements.

        - If `options` is set, the input is disabled.
        - If a value was saved for the input in a previous step, the latest value is added to the HTML.

        Requires the unmangled name of the element, so must be called `before` `mangle_ids_and_names`
        """
        elements = _assert_element_list(
            self._xpath("//xhtml:button | //xhtml:input | //xhtml:select | //xhtml:textarea")
        )

        for element in elements:
            # Disable the element if options specify readonly
            if self._options.readonly:
                element.set("disabled", "disabled")

            name = element.get("name")
            if not name or not self._attempt:
                continue

            last_value = self._attempt.get(name)
            if last_value is not None:
                _set_element_value(element, last_value, name, self._xpath)

    def _soften_validation(self) -> None:
        """Replaces HTML attributes so that submission is not prevented.

        Removes attributes `pattern`, `required`, `minlength`, `maxlength`, `min`, `max` from elements, so form
        submission is not affected. The standard attributes are replaced with `data-qpy_X`, which are then evaluated in
        JavaScript.
        """

        def handle_attribute(
            elements: list[str], attribute: str, data_attribute: str, aria_attribute: str | None = None
        ) -> None:
            xhtml_elems = " | ".join(f".//xhtml:{elem}" for elem in elements)
            element_list = _assert_element_list(self._xpath(f"({xhtml_elems})[@{attribute}]"))
            for element in element_list:
                value = element.get(attribute)
                element.attrib.pop(attribute)
                if value:
                    value = "true" if value == attribute else value
                    element.set(data_attribute, value)
                    if aria_attribute:
                        element.set(aria_attribute, value)

        # 'pattern' attribute for <input> elements
        handle_attribute(["input"], "pattern", "data-qpy_pattern")

        # 'required' attribute for <input>, <select>, <textarea> elements
        handle_attribute(["input", "select", "textarea"], "required", "data-qpy_required", "aria-required")

        # 'minlength'/'maxlength' attribute for <input>, <textarea> elements
        handle_attribute(["input", "textarea"], "minlength", "data-qpy_minlength")
        handle_attribute(["input", "textarea"], "maxlength", "data-qpy_maxlength")

        # 'min'/'max' attributes for <input> elements
        handle_attribute(["input"], "min", "data-qpy_min", "aria-valuemin")
        handle_attribute(["input"], "max", "data-qpy_max", "aria-valuemax")

    def _defuse_buttons(self) -> None:
        """Turns submit and reset buttons into simple buttons without a default action."""
        for element in _assert_element_list(
            self._xpath("(//xhtml:input | //xhtml:button)[@type = 'submit' or @type = 'reset']")
        ):
            element.set("type", "button")

    def _shuffle_contents(self) -> None:
        """Shuffles children of elements marked with `qpy:shuffle-contents`.

        Also replaces `qpy:shuffled-index` elements which are descendants of each child with the new index of the child.
        """
        for element in _assert_element_list(self._xpath("//*[@qpy:shuffle-contents]")):
            # Collect child elements to shuffle them
            child_elements = [child for child in element if isinstance(child, etree._Element)]
            self._random.shuffle(child_elements)

            element.attrib.pop("{%s}shuffle-contents" % self.QPY_NAMESPACE)

            # Reinsert shuffled elements, preserving non-element nodes
            for i, child in enumerate(child_elements):
                _replace_shuffled_indices(child, i + 1)
                # Move each child element back to its parent at the correct position
                element.append(child)

    def _clean_up(self) -> None:
        """Removes remaining QuestionPy elements and attributes as well as comments and xmlns declarations."""
        for element in _assert_element_list(self._xpath("//qpy:*")):
            parent = element.getparent()
            if parent is not None:
                parent.remove(element)

        # Remove attributes in the QuestionPy namespace
        for element in _assert_element_list(self._xpath("//*")):
            qpy_attributes = [attr for attr in element.attrib if attr.startswith(f"{{{self.QPY_NAMESPACE}}}")]  # type: ignore[arg-type]
            for attr in qpy_attributes:
                del element.attrib[attr]

        # Remove comments
        for comment in _assert_element_list(self._xpath("//comment()")):
            parent = comment.getparent()
            if parent is not None:
                parent.remove(comment)

        # Remove namespaces from all elements. (QPy elements should all have been consumed previously anyhow.)
        for element in _assert_element_list(self._xpath("//*")):
            qname = etree.QName(element)
            if qname.namespace == self.XHTML_NAMESPACE:
                element.tag = qname.localname

        etree.cleanup_namespaces(self._xml, top_nsmap={None: self.XHTML_NAMESPACE})  # type: ignore[dict-item]

    def _add_class_names(self, element: etree._Element, *class_names: str) -> None:
        """Adds the given class names to the elements `class` attribute if not already present."""
        existing_classes = element.get("class", "").split()
        for class_name in class_names:
            if class_name not in existing_classes:
                existing_classes.append(class_name)
        element.set("class", " ".join(existing_classes))

    def _add_styles(self) -> None:
        """Adds CSS classes to various elements."""
        # First group: input (not checkbox, radio, button, submit, reset), select, textarea
        for element in _assert_element_list(
            self._xpath("""
                //xhtml:input[@type != 'checkbox' and @type != 'radio' and
                              @type != 'button' and @type != 'submit' and @type != 'reset']
                | //xhtml:select | //xhtml:textarea
                """)
        ):
            self._add_class_names(element, "form-control", "qpy-input")

        # Second group: input (button, submit, reset), button
        for element in _assert_element_list(
            self._xpath("""
                //xhtml:input[@type = 'button' or @type = 'submit' or @type = 'reset']
                | //xhtml:button
                """)
        ):
            self._add_class_names(element, "btn", "btn-primary", "qpy-input")

        # Third group: input (checkbox, radio)
        for element in _assert_element_list(self._xpath("//xhtml:input[@type = 'checkbox' or @type = 'radio']")):
            self._add_class_names(element, "qpy-input")

    def _format_floats(self) -> None:
        """Handles `qpy:format-float`.

        Uses `format_float` and optionally adds thousands separators.
        """
        thousands_sep = ","  # Placeholder for thousands separator
        decimal_sep = "."  # Placeholder for decimal separator

        for element in _assert_element_list(self._xpath("//qpy:format-float")):
            if element.text is None:
                continue
            float_val = float(element.text)

            precision = int(element.get("precision", -1))
            strip_zeroes = "strip-zeros" in element.attrib

            formatted_str = f"{float_val:.{precision}f}" if precision >= 0 else str(float_val)

            if strip_zeroes:
                formatted_str = formatted_str.rstrip("0").rstrip(decimal_sep) if "." in formatted_str else formatted_str

            thousands_sep_attr = element.get("thousands-separator", "no")
            if thousands_sep_attr == "yes":
                parts = formatted_str.split(decimal_sep)
                integral_part = parts[0]
                integral_part_with_sep = f"{int(integral_part):,}".replace(",", thousands_sep)

                if len(parts) > 1:
                    formatted_str = integral_part_with_sep + decimal_sep + parts[1]
                else:
                    formatted_str = integral_part_with_sep

            new_text = etree.Element("span")
            new_text.text = formatted_str
            parent = element.getparent()

            new_text.tail = element.tail
            if parent:
                parent.insert(parent.index(element), new_text)
                parent.remove(element)


class QuestionFormulationUIRenderer(QuestionUIRenderer):
    def __init__(
        self,
        xml: str,
        placeholders: dict[str, str],
        options: QuestionDisplayOptions,
        seed: int | None = None,
        attempt: dict | None = None,
    ) -> None:
        """Renderer for the formulation UI part that provides metadata."""
        super().__init__(xml, placeholders, options, seed, attempt)
        self.metadata = self._get_metadata()

    def _get_metadata(self) -> QuestionMetadata:
        """Extracts metadata from the question UI."""
        question_metadata = QuestionMetadata()
        namespaces: dict[str, str] = {"xhtml": self.XHTML_NAMESPACE, "qpy": self.QPY_NAMESPACE}

        # Extract correct responses
        for element in self._xml.findall(".//*[@qpy:correct-response]", namespaces=namespaces):
            name = element.get("name")
            if not name:
                continue

            if element.tag.endswith("input") and element.get("type") == "radio":
                value = element.get("value")
            else:
                value = element.get(f"{{{self.QPY_NAMESPACE}}}correct-response")

            if not value:
                continue

            question_metadata.correct_response[name] = value

        # Extract other metadata
        for element_type in ["input", "select", "textarea", "button"]:
            for element in self._xml.findall(f".//xhtml:{element_type}", namespaces=namespaces):
                name = element.get("name")
                if not name:
                    continue

                question_metadata.expected_data[name] = "Any"
                if element.get("required") is not None:
                    question_metadata.required_fields.append(name)

        return question_metadata
