#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from questionpy import make_question_type_init

from .question_type import SinglechoiceQuestion

init = make_question_type_init(SinglechoiceQuestion)
