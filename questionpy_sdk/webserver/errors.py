#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>


class MissingStateError(Exception):
    message: str

    def __init__(self) -> None:
        super().__init__(self.message)


class MissingQuestionStateError(MissingStateError):
    message = "The question state is missing."


class MissingAttemptStateError(MissingStateError):
    message = "The attempt state is missing."


class MissingAttemptSeedError(MissingStateError):
    message = "The attempt seed is missing."


class MissingAttemptScoreError(MissingStateError):
    message = "The attempt score is missing."


class MissingAttemptDataError(MissingStateError):
    message = "The attempt data is missing."
