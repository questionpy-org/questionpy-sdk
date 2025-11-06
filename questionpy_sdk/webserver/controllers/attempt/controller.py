#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import contextlib
import logging
import random
import re
from collections.abc import Callable
from typing import Any

import jinja2
from pydantic import JsonValue
from yarl import URL

import questionpy_sdk.webserver.errors as webserver_errors
from questionpy import AttemptModel, AttemptScoredModel, ScoreModel
from questionpy_common.api.attempt import FeedbackType, JsModuleCall
from questionpy_sdk.webserver.constants import DEFAULT_REQUEST_INFO
from questionpy_sdk.webserver.controllers.base import BaseController
from questionpy_server.worker import Worker

from .data import AttemptData, AttemptRenderData, AttemptTemplateContext
from .errors import SectionErrorMap, log_render_errors
from .question_ui import QuestionDisplayOptions, QuestionFormulationUIRenderer, QuestionUIRenderer

_log = logging.getLogger(__name__)
_QPY_URL_PATTERN = re.compile(r"^qpy://static/([a-z_]\w{0,126})/([a-z_]\w{0,126})((?:/[\w\-@:%+.~=]+)+)$")


class AttemptController(BaseController):
    async def get_attempt(
        self, question_id: str, attempt_id: str, display_options: QuestionDisplayOptions
    ) -> AttemptRenderData:
        """Starts a new attempt or restores the previous attempt and renders the UI."""
        data: dict[str, JsonValue] | None = None
        state: str | None = None
        score: ScoreModel | None = None
        new_seed: bool = False

        with contextlib.suppress(webserver_errors.MissingAttemptDataError):
            data = await self._state_manager.read_attempt_data(question_id, attempt_id)
        with contextlib.suppress(webserver_errors.MissingAttemptStateError):
            state = await self._state_manager.read_attempt_state(question_id, attempt_id)
        with contextlib.suppress(webserver_errors.MissingAttemptScoreError):
            score = await self._state_manager.read_attempt_score(question_id, attempt_id)
        try:
            seed = await self._state_manager.read_attempt_seed(question_id, attempt_id)
        except webserver_errors.MissingAttemptSeedError:
            seed = random.randint(0, 1000)
            new_seed = True

        async with self.get_worker() as worker:
            attempt, state = await self._get_or_start_attempt(question_id, attempt_id, state, data, score, worker)
            renderer = _AttemptRenderer(attempt, display_options, self.generate_api_url, worker)
            render_data = await renderer.render_ui(data, state, score, seed)
            if new_seed:
                await self._state_manager.write_attempt_seed(question_id, attempt_id, seed)
            return render_data

    async def get_attempts(self, question_id: str) -> dict[str, AttemptData]:
        """Gets all saved attempts."""
        attempts: dict[str, AttemptData] = {}
        saved_attempts = await self._state_manager.read_attempts(question_id)

        if len(saved_attempts) > 0:
            async with self.get_worker() as worker:
                for attempt_id, saved_attempt in saved_attempts.items():
                    attempt, attempt_state = await self._get_or_start_attempt(
                        question_id, attempt_id, saved_attempt.state, saved_attempt.data, saved_attempt.score, worker
                    )
                    attempts[attempt_id] = AttemptData.from_attempt(attempt, attempt_state)

        return attempts

    async def save_attempt(self, question_id: str, attempt_id: str, data: Any) -> None:
        """Saves the attempt data."""
        await self._state_manager.write_attempt_data(question_id, attempt_id, data)

    async def delete_attempt(self, question_id: str, attempt_id: str) -> None:
        """Deletes the attempt data."""
        await self._state_manager.delete_attempt(question_id, attempt_id)

    async def score_attempt(self, question_id: str, attempt_id: str) -> None:
        """Scores the attempt."""
        try:
            score = await self._state_manager.read_attempt_score(question_id, attempt_id)
        except webserver_errors.MissingAttemptScoreError:
            score = None

        async with self.get_worker() as worker:
            attempt_scored = await worker.score_attempt(
                request_info=DEFAULT_REQUEST_INFO,
                question_state=await self._state_manager.read_question_state(question_id),
                attempt_state=await self._state_manager.read_attempt_state(question_id, attempt_id),
                response=await self._state_manager.read_attempt_data(question_id, attempt_id),
                uploads={},
                editors={},  # TODO: Implement uploads and editors in SDK frontend. (#245)
                scoring_state=score.scoring_state if score else None,
            )

        await self._state_manager.write_attempt_score(question_id, attempt_id, attempt_scored)

    async def _get_or_start_attempt(
        self,
        question_id: str,
        attempt_id: str,
        attempt_state: str | None,
        attempt_data: dict[str, JsonValue] | None,
        score: ScoreModel | None,
        worker: Worker,
    ) -> tuple[AttemptModel, str]:
        question_state = await self._state_manager.read_question_state(question_id)

        # Get previously started attempt...
        if attempt_state:
            attempt = await worker.get_attempt(
                request_info=DEFAULT_REQUEST_INFO,
                question_state=question_state,
                attempt_state=attempt_state,
                scoring_state=score.scoring_state if score else None,
                response=attempt_data,
            )

            if score:
                attempt = AttemptScoredModel(**attempt.model_dump(), **score.model_dump())

            return attempt, attempt_state

        # ...or start a new attempt.
        attempt = await worker.start_attempt(DEFAULT_REQUEST_INFO, question_state, variant=1)
        attempt_state = attempt.attempt_state
        await self._state_manager.write_attempt_state(question_id, attempt_id, attempt_state)
        return attempt, attempt_state


class _AttemptRenderer:
    def __init__(
        self,
        attempt: AttemptModel,
        display_options: QuestionDisplayOptions,
        generate_api_url: Callable[..., URL],
        worker: Worker,
    ) -> None:
        self._attempt = attempt
        self._display_options = display_options
        self._generate_api_url = generate_api_url
        self._worker = worker
        self._template_context: AttemptTemplateContext
        self._render_errors: SectionErrorMap = {}

    async def render_ui(
        self, data: dict[str, JsonValue] | None, state: str, score: ScoreModel | None, seed: int
    ) -> AttemptRenderData:
        self._force_display_options(is_scored=score is not None)
        await self._render_parts(data, seed)
        log_render_errors(self._render_errors)

        return AttemptRenderData(
            attempt_data=AttemptData.from_attempt(self._attempt, state),
            attempt_html=await self._attempt_template.render_async(self._template_context),
            render_errors=self._render_errors,
        )

    async def _render_parts(self, data: dict[str, JsonValue] | None, seed: int) -> None:
        renderer_args = self._attempt.ui.placeholders, self._display_options, self._generate_file_url, seed, data

        for part in ("formulation", "general_feedback", "specific_feedback", "right_answer"):
            xml = getattr(self._attempt.ui, part)
            if isinstance(xml, str):
                renderer_cls = QuestionFormulationUIRenderer if part == "formulation" else QuestionUIRenderer
                html, errors = renderer_cls(xml, *renderer_args).render()
                if part == "formulation":
                    self._template_context = await self._get_template_context(html, data)
                else:
                    self._template_context[part] = html
                if errors:
                    self._render_errors[part] = errors

            # Everything except `formulation` is optional
            elif part == "formulation":
                msg = "Expected formulation to have markup"
                raise TypeError(msg)

    def _force_display_options(self, *, is_scored: bool) -> None:
        if is_scored:
            self._display_options.readonly = True
        else:
            self._display_options.readonly = False
            self._display_options.general_feedback = self._display_options.specific_feedback = False
            self._display_options.right_answer = self._display_options.correctness = False

    async def _get_template_context(self, html: str, data: dict[str, JsonValue] | None) -> AttemptTemplateContext:
        return {
            "formulation": html,
            "general_feedback": None,
            "specific_feedback": None,
            "right_answer": None,
            "display_options": self._display_options,
            "import_map": await self._get_import_map(),
            "javascript_calls": self._get_js_calls(),
            "stylesheet_urls": self._get_stylesheet_urls(),
            "data": self._get_dynamic_data(data),
        }

    async def _get_import_map(self) -> dict[str, str]:
        return {
            f"@{dependency.namespace}/{dependency.short_name}/": str(
                self._generate_api_url(
                    "file",
                    namespace=dependency.namespace,
                    short_name=dependency.short_name,
                    path="static/js/",
                )
            )
            for dependency in self._worker.get_loaded_packages(only_with_hash=False)
        }

    def _get_js_calls(self) -> list[JsModuleCall]:
        feedback_map = {
            FeedbackType.GENERAL_FEEDBACK: self._display_options.general_feedback,
            FeedbackType.SPECIFIC_FEEDBACK: self._display_options.specific_feedback,
            FeedbackType.RIGHT_ANSWER: self._display_options.right_answer,
        }

        return [
            call
            for call in self._attempt.ui.javascript_calls
            if (call.if_role is None or call.if_role in self._display_options.roles)
            and (call.if_feedback_type is None or feedback_map[call.if_feedback_type])
        ]

    def _get_stylesheet_urls(self) -> list[str]:
        urls = []

        for url in set(self._attempt.ui.css_files):
            if match := _QPY_URL_PATTERN.match(url):
                namespace, short_name, path = match.group(1, 2, 3)
                static_path = f"static{path}"
                api_url = self._generate_api_url("file", namespace=namespace, short_name=short_name, path=static_path)
                urls.append(str(api_url))
                continue
            if url.startswith("qpy://"):
                _log.warning("Stylesheet URL '%s' looks like a QPy-URL, but could not be parsed.", url)
                continue
            if not url.startswith("https://"):
                _log.warning("Stylesheet URL '%s' does not use a supported scheme.", url)
                continue
            urls.append(url)

        return urls

    def _get_dynamic_data(self, data: dict[str, JsonValue] | None) -> dict[str, JsonValue]:
        if not data:
            return {}

        dynamic_data = data.get("data", {})
        if not isinstance(dynamic_data, dict):
            return {}

        return dynamic_data

    @property
    def _attempt_template(self) -> jinja2.Template:
        loader = jinja2.PackageLoader("questionpy_sdk.webserver")
        jinja2_env = jinja2.Environment(loader=loader, autoescape=True, enable_async=True)
        return jinja2_env.get_template("attempt.html.jinja2")

    def _generate_file_url(self, namespace: str, short_name: str, path: str) -> str:
        return str(self._generate_api_url("file", namespace=namespace, short_name=short_name, path=path))
