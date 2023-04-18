import json
from typing import Any, Optional, Type, Generic, TypeVar, ClassVar, get_args, get_origin

from pydantic import BaseModel, ValidationError
from questionpy_common.qtype import OptionsFormDefinition, BaseQuestionType, BaseQuestion, OptionsFormValidationError

from questionpy.form import FormModel
from questionpy.form.validation import validate_form

F = TypeVar("F", bound=FormModel)


class Question(BaseQuestion, BaseModel):
    question_state: dict[str, object]


class QuestionType(BaseQuestionType, Generic[F]):
    form_model: ClassVar[Type[FormModel]]
    implementation: ClassVar[Optional[Type["QuestionType"]]] = None

    def __init_subclass__(cls, *args: Any, **kwargs: Any) -> None:
        # __orig_bases__ is only present when at least one base is a parametrized generic
        # See PEP 560 https://peps.python.org/pep-0560/
        if "__orig_bases__" in cls.__dict__:
            bases = cls.__dict__["__orig_bases__"]
        else:
            bases = cls.__bases__

        for base in bases:
            origin = get_origin(base) or base
            if issubclass(origin, QuestionType):
                args = get_args(base)
                if args:
                    # QuestionType[args] was used
                    if not isinstance(args[0], type) or not issubclass(args[0], FormModel):
                        raise TypeError(f"Type parameter '{args[0]!r}' of QuestionType is not a subclass of FormModel")
                    cls.form_model = args[0]
                    validate_form(cls.form_model.qpy_form)
                else:
                    # QuestionType was used without parameters, default to an empty form model
                    cls.form_model = FormModel
                break

        QuestionType.implementation = cls

        super().__init_subclass__(**kwargs)

    def get_options_form(self, question_state: Optional[dict[str, object]]) \
            -> tuple[OptionsFormDefinition, dict[str, object]]:
        return (
            self.form_model.qpy_form,
            question_state or {}
        )

    def create_question_from_options(self, old_state: Optional[dict[str, object]],
                                     form_data: dict[str, object]) -> BaseQuestion:
        try:
            parsed_form_data = self.form_model.parse_obj(form_data)
        except ValidationError as e:
            error_dict = {".".join(map(str, error["loc"])): error["msg"] for error in e.errors()}
            raise OptionsFormValidationError(error_dict) from e

        new_state = old_state.copy() if old_state else {}
        # In dict(), pydantic doesn't serialize non-BaseModel fields such as out OptionEnum.
        # So we do json() and loads() again. Looks like this is going to be fixed in pydantic v2:
        # https://github.com/pydantic/pydantic/issues/951
        new_state.update(json.loads(parsed_form_data.json()))

        return Question(question_state=new_state)

    def create_question_from_state(self, question_state: dict[str, object]) -> BaseQuestion:
        return Question(question_state=question_state)
