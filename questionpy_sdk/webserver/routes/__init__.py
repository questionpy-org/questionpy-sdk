#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from .attempt import routes as attempt_routes
from .file import routes as file_routes
from .manifest import routes as manifest_routes
from .question import routes as question_routes

api_routes = (attempt_routes, file_routes, manifest_routes, question_routes)
