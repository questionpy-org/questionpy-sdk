from abc import ABC
from typing import Any, Optional, Type, Generic, TypeVar, ClassVar, get_args, get_origin, cast

from questionpy_common.qtype import BaseQuestionType, OptionsFormDefinition

from questionpy.form import FormModel

F = TypeVar("F", bound=FormModel)


class QuestionType(BaseQuestionType, ABC, Generic[F]):
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
                else:
                    # QuestionType was used without parameters, default to an empty form model
                    cls.form_model = FormModel
                break

        QuestionType.implementation = cls

        super().__init_subclass__(**kwargs)

    def get_options_form_definition(self) -> OptionsFormDefinition:
        return cast(OptionsFormDefinition, self.form_model.form())

    def validate_options(self, options: Any) -> F:
        return cast(F, self.form_model.parse_obj(options))
