from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type

from questionpy._manifest import Manifest
from questionpy.form import Form


class MissingOptionError(Exception):
    def __init__(self, name: str):
        super().__init__(f"Question option '{name}' was required but not provided")
        self.name = name


class QuestionType(ABC):
    implementation: Optional[Type["QuestionType"]] = None

    def __init__(self, manifest: Manifest):
        self.manifest = manifest

    def __init_subclass__(cls, **kwargs: Any) -> None:
        QuestionType.implementation = cls

    @abstractmethod
    def render_edit_form(self, form: Form) -> None:
        pass

    def validate_options(self, options: Dict[str, Any]) -> Dict[str, Any]:
        return options
