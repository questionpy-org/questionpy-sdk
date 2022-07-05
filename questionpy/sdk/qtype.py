import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

from questionpy.sdk.manifest import Manifest
from questionpy.sdk.model.form import Form

log = logging.getLogger(__name__)


class MissingOptionError(Exception):
    def __init__(self, name: str):
        self.name = name


class QuestionType(ABC):
    manifest: Manifest

    def __init__(self, manifest: Manifest):
        self.manifest = manifest

    @abstractmethod
    def render_edit_form(self, form: Form) -> None: ...

    def validate_options(self, options: Dict[str, Any]) -> Dict[str, Any]:
        return options
