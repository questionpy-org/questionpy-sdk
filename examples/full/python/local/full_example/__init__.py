from questionpy import Package, QuestionTypeWrapper

from .question_type import ExampleQuestion


def init(package: Package) -> QuestionTypeWrapper:
    return QuestionTypeWrapper(ExampleQuestion, package)
