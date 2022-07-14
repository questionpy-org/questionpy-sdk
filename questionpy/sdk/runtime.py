import logging
import sys
from typing import Type

from questionpy.sdk.manifest import Manifest
from questionpy.sdk.model.form import Form
from questionpy.sdk.model.messages import PingMessage, PongMessage, RenderEditForm, ValidateOptionsMessage
from questionpy.sdk.qtype import QuestionType
from questionpy.sdk.server import QPyPackageServer

log = logging.getLogger(__name__)


def run_qtype(manifest: Manifest, qtype: Type[QuestionType], *, pretty: bool = False) -> None:
    qtype_instance = qtype(manifest=manifest)

    log.info("Running question type '%s:%s' with manifest '%s'",
             qtype.__module__, qtype.__name__, manifest)

    server = QPyPackageServer(sys.stdin, sys.stdout, pretty=pretty)
    for message in server:
        if isinstance(message, PingMessage):
            server.send(PongMessage())
        elif isinstance(message, RenderEditForm):
            form = Form()
            qtype_instance.render_edit_form(form)
            server.send(RenderEditForm.Response(form=form))
        elif isinstance(message, ValidateOptionsMessage):
            server.send(ValidateOptionsMessage.Response(state=qtype_instance.validate_options(message.options)))
        else:
            log.error("Unsupported message type: %s", type(message).__name__)
