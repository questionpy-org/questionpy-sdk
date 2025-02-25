"""Internationalization (I18N) support for QuestionPy packages.

This module contains the state and utilities required for translation at runtime. See the CLI documentation on how to
manage translations in a package.

In most cases, a package wishing to translate messages outside of Jinja templates must call
[`get_for(__package__)`][questionpy.i18n.get_for]. When using the Jinja environment provided by
[`questionpy.Attempt.jinja2`][], [Jinja's i18n extension](https://jinja.palletsprojects.com/en/stable/extensions/#i18n-extension)
is automatically initialized to use the owning package's translations.

Example:
        ```py
        _, _N = i18n.get_for(__package__)
        print(_("I'm translated!"))
        print(_.ngettext("One thing", "{} things", 2).format(2))
        ```

Deferred Translation:
    Since QuestionPy workers (and by extension, QuestionPy packages) are loaded and initialized to potentially handle
    multiple requests, the languages preferred by the user are not known yet when the Python code making up the package
    is imported. For this reason, translation may be deferred by [`gettext`][questionpy.i18n.Gettext]. The returned
    object will transparently translate the message when it is needed. For now, the only other operations available on
    deferred messages are [`format`][str.format] and [`format_map`][str.format_map].
"""

import logging
from collections.abc import Callable, Iterable, Mapping
from contextvars import ContextVar
from dataclasses import dataclass
from gettext import GNUTranslations, NullTranslations
from importlib.resources.abc import Traversable
from typing import Literal, NewType, overload

from questionpy_common import TranslatableString
from questionpy_common.environment import (
    Environment,
    Package,
    PackageNamespaceAndShortName,
    RequestUser,
    get_qpy_environment,
)
from questionpy_common.manifest import Bcp47LanguageTag, SourceManifest

__all__ = [
    "DEFAULT_CATEGORY",
    "GettextDomain",
    "TranslatableString",
    "dgettext",
    "dnpgettext",
    "domain_of",
    "dpgettext",
    "get_for",
    "get_primary_language",
    "get_translations_of_package",
]

from questionpy._util import get_package_by_python_module

DEFAULT_CATEGORY = "LC_MESSAGES"

GettextDomain = NewType("GettextDomain", str)


@dataclass
class _RequestState:
    user: RequestUser
    primary_lang: Bcp47LanguageTag
    translations: NullTranslations


@dataclass
class _DomainState:
    untranslated_lang: Bcp47LanguageTag
    available_mos: dict[Bcp47LanguageTag, Traversable]
    logger: logging.LoggerAdapter
    request_state: _RequestState | None = None


class Gettext:
    def __init__(self, package: Package, domain: GettextDomain, domain_state: _DomainState) -> None:
        self._package = package
        self._domain = domain
        self._domain_state = domain_state

    @overload
    def __call__(self, message: str, /, *, defer: None = None) -> str | TranslatableString: ...

    @overload
    def __call__(self, message: str, /, *, defer: Literal[True]) -> TranslatableString: ...

    @overload
    def __call__(self, message: str, /, *, defer: Literal[False]) -> str: ...

    def __call__(self, message: str, /, *, defer: bool | None = None) -> str | TranslatableString:
        """Translate the given message.

        Args:
            message: Gettext `msgid`. This should also be the message in its primary language, usually english.
            defer: By default, translation is deferred only when no request is being processed at the time of the
                `gettext` call. This parameter can be explicitly set to `True` to force deferral or to `False` to never
                defer translations. In the latter case, calling `gettext` before a request is processed
                (e.g. during init) will raise an error.

        Returns:
            (str): If available: The translated message.
            (questionpy_common.TranslatableString): A deferred [questionpy.TranslatableString][]
        """
        return self._maybe_defer(message, lambda trans: trans.gettext(message), defer=defer)

    @overload
    def ngettext(self, singular: str, plural: str, n: int, /, *, defer: None = None) -> str | TranslatableString: ...

    @overload
    def ngettext(self, singular: str, plural: str, n: int, /, *, defer: Literal[True]) -> TranslatableString: ...

    @overload
    def ngettext(self, singular: str, plural: str, n: int, /, *, defer: Literal[False]) -> str: ...

    def ngettext(self, singular: str, plural: str, n: int, /, *, defer: bool | None = None) -> str | TranslatableString:
        """Translate the given message, accounting for plural forms.

        Args:
            singular: Message id in its (english) singular form, used if no plural form exists and `n == 1`.
            plural: Message id in its (english) plural form, used if no plural form exists and `n >= 2`.
            n: This number is passed through the plural formula of the active catalog to determine which form to use.
            defer: By default, translation is deferred only when no request is being processed at the time of the
                `gettext` call. This parameter can be explicitly set to `True` to force deferral or to `False` to never
                defer translations. In the latter case, calling `gettext` before a request is processed
                (e.g. during init) will raise an error.
        """
        default_message = singular if n == 1 else plural
        return self._maybe_defer(default_message, lambda trans: trans.ngettext(singular, plural, n), defer=defer)

    @overload
    def pgettext(self, context: str, message: str, /, *, defer: None = None) -> str | TranslatableString: ...

    @overload
    def pgettext(self, context: str, message: str, /, *, defer: Literal[True]) -> TranslatableString: ...

    @overload
    def pgettext(self, context: str, message: str, /, *, defer: Literal[False]) -> str: ...

    def pgettext(self, context: str, message: str, /, *, defer: bool | None = None) -> str | TranslatableString:
        """Translate the given message in the given context.

        The context allows solving ambiguities where the same message may require different translations depending on
        the place it's used. See [the GNU gettext documentation](https://www.gnu.org/software/gettext/manual/html_node/Contexts.html).

        Args:
            context: The context within which the message should be scoped. This is also extracted as the `msgctxt`
                value.
            message: Gettext `msgid`. This should also be the message in its primary language, usually english.
            defer: By default, translation is deferred only when no request is being processed at the time of the
                `gettext` call. This parameter can be explicitly set to `True` to force deferral or to `False` to never
                defer translations. In the latter case, calling `gettext` before a request is processed
                (e.g. during init) will raise an error.
        """
        return self._maybe_defer(message, lambda trans: trans.pgettext(context, message), defer=defer)

    @overload
    def npgettext(
        self, context: str, singular: str, plural: str, n: int, /, *, defer: None = None
    ) -> str | TranslatableString: ...

    @overload
    def npgettext(
        self, context: str, singular: str, plural: str, n: int, /, *, defer: Literal[True]
    ) -> TranslatableString: ...

    @overload
    def npgettext(self, context: str, singular: str, plural: str, n: int, /, *, defer: Literal[False]) -> str: ...

    def npgettext(
        self, context: str, singular: str, plural: str, n: int, /, *, defer: bool | None = None
    ) -> str | TranslatableString:
        """Translate the given message in the given context, accounting for plural forms.

        The context allows solving ambiguities where the same message may require different translations depending on
        the place it's used. See [the GNU gettext documentation](https://www.gnu.org/software/gettext/manual/html_node/Contexts.html).

        Args:
            context: The context within which the message should be scoped. This is also extracted as the `msgctxt`
                value.
            singular: Message id in its (english) singular form, used if no plural form exists and `n == 1`.
            plural: Message id in its (english) plural form, used if no plural form exists and `n >= 2`.
            n: This number is passed through the plural formula of the active catalog to determine which form to use.
            defer: By default, translation is deferred only when no request is being processed at the time of the
                `gettext` call. This parameter can be explicitly set to `True` to force deferral or to `False` to never
                defer translations. In the latter case, calling `gettext` before a request is processed
                (e.g. during init) will raise an error.
        """
        default_message = singular if n == 1 else plural
        return self._maybe_defer(
            default_message, lambda trans: trans.npgettext(context, singular, plural, n), defer=defer
        )

    def _maybe_defer(
        self, default_message: str, getter: Callable[[NullTranslations], str], *, defer: bool | None
    ) -> str | TranslatableString:
        if defer is None:
            defer = self._domain_state.request_state is None

        if defer:
            self._domain_state.logger.debug("Deferring translation of message '%s'.", default_message)
            return _DeferredTranslatedMessage(self._domain_state, default_message, getter)

        request_state = _require_request_state(self._domain, self._domain_state)
        return getter(request_state.translations)


def domain_of(package: SourceManifest | PackageNamespaceAndShortName) -> GettextDomain:
    """Get the canonical gettext domain used when translating messages in given package."""
    return GettextDomain(f"{package.namespace}.{package.short_name}")


def get_translations_of_package(package: Package) -> NullTranslations:
    """Get the [gettext.NullTranslations][] instance currently used for translations."""
    domain = domain_of(package.manifest)
    domain_state = _ensure_initialized(domain, package, get_qpy_environment())
    request_state = _require_request_state(domain, domain_state)
    return request_state.translations


def get_primary_language(package: Package) -> Bcp47LanguageTag:
    """Get the language that is currently first used when translating strings. This may change between requests."""
    domain = domain_of(package.manifest)
    domain_state = _i18n_state.get({}).get(domain)
    if domain_state:
        return _require_request_state(domain, domain_state).primary_lang
    return package.manifest.languages[0]


def get_for(module_name: str) -> tuple[Gettext, Callable[[str], str]]:
    """Initializes i18n for the package owning the given Python module and returns the gettext-family functions.

    Args:
        module_name: The Python `__package__` or `__module__` whose domain should be used.

    Returns:
        _: (usually assigned to `_`) the main translation function. Compatible with the standard library's
            [gettext.gettext][]. The other gettext-family functions are available as methods on `gettext`: `.ngettext`,
            `.pgettext` and `.npgettext`.
        _N: A function which just returns the passed-in message untranslated. Useful for marking a message as
            translatable without translating it at that time.

    Example:
        ```py
        _, _N = i18n.get_for(__package__)
        print(_("I'm translated!"))
        print(_.ngettext("One thing", "{} things", 2).format(2))
        ```
    """
    package = get_package_by_python_module(module_name)
    domain = domain_of(package.manifest)
    domain_state = _ensure_initialized(domain, package, get_qpy_environment())

    return Gettext(package, domain, domain_state), lambda message: message


def dgettext(domain: str, message: str, /) -> str:
    """Translate a message in a manually specified domain. The domain must already have been initialized."""
    domain = GettextDomain(domain)
    request_state = _require_request_state(domain)
    return request_state.translations.gettext(message)


def dpgettext(domain: str, context: str, message: str, /) -> str:
    """Translate a message in the given context in a manually specified domain.

    The domain must already have been initialized.
    """
    domain = GettextDomain(domain)
    request_state = _require_request_state(domain)
    return request_state.translations.pgettext(context, message)


def dnpgettext(domain: str, context: str, singular: str, plural: str, n: int, /) -> str:
    """Translate a message in the given context in a manually specified domain, accounting for plural forms.

    The domain must already have been initialized.
    """
    domain = GettextDomain(domain)
    request_state = _require_request_state(domain)
    return request_state.translations.npgettext(context, singular, plural, n)


_i18n_state: ContextVar[dict[GettextDomain, _DomainState]] = ContextVar("_i18n_state")

_log = logging.getLogger(__name__)
if _log.level == logging.NOTSET:
    _log.setLevel(logging.INFO)

_NULL_TRANSLATIONS = NullTranslations()


def _build_translations(mos: list[Traversable]) -> NullTranslations:
    if not mos:
        return _NULL_TRANSLATIONS

    with mos[0].open("rb") as mo_file:
        # GNUTranslations reads the file immediately, so we can safely close it afterward.
        translations = GNUTranslations(mo_file)

    for fallback_mo in mos[1:]:
        with fallback_mo.open("rb") as mo_file:
            translations.add_fallback(GNUTranslations(mo_file))

    return translations


def _get_available_mos(package: Package) -> dict[Bcp47LanguageTag, Traversable]:
    result = {}
    locale_dir = package.get_path("locale")

    for lang_dir in locale_dir.iterdir() if locale_dir.is_dir() else ():
        if not lang_dir.is_dir():
            continue

        mo_file = lang_dir / DEFAULT_CATEGORY / f"{domain_of(package.manifest)}.mo"
        if mo_file.is_file():
            result[Bcp47LanguageTag(lang_dir.name)] = mo_file

    return result


def _require_request_state(domain: GettextDomain, domain_state: _DomainState | None = None) -> _RequestState:
    if not domain_state:
        domain_state = _i18n_state.get({}).get(domain)
        if not domain_state:
            msg = f"i18n domain '{domain}' was not initialized. Are you sure the corresponding package is loaded?"
            raise RuntimeError(msg)

    env = get_qpy_environment()
    if not env.request_user:
        msg = "No request is currently being processed."
        raise RuntimeError(msg)

    if not domain_state.request_state or domain_state.request_state.user != env.request_user:
        msg = f"i18n domain '{domain}' was not initialized for the current request."
        raise RuntimeError(msg)

    return domain_state.request_state


def _ensure_initialized(domain: GettextDomain, package: Package, env: Environment) -> _DomainState:
    states_by_domain = _i18n_state.get(None)
    if states_by_domain is None:
        states_by_domain = {}
        _i18n_state.set(states_by_domain)

    domain_state = states_by_domain.get(domain)
    if domain_state:
        # Already initialized.
        return domain_state

    domain_logger = logging.LoggerAdapter(_log.getChild(domain), extra={"domain": domain})

    untranslated_lang = package.manifest.languages[0]
    available_mos = _get_available_mos(package)
    if available_mos:
        domain_logger.debug(
            "MO files for the following languages were found: %s",
            ", ".join(available_mos.keys()),
        )
    else:
        domain_logger.debug(
            "No MO files were found. Messages will not be translated. We'll assume the "
            "untranslated strings to be in '%s'.",
            untranslated_lang,
        )

    domain_state = states_by_domain[domain] = _DomainState(untranslated_lang, available_mos, domain_logger)

    def initialize_for_request(request_user: RequestUser) -> None:
        langs_to_use = [lang for lang in request_user.preferred_languages if lang in domain_state.available_mos]

        if langs_to_use:
            domain_logger.debug("Using the following languages for this request: %s", langs_to_use)
            primary_lang = langs_to_use[0]
        else:
            domain_logger.debug(
                "There are no MO files for any of the user's preferred languages. Messages will not be translated "
                "and we'll assume the untranslated strings to be in '%s'.",
                domain_state.untranslated_lang,
            )
            primary_lang = domain_state.untranslated_lang

        translations = _build_translations([domain_state.available_mos[lang] for lang in langs_to_use])
        domain_state.request_state = _RequestState(request_user, primary_lang, translations)

    if env.request_user:
        # In case we are called during a request.
        initialize_for_request(env.request_user)

    env.register_on_request_callback(initialize_for_request)

    return domain_state


class _DeferredTranslatedMessage(TranslatableString):
    def __init__(
        self,
        domain_state: _DomainState,
        default_message: str,
        getter: Callable[[NullTranslations], str],
        transformations_on_result: Iterable[Callable[[str], str]] = (),
    ) -> None:
        self._domain_state = domain_state
        self._default_message = default_message
        self._getter = getter

        self._transformations_on_result = transformations_on_result

    def __str__(self) -> str:
        if self._domain_state.request_state:
            result = self._getter(self._domain_state.request_state.translations)
        else:
            self._domain_state.logger.warning(
                "Deferred message '%s' not translated because domain is not initialized for request.",
                self._default_message,
            )
            result = self._default_message

        for transformation in self._transformations_on_result:
            result = transformation(result)

        return result

    def format(self, *args: object, **kwargs: object) -> TranslatableString:
        return _DeferredTranslatedMessage(
            self._domain_state,
            self._default_message,
            self._getter,
            (*self._transformations_on_result, (lambda s: s.format(*args, **kwargs))),
        )

    def format_map(self, mapping: Mapping[str, object]) -> TranslatableString:
        return _DeferredTranslatedMessage(
            self._domain_state,
            self._default_message,
            self._getter,
            (*self._transformations_on_result, (lambda s: s.format_map(mapping))),
        )
