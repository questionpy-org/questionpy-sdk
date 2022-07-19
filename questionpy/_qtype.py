from abc import ABC, abstractmethod
from typing import Any, Optional, Type

from questionpy._manifest import Manifest
from questionpy.form import Form


class QuestionType(ABC):
    implementation: Optional[Type["QuestionType"]] = None

    def __init__(self, manifest: Manifest):
        self.manifest = manifest

    def __init_subclass__(cls, **kwargs: Any) -> None:
        QuestionType.implementation = cls

    @abstractmethod
    def render_edit_form(self) -> Form:
        pass

    def validate_options(self, options: Any) -> Any:
        return options
