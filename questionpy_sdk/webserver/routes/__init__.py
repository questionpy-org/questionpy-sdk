#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from .attempt import routes as attempt_routes
from .files import routes as files_routes
from .manifest import routes as manifest_routes
from .options import routes as options_routes

api_routes = (attempt_routes, manifest_routes, options_routes, files_routes)
