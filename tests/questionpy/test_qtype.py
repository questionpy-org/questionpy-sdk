from questionpy import BaseQuestionState, Question
from questionpy._qtype import QuestionStateWithVersion
from questionpy.form import FormModel
from tests.questionpy.test_attempt import MyAttempt


class MyQuestion(Question):
    attempt_class = MyAttempt

    # These are forward references, i.e. the types don't exist yet. get_mro_type_hint will support this, as long as it's
    # called after the types are defined, so it must be called after module execution. We test that we call
    # get_type_hints correctly.
    options: "MyFormModel"
    question_state: "MyQuestionState"


class MyFormModel(FormModel):
    pass


class MyQuestionState(BaseQuestionState):
    pass


def test_should_resolve_forward_references() -> None:
    assert MyQuestion.options_class is MyFormModel
    assert MyQuestion.question_state_class is MyQuestionState
    assert MyQuestion.question_state_with_version_class is QuestionStateWithVersion[MyFormModel, MyQuestionState]
