#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from typing import List

import xml.etree.ElementTree as ETree


class QuestionMetadata:
    def __init__(self) -> None:
        self.correct_response: dict[str, str] = {}
        self.expected_data: dict[str, str] = {}
        self.required_fields: List[str] = []


class QuestionUIRenderer:
    XHTML_NAMESPACE: str = "http://www.w3.org/1999/xhtml"
    QPY_NAMESPACE: str = "http://questionpy.org/ns/question"

    def __init__(self, xml: str, placeholders: List[str]) -> None:
        self.xml = xml
        self.placeholders = placeholders

    def get_metadata(self) -> QuestionMetadata:
        """Extracts metadata from the question UI.

        Returns:
            QuestionMetadata: question_metadata
        """
        question_metadata = QuestionMetadata()
        namespaces: dict[str, str] = {'xhtml': self.XHTML_NAMESPACE, 'qpy': self.QPY_NAMESPACE}

        root = ETree.fromstring(self.xml)

        # Extract correct responses
        for element in root.findall(".//qpy:formulation//*[@qpy:correct-response]", namespaces=namespaces):
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
            for element in root.findall(f".//qpy:formulation//{{{self.XHTML_NAMESPACE}}}{element_type}",
                                        namespaces=namespaces):
                name = element.get("name")
                if not name:
                    continue

                question_metadata.expected_data[name] = "Any"
                if element.get("required") is not None:
                    question_metadata.required_fields.append(name)

        return question_metadata
