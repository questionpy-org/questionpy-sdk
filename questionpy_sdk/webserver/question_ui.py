#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
import random
from typing import List, Any, Optional

from lxml import etree
from lxml.html.clean import Cleaner
from pydantic import BaseModel


def is_iterable(query: Any) -> list:
    """Checks if the XPath query result is iterable.

    - If it is, returns the iterable.
    - Otherwise, raises an error.

    Args:
        query: The result of an XPath query.

    Returns:
        query: The iterable object.

    Raises:
        TypeError: If the result is not iterable.
    """
    if not isinstance(query, list):
        raise TypeError("XPath query result is not iterable.")

    return query


class QuestionMetadata:
    def __init__(self) -> None:
        self.correct_response: dict[str, str] = {}
        self.expected_data: dict[str, str] = {}
        self.required_fields: List[str] = []


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
    for index_element in is_iterable(element.xpath(".//qpy:shuffled-index",
                                                   namespaces={'qpy': "http://questionpy.org/ns/question"})):
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

        index_element.getparent().replace(index_element, new_text_node)


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
        """Extracts metadata from the question UI.

        Returns:
            QuestionMetadata: question_metadata
        """
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
            for element in self.question.findall(f".//qpy:formulation//{{{self.XHTML_NAMESPACE}}}{element_type}",
                                                 namespaces=namespaces):
                name = element.get("name")
                if not name:
                    continue

                question_metadata.expected_data[name] = "Any"
                if element.get("required") is not None:
                    question_metadata.required_fields.append(name)

        return question_metadata

    def render_general_feedback(self, attempt: Any = None, options: Optional[QuestionDisplayOptions] = None)\
            -> Optional[str]:
        try:
            elements = is_iterable(
                self.question.xpath(".//qpy:general-feedback", namespaces={'qpy': self.QPY_NAMESPACE}))
        except TypeError:
            return None
        return self.render_part(elements[0], attempt, options)

    def render_specific_feedback(self, attempt: Any = None, options: Optional[QuestionDisplayOptions] = None)\
            -> Optional[str]:
        try:
            elements = is_iterable(
                self.question.xpath(".//qpy:specific-feedback", namespaces={'qpy': self.QPY_NAMESPACE}))
        except TypeError:
            return None
        return self.render_part(elements[0], attempt, options)

    def render_right_answer(self, attempt: Any = None, options: Optional[QuestionDisplayOptions] = None) \
            -> Optional[str]:
        try:
            elements = is_iterable(
                self.question.xpath(".//qpy:right-answer", namespaces={'qpy': self.QPY_NAMESPACE}))
        except TypeError:
            return None
        return self.render_part(elements[0], attempt, options)

    def render_formulation(self, attempt: Any = None, options: Optional[QuestionDisplayOptions] = None) -> str:
        formulations = self.question.findall(f".//{{{self.QPY_NAMESPACE}}}formulation")

        if not formulations:
            raise FormulationElementMissingError("Question UI XML contains no 'qpy:formulation' element")

        return self.render_part(formulations[0], attempt, options)

    def render_part(self, part: etree._Element, attempt: Any = None, options: Optional[QuestionDisplayOptions] = None) \
            -> str:
        newdoc = etree.ElementTree(etree.Element("div", nsmap={None: self.XHTML_NAMESPACE}))  # type: ignore
        div = newdoc.getroot()

        # TODO: This only appends child nodes. Any text directly in the part is not copied but should be.
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

        Args:
            xpath: etree.XPathEvaluator

        Returns:
            None
        """
        for p_instruction in is_iterable(xpath("//processing-instruction('p')")):
            if not p_instruction.text:
                continue
            parts = p_instruction.text.strip().split()
            key = parts[0]
            clean_option = parts[1] if len(parts) > 1 else "clean"

            if key not in self.placeholders:
                p_instruction.getparent().remove(p_instruction)
                continue

            raw_value = self.placeholders[key]

            if clean_option.lower() not in ["clean", "noclean"]:
                assert clean_option.lower() == "plain"
                # Treat the value as plain text
                root = etree.Element("string")
                root.text = etree.CDATA(raw_value)
                p_instruction.getparent().replace(p_instruction, root)
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

            p_instruction.getparent().remove(p_instruction)

    def hide_unwanted_feedback(self, xpath: etree.XPathDocumentEvaluator,
                               options: Optional[QuestionDisplayOptions] = None) -> None:
        """Hides elements marked with `qpy:feedback` if the type of feedback is disabled in ``options``

        Args:
            xpath: etree.XPathEvaluator
            options: QuestionDisplayOptions

        Returns:
            None
        """
        if not options:
            return

        for element in is_iterable(xpath("//*[@qpy:feedback]")):
            feedback_type = element.get(f"{{{self.QPY_NAMESPACE}}}feedback")

            # Check conditions to remove the element
            if ((feedback_type == "general" and not options.general_feedback) or (
                    feedback_type == "specific" and not options.feedback)):
                element.getparent().remove(element)

    def hide_if_role(self, xpath: etree.XPathDocumentEvaluator, options: Optional[QuestionDisplayOptions] = None) \
            -> None:
        """Removes elements with `qpy:if-role` attributes if the user matches none of the given roles in this context.

        Args:
            xpath: etree.XPathEvaluator
            options: QuestionDisplayOptions
        """
        if not options or options.context.get('role') == 'admin':
            return

        for attr in is_iterable(xpath("//@qpy:if-role")):
            allowed_roles = attr.split()

            if options.context.get('role') not in allowed_roles:
                attr.getparent().getparent().remove(attr.getparent())

    def set_input_values_and_readonly(self, xpath: etree.XPathDocumentEvaluator, attempt: Any,
                                      options: Optional[QuestionDisplayOptions] = None) -> None:
        """Transforms input(-like) elements.

        - If ``options`` is set, the input is disabled.
        - If a value was saved for the input in a previous step, the latest value is added to the HTML.

        Requires the unmangled name of the element, so must be called `before` ``mangle_ids_and_names``

        Args:
            xpath: etree.XPathEvaluator
            attempt: Any
            options: QuestionDisplayOptions

        Returns:
            None
        """
        for element in is_iterable(xpath("//xhtml:button | //xhtml:input | //xhtml:select | //xhtml:textarea")):
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
                type_attr = local_name.split("}")[-1]

            if not attempt:
                continue

            # TODO: 'attempt' provides a method to get the last saved value for the element
            last_value = attempt.get_last_saved_value(name)

            if last_value is not None:
                if type_attr in ["checkbox", "radio"]:
                    if element.get("value") == last_value:
                        element.set("checked", "checked")
                elif type_attr == "select":
                    # Iterate over child <option> elements to set 'selected' attribute
                    for option in is_iterable(xpath(f".//xhtml:option[parent::xhtml:select[@name='{name}']]")):
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

        Args:
            xpath: etree.XPathEvaluator

        Returns:
            None
        """
        # Handle 'pattern' attribute for <input> elements
        for element in is_iterable(xpath(".//xhtml:input[@pattern]")):
            pattern = element.get("pattern")
            element.attrib.pop("pattern", None)  # Remove the attribute
            element.set("data-qpy_pattern", pattern)

        # Handle 'required' attribute for <input>, <select>, <textarea> elements
        for element in is_iterable(xpath("(.//xhtml:input | .//xhtml:select | .//xhtml:textarea)[@required]")):
            element.attrib.pop("required")
            element.set("data-qpy_required", "true")
            element.set("aria-required", "true")

        # Handle 'minlength' attribute for <input>, <textarea> elements
        for element in is_iterable(xpath("(.//xhtml:input | .//xhtml:textarea)[@minlength]")):
            minlength = element.get("minlength")
            element.attrib.pop("minlength")  # Remove the attribute
            element.set("data-qpy_minlength", minlength)

        # Handle 'maxlength' attribute for <input>, <textarea> elements
        for element in is_iterable(xpath("(.//xhtml:input | .//xhtml:textarea)[@maxlength]")):
            maxlength = element.get("maxlength")
            element.attrib.pop("maxlength")
            element.set("data-qpy_maxlength", maxlength)

        # Handle 'min' attribute for <input> elements
        for element in is_iterable(xpath(".//xhtml:input[@min]")):
            min_value = element.get("min")
            element.attrib.pop("min")
            element.set("data-qpy_min", min_value)
            element.set("aria-valuemin", min_value)

        # Handle 'max' attribute for <input> elements
        for element in is_iterable(xpath(".//xhtml:input[@max]")):
            max_value = element.get("max")
            element.attrib.pop("max")
            element.set("data-qpy_max", max_value)
            element.set("aria-valuemax", max_value)

    def defuse_buttons(self, xpath: etree.XPathDocumentEvaluator) -> None:
        """Turns submit and reset buttons into simple buttons without a default action.

        Args:
            xpath: etree.XPathEvaluator

        Returns:
            None
        """
        for element in is_iterable(xpath("(//xhtml:input | //xhtml:button)[@type = 'submit' or @type = 'reset']")):
            element.set("type", "button")

    def shuffle_contents(self, xpath: etree.XPathDocumentEvaluator) -> None:
        """Shuffles children of elements marked with `qpy:shuffle-contents`.

        Also replaces `qpy:shuffled-index` elements which are descendants of each child with the new index of the child.

        Args:
            xpath: etree.XPathEvaluator

        Returns:
            None
        """
        if self.seed:
            random.seed(self.seed)

        for element in is_iterable(xpath("//*[@qpy:shuffle-contents]")):
            # Collect child elements to shuffle them
            child_elements = [
                child for child in element if isinstance(child, etree._Element)
            ]  # pylint: disable=protected-access
            random.shuffle(child_elements)

            element.attrib.pop("{%s}shuffle-contents" % self.QPY_NAMESPACE)

            # Reinsert shuffled elements, preserving non-element nodes
            for i, child in enumerate(child_elements):
                replace_shuffled_indices(child, i + 1)
                # Move each child element back to its parent at the correct position
                element.append(child)

    def clean_up(self, xpath: etree.XPathDocumentEvaluator) -> None:
        """Removes remaining QuestionPy elements and attributes as well as comments and xmlns declarations.

        Args:
            xpath: etree.XPathEvaluator

        Returns:
            None
        """
        for element in is_iterable(xpath("//qpy:*")):
            element.getparent().remove(element)

        # Remove attributes in the QuestionPy namespace
        for element in is_iterable(xpath("//*")):
            qpy_attributes = [attr for attr in element.attrib.keys() if
                              attr.startswith('{http://questionpy.org/ns/question}')]
            for attr in qpy_attributes:
                del element.attrib[attr]

        # Remove comments
        for comment in is_iterable(xpath("//comment()")):
            comment.getparent().remove(comment)

        # Remove the 'qpy' namespace URI from the element
        for element in is_iterable(xpath("//*")):
            if element.tag.startswith('{'):
                element.tag = etree.QName(element).localname
            for name_space in list(element.nsmap.keys()):
                if name_space is not None and name_space == 'qpy':
                    etree.cleanup_namespaces(element, keep_ns_prefixes=['xml'])

    def add_class_names(self, element: etree._Element, *class_names: str) -> None:
        """Adds the given class names to the elements `class` attribute if not already present.

        Args:
            element: etree._Element
            *class_names: str

        Returns:

        """
        existing_classes = element.get('class', '').split()
        for class_name in class_names:
            if class_name not in existing_classes:
                existing_classes.append(class_name)
        element.set('class', ' '.join(existing_classes))

    def add_styles(self, xpath: etree.XPathDocumentEvaluator) -> None:
        """Adds CSS classes to various elements

        Args:
            xpath: etree.XPathEvaluator

        Returns:
            None
        """
        # First group: input (not checkbox, radio, button, submit, reset), select, textarea
        for element in is_iterable(xpath("""
                //xhtml:input[@type != 'checkbox' and @type != 'radio' and
                              @type != 'button' and @type != 'submit' and @type != 'reset']
                | //xhtml:select | //xhtml:textarea
                """)):
            self.add_class_names(element, "form-control", "qpy-input")

        # Second group: input (button, submit, reset), button
        for element in is_iterable(xpath("""
                //xhtml:input[@type = 'button' or @type = 'submit' or @type = 'reset']
                | //xhtml:button
                """)):
            self.add_class_names(element, "btn", "btn-primary", "qpy-input")

        # Third group: input (checkbox, radio)
        for element in is_iterable(xpath("//xhtml:input[@type = 'checkbox' or @type = 'radio']")):
            self.add_class_names(element, "qpy-input")

    def format_floats(self, xpath: etree.XPathDocumentEvaluator) -> None:
        thousands_sep = ","  # Placeholder for thousands separator
        decimal_sep = "."  # Placeholder for decimal separator

        for element in is_iterable(xpath("//qpy:format-float")):
            float_val = float(element.text)
            precision = int(element.get("precision", -1))
            strip_zeroes = "strip-zeros" in element.attrib

            if precision >= 0:
                formatted_str = f"{{:.{precision}f}}".format(float_val)
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

            assert isinstance(element, etree._Element)  # pylint: disable=protected-access
            parent.insert(parent.index(element), new_text)
            parent.remove(element)


class FormulationElementMissingError(Exception):
    """Exception raised when a 'qpy:formulation' element is missing from the XML."""
