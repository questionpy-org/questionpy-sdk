#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from typing import TYPE_CHECKING, Any, Generic, TypeVar

from aiohttp import web
from pydantic import BaseModel

from questionpy_sdk.webserver.constants import REQUEST_CONTROLLER_KEY

if TYPE_CHECKING:
    from questionpy_sdk.webserver.controllers.base import BaseController

CT = TypeVar("CT", bound="BaseController")


class BaseView(web.View, Generic[CT]):
    controller_class: type[CT]

    @property
    def controller(self) -> CT:
        try:
            return self.request[REQUEST_CONTROLLER_KEY]
        except KeyError as err:
            msg = "Controller not injected"
            raise RuntimeError(msg) from err

    def json_model_response(self, model: BaseModel, **kwargs: Any) -> web.Response:
        """Create JSON response from model using Pydantic's serializer."""
        return web.json_response(text=model.model_dump_json(**kwargs))
