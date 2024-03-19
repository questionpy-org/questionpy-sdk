#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import random
from typing import Any, Optional

from lxml import etree
from lxml.html.clean import Cleaner
from pydantic import BaseModel


def assert_element_list(query: Any) -> list[etree._Element]:
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
        raise TypeError("XPath query result is not a list.")

    return query


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


def int_to_letter(index: int) -> str:
    """Converts an integer to its corresponding letter (1 -> a, 2 -> b, etc.)."""
    return chr(ord('a') + index - 1)


def int_to_roman(index: int) -> str:
    """Converts an integer to its Roman numeral representation. Simplified version."""
    val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4,
        1
    ]
    syb = [
        "M", "CM", "D", "CD",
        "C", "XC", "L", "XL",
        "X", "IX", "V", "IV",
        "I"
    ]
    roman_num = ''
    i = 0
    while index > 0:
        for _ in range(index // val[i]):
            roman_num += syb[i]
            index -= val[i]
        i += 1
    return roman_num


def replace_shuffled_indices(element: etree._Element, index: int) -> None:
    for index_element in assert_element_list(element.xpath(".//qpy:shuffled-index",
                                                           namespaces={'qpy': QuestionUIRenderer.QPY_NAMESPACE})):
        format_style = index_element.get("format", "123")

        if format_style == "123":
            index_str = str(index)
        elif format_style == "abc":
            index_str = int_to_letter(index).lower()
        elif format_style == "ABC":
            index_str = int_to_letter(index).upper()
        elif format_style == "iii":
            index_str = int_to_roman(index).lower()
        elif format_style == "III":
            index_str = int_to_roman(index).upper()
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


class QuestionUIRenderer:
    XHTML_NAMESPACE: str = "http://www.w3.org/1999/xhtml"
    QPY_NAMESPACE: str = "http://questionpy.org/ns/question"
    question: etree._Element
    placeholders: dict[str, str]

    def __init__(self, xml: str, placeholders: dict[str, str], seed: Optional[int] = None) -> None:
        self.seed = seed
        self.xml = xml
        self.placeholders = placeholders
        self.question = etree.fromstring(xml.encode())

    def get_metadata(self) -> QuestionMetadata:
        """Extracts metadata from the question UI."""
        question_metadata = QuestionMetadata()
        namespaces: dict[str, str] = {'xhtml': self.XHTML_NAMESPACE, 'qpy': self.QPY_NAMESPACE}

        # Extract correct responses
        for element in self.question.findall(".//qpy:formulation//*[@qpy:correct-response]",
                                             namespaces=namespaces):
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
        for element_type in ['input', 'select', 'textarea', 'button']:
            for element in self.question.findall(f".//qpy:formulation//xhtml:{element_type}",
                                                 namespaces=namespaces):
                name = element.get("name")
                if not name:
                    continue

                question_metadata.expected_data[name] = "Any"
                if element.get("required") is not None:
                    question_metadata.required_fields.append(name)

        return question_metadata

    def render_general_feedback(self, attempt: Optional[dict] = None,
                                options: Optional[QuestionDisplayOptions] = None) -> Optional[str]:
        """Renders the contents of the `qpy:general-feedback` element or returns `None` if there is none."""
        try:
            elements = assert_element_list(
                self.question.xpath(".//qpy:general-feedback", namespaces={'qpy': self.QPY_NAMESPACE}))
        except TypeError:
            return None

        if not elements:
            return None

        return self.render_part(elements[0], attempt, options)

    def render_specific_feedback(self, attempt: Optional[dict] = None,
                                 options: Optional[QuestionDisplayOptions] = None) -> Optional[str]:
        """Renders the contents of the `qpy:specific-feedback` element or returns `None` if there is none."""
        try:
            elements = assert_element_list(
                self.question.xpath(".//qpy:specific-feedback", namespaces={'qpy': self.QPY_NAMESPACE}))
        except TypeError:
            return None

        if not elements:
            return None

        return self.render_part(elements[0], attempt, options)

    def render_right_answer(self, attempt: Optional[dict] = None,
                            options: Optional[QuestionDisplayOptions] = None) -> Optional[str]:
        """Renders the contents of the `qpy:right-answer` element or returns `None` if there is none."""
        try:
            elements = assert_element_list(
                self.question.xpath(".//qpy:right-answer", namespaces={'qpy': self.QPY_NAMESPACE}))
        except TypeError:
            return None

        if not elements:
            return None

        return self.render_part(elements[0], attempt, options)

    def render_formulation(self, attempt: Optional[dict] = None,
                           options: Optional[QuestionDisplayOptions] = None) -> str:
        """Renders the contents of the `qpy:formulation` element. Raises an exception if there is none.

        Raises:
            FormulationElementMissingError
        """
        formulations = self.question.findall(f".//{{{self.QPY_NAMESPACE}}}formulation")

        if not formulations:
            raise FormulationElementMissingError("Question UI XML contains no 'qpy:formulation' element")

        return self.render_part(formulations[0], attempt, options)

    def render_part(self, part: etree._Element, attempt: Optional[dict] = None,
                    options: Optional[QuestionDisplayOptions] = None) -> str:
        """Applies transformations to the descendants of a given node and returns the resulting HTML."""
        newdoc = etree.ElementTree(etree.Element("div", nsmap={None: self.XHTML_NAMESPACE}))  # type: ignore
        div = newdoc.getroot()

        for child in part:
            div.append(child)

        xpath = etree.XPathDocumentEvaluator(newdoc)
        xpath.register_namespace("xhtml", self.XHTML_NAMESPACE)
        xpath.register_namespace("qpy", self.QPY_NAMESPACE)

        self.resolve_placeholders(xpath)
        self.hide_unwanted_feedback(xpath, options)
        self.hide_if_role(xpath, options)
        self.set_input_values_and_readonly(xpath, attempt, options)
        self.soften_validation(xpath)
        self.defuse_buttons(xpath)
        self.shuffle_contents(xpath)
        self.add_styles(xpath)
        self.format_floats(xpath)
        # TODO: mangle_ids_and_names
        self.clean_up(xpath)

        return etree.tostring(newdoc, pretty_print=True).decode()

    def resolve_placeholders(self, xpath: etree.XPathDocumentEvaluator) -> None:
        """Replace placeholder PIs such as `<?p my_key plain?>` with the appropriate value from `self.placeholders`.

        Since QPy transformations should not be applied to the content of the placeholders, this method should be called
        last.
        """
        for p_instruction in assert_element_list(xpath("//processing-instruction('p')")):
            if not p_instruction.text:
                continue
            parts = p_instruction.text.strip().split()
            key = parts[0]
            clean_option = parts[1] if len(parts) > 1 else "clean"

            parent = p_instruction.getparent()
            if parent is None:
                continue

            if key not in self.placeholders:
                parent.remove(p_instruction)
                continue

            raw_value = self.placeholders[key]

            if clean_option.lower() not in ["clean", "noclean"]:
                assert clean_option.lower() == "plain"
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

    def hide_unwanted_feedback(self, xpath: etree.XPathDocumentEvaluator,
                               options: Optional[QuestionDisplayOptions] = None) -> None:
        """Hides elements marked with `qpy:feedback` if the type of feedback is disabled in ``options``"""
        if not options:
            return

        for element in assert_element_list(xpath("//*[@qpy:feedback]")):
            feedback_type = element.get(f"{{{self.QPY_NAMESPACE}}}feedback")

            # Check conditions to remove the element
            if ((feedback_type == "general" and not options.general_feedback) or (
                    feedback_type == "specific" and not options.feedback)):
                parent = element.getparent()
                if parent is not None:
                    parent.remove(element)

    def hide_if_role(self, xpath: etree.XPathDocumentEvaluator, options: Optional[QuestionDisplayOptions] = None) \
            -> None:
        """Removes elements with `qpy:if-role` attributes if the user matches none of the given roles in this
        context."""
        if not options or options.context.get('role') == 'admin':
            return

        for element in assert_element_list(xpath("//*[@qpy:if-role]")):
            attr = element.attrib.get(f'{{{self.QPY_NAMESPACE}}}if-role')
            if attr is None:
                continue
            allowed_roles = attr.split()

            if options.context.get('role') not in allowed_roles:
                parent = element.getparent()
                if parent is not None:
                    parent.remove(element)

    def set_input_values_and_readonly(self, xpath: etree.XPathDocumentEvaluator, attempt: Optional[dict],
                                      options: Optional[QuestionDisplayOptions] = None) -> None:
        """Transforms input(-like) elements.

        - If ``options`` is set, the input is disabled.
        - If a value was saved for the input in a previous step, the latest value is added to the HTML.

        Requires the unmangled name of the element, so must be called `before` ``mangle_ids_and_names``
        """
        for element in assert_element_list(xpath("//xhtml:button | //xhtml:input | //xhtml:select | //xhtml:textarea")):
            # Disable the element if options specify readonly
            if options and options.readonly:
                element.set("disabled", "disabled")

            name = element.get("name")
            if not name:
                continue

            if element.tag.endswith("}input"):
                type_attr = element.get("type", "text")
            else:
                local_name = str(etree.QName(element).localname)  # Extract the local name
                type_attr = local_name.rsplit('}', maxsplit=1)[-1]

            if not attempt:
                continue

            last_value = attempt.get(name)
            if last_value is not None:
                if type_attr in ["checkbox", "radio"]:
                    if element.get("value") == last_value:
                        element.set("checked", "checked")
                elif type_attr == "select":
                    # Iterate over child <option> elements to set 'selected' attribute
                    for option in assert_element_list(xpath(f".//xhtml:option[parent::xhtml:select[@name='{name}']]")):
                        opt_value = option.get("value") if option.get("value") is not None else option.text
                        if opt_value == last_value:
                            option.set("selected", "selected")
                            break
                elif type_attr not in ["button", "submit", "hidden"]:
                    element.set("value", last_value)

    def soften_validation(self, xpath: etree.XPathDocumentEvaluator) -> None:
        """Replaces the HTML attributes `pattern`, `required`, `minlength`, `maxlength`, `min, `max` so that submission
        is not prevented.

        The standard attributes are replaced with `data-qpy_X`, which are then evaluated in JS.
        """
        # Handle 'pattern' attribute for <input> elements
        for element in assert_element_list(xpath(".//xhtml:input[@pattern]")):
            pattern = element.get("pattern")
            element.attrib.pop("pattern")  # Remove the attribute
            if pattern:
                element.set("data-qpy_pattern", pattern)

        # Handle 'required' attribute for <input>, <select>, <textarea> elements
        for element in assert_element_list(xpath("(.//xhtml:input | .//xhtml:select | .//xhtml:textarea)[@required]")):
            element.attrib.pop("required")
            element.set("data-qpy_required", "true")
            element.set("aria-required", "true")

        # Handle 'minlength' attribute for <input>, <textarea> elements
        for element in assert_element_list(xpath("(.//xhtml:input | .//xhtml:textarea)[@minlength]")):
            minlength = element.get("minlength")
            element.attrib.pop("minlength")  # Remove the attribute
            if minlength:
                element.set("data-qpy_minlength", minlength)

        # Handle 'maxlength' attribute for <input>, <textarea> elements
        for element in assert_element_list(xpath("(.//xhtml:input | .//xhtml:textarea)[@maxlength]")):
            maxlength = element.get("maxlength")
            element.attrib.pop("maxlength")
            if maxlength:
                element.set("data-qpy_maxlength", maxlength)

        # Handle 'min' attribute for <input> elements
        for element in assert_element_list(xpath(".//xhtml:input[@min]")):
            min_value = element.get("min")
            element.attrib.pop("min")
            if min_value:
                element.set("data-qpy_min", min_value)
                element.set("aria-valuemin", min_value)

        # Handle 'max' attribute for <input> elements
        for element in assert_element_list(xpath(".//xhtml:input[@max]")):
            max_value = element.get("max")
            element.attrib.pop("max")
            if max_value:
                element.set("data-qpy_max", max_value)
                element.set("aria-valuemax", max_value)

    def defuse_buttons(self, xpath: etree.XPathDocumentEvaluator) -> None:
        """Turns submit and reset buttons into simple buttons without a default action."""
        for element in assert_element_list(
                xpath("(//xhtml:input | //xhtml:button)[@type = 'submit' or @type = 'reset']")):
            element.set("type", "button")

    def shuffle_contents(self, xpath: etree.XPathDocumentEvaluator) -> None:
        """Shuffles children of elements marked with `qpy:shuffle-contents`.

        Also replaces `qpy:shuffled-index` elements which are descendants of each child with the new index of the child.
        """
        if self.seed:
            random.seed(self.seed)

        for element in assert_element_list(xpath("//*[@qpy:shuffle-contents]")):
            # Collect child elements to shuffle them
            child_elements = [
                child for child in element if isinstance(child, etree._Element)  # pylint: disable=protected-access
            ]
            random.shuffle(child_elements)

            element.attrib.pop("{%s}shuffle-contents" % self.QPY_NAMESPACE)

            # Reinsert shuffled elements, preserving non-element nodes
            for i, child in enumerate(child_elements):
                replace_shuffled_indices(child, i + 1)
                # Move each child element back to its parent at the correct position
                element.append(child)

    def clean_up(self, xpath: etree.XPathDocumentEvaluator) -> None:
        """Removes remaining QuestionPy elements and attributes as well as comments and xmlns declarations."""
        for element in assert_element_list(xpath("//qpy:*")):
            parent = element.getparent()
            if parent is not None:
                parent.remove(element)

        # Remove attributes in the QuestionPy namespace
        for element in assert_element_list(xpath("//*")):
            qpy_attributes = [attr for attr in element.attrib.keys() if
                              attr.startswith(f'{{{self.QPY_NAMESPACE}}}')]  # type: ignore[arg-type]
            for attr in qpy_attributes:
                del element.attrib[attr]

        # Remove comments
        for comment in assert_element_list(xpath("//comment()")):
            parent = comment.getparent()
            if parent is not None:
                parent.remove(comment)

        # Remove the 'qpy' namespace URI from the element
        for element in assert_element_list(xpath("//*")):
            if element.tag.startswith('{'):
                element.tag = etree.QName(element).localname
            for name_space in list(element.nsmap.keys()):
                if name_space is not None and name_space == 'qpy':
                    etree.cleanup_namespaces(element, keep_ns_prefixes=['xml'])

    def add_class_names(self, element: etree._Element, *class_names: str) -> None:
        """Adds the given class names to the elements `class` attribute if not already present."""
        existing_classes = element.get('class', '').split()
        for class_name in class_names:
            if class_name not in existing_classes:
                existing_classes.append(class_name)
        element.set('class', ' '.join(existing_classes))

    def add_styles(self, xpath: etree.XPathDocumentEvaluator) -> None:
        """Adds CSS classes to various elements."""
        # First group: input (not checkbox, radio, button, submit, reset), select, textarea
        for element in assert_element_list(xpath("""
                //xhtml:input[@type != 'checkbox' and @type != 'radio' and
                              @type != 'button' and @type != 'submit' and @type != 'reset']
                | //xhtml:select | //xhtml:textarea
                """)):
            self.add_class_names(element, "form-control", "qpy-input")

        # Second group: input (button, submit, reset), button
        for element in assert_element_list(xpath("""
                //xhtml:input[@type = 'button' or @type = 'submit' or @type = 'reset']
                | //xhtml:button
                """)):
            self.add_class_names(element, "btn", "btn-primary", "qpy-input")

        # Third group: input (checkbox, radio)
        for element in assert_element_list(xpath("//xhtml:input[@type = 'checkbox' or @type = 'radio']")):
            self.add_class_names(element, "qpy-input")

    def format_floats(self, xpath: etree.XPathDocumentEvaluator) -> None:
        """Handles `qpy:format-float`.

        Uses `format_float` and optionally adds thousands separators.
        """
        thousands_sep = ","  # Placeholder for thousands separator
        decimal_sep = "."  # Placeholder for decimal separator

        for element in assert_element_list(xpath("//qpy:format-float")):
            if element.text is None:
                continue
            float_val = float(element.text)

            precision = int(element.get("precision", -1))
            strip_zeroes = "strip-zeros" in element.attrib

            if precision >= 0:
                formatted_str = f"{float_val:.{precision}f}"
            else:
                formatted_str = str(float_val)

            if strip_zeroes:
                formatted_str = formatted_str.rstrip('0').rstrip(decimal_sep) if '.' in formatted_str else formatted_str

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


class FormulationElementMissingError(Exception):
    """Exception raised when a 'qpy:formulation' element is missing from the XML."""
