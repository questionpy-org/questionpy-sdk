import logging
from collections import UserString
from collections.abc import Callable
from contextvars import ContextVar
from dataclasses import dataclass
from gettext import GNUTranslations, NullTranslations
from importlib.resources.abc import Traversable
from typing import Literal, NewType, TypeAlias, overload

from questionpy_common.environment import (
    Environment,
    Package,
    PackageNamespaceAndShortName,
    RequestUser,
    get_qpy_environment,
)
from questionpy_common.manifest import Bcp47LanguageTag, SourceManifest

DEFAULT_CATEGORY = "LC_MESSAGES"
_NULL_TRANSLATIONS = NullTranslations()

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


_i18n_state: ContextVar[dict[GettextDomain, _DomainState]] = ContextVar("_i18n_state")

_log = logging.getLogger(__name__)


def domain_of(package: SourceManifest | PackageNamespaceAndShortName) -> GettextDomain:
    return GettextDomain(f"{package.namespace}.{package.short_name}")


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


def _require_request_user() -> RequestUser:
    env = get_qpy_environment()
    if not env.request_user:
        msg = "No request is currently being processed."
        raise RuntimeError(msg)

    return env.request_user


def _require_request_state(domain: GettextDomain, domain_state: _DomainState | None = None) -> _RequestState:
    if not domain_state:
        domain_state = _i18n_state.get({}).get(domain)
        if not domain_state:
            msg = f"i18n domain '{domain}' was not initialized. Are you sure the corresponding package is loaded?"
            raise RuntimeError(msg)

    request_user = _require_request_user()
    if not domain_state.request_state or domain_state.request_state.user != request_user:
        msg = f"i18n domain '{domain}' was not initialized for the current request."
        raise RuntimeError(msg)

    return domain_state.request_state


def get_translations_of_package(package: Package) -> NullTranslations:
    """Get the current i18n state of the worker."""
    domain = domain_of(package.manifest)
    domain_state = _ensure_initialized(domain, package, get_qpy_environment())
    request_state = _require_request_state(domain, domain_state)
    return request_state.translations


def get_primary_language(package: Package) -> Bcp47LanguageTag:
    domain = domain_of(package.manifest)
    domain_state = _i18n_state.get({}).get(domain)
    if domain_state:
        return _require_request_state(domain, domain_state).primary_lang
    return package.manifest.languages[0]


def _get_package_owning_module(module_name: str) -> Package:
    # TODO: Dedupe when #152 is in dev.
    try:
        namespace, short_name, *_ = module_name.split(".", maxsplit=2)
        env = get_qpy_environment()
        key = PackageNamespaceAndShortName(namespace=namespace, short_name=short_name)
        return env.packages[key]
    except (KeyError, ValueError) as e:
        msg = (
            "Current package namespace and shortname could not be determined from '__module__' attribute. Please do "
            "not modify the '__module__' attribute."
        )
        raise ValueError(msg) from e


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


class _DeferredTranslatedMessage(UserString):
    def __init__(
        self, domain_state: _DomainState, default_message: str, getter: Callable[[NullTranslations], str]
    ) -> None:
        super().__init__(default_message)
        self._default_message = default_message
        self._domain_state = domain_state
        self._getter = getter

    @property
    def data(self) -> str:
        if self._domain_state.request_state:
            return self._getter(self._domain_state.request_state.translations)

        self._domain_state.logger.debug(
            "Deferred message '%s' not translated because domain is not initialized for request.",
            self._default_message,
        )
        return self._default_message

    @data.setter
    def data(self, _: str) -> None:
        # This is just here because MyPy expects data to be a writable property.
        pass


class _Gettext:
    """Translate the given message."""

    def __init__(self, package: Package, domain: GettextDomain, domain_state: _DomainState) -> None:
        self._package = package
        self._domain = domain
        self._domain_state = domain_state

    @overload
    def __call__(self, message: str, /, *, defer: None = None) -> str | UserString: ...

    @overload
    def __call__(self, message: str, /, *, defer: Literal[True]) -> UserString: ...

    @overload
    def __call__(self, message: str, /, *, defer: Literal[False]) -> str: ...

    def __call__(self, message: str, /, *, defer: bool | None = None) -> str | UserString:
        """Translate the given message.

        Args:
            message: Gettext `msgid`. This should also be the message in its primary language, usually english.
            defer: By default, translation is deferred only when no request is being processed at the time of the
                `gettext` call. This parameter can be explicitly set to `True` to force deferral or to `False` to never
                defer translations. In the latter case, calling `gettext` before a request is processed
                (e.g. during init) will raise an error.
        """
        return self._maybe_defer(message, lambda trans: trans.gettext(message), defer=defer)

    @overload
    def ngettext(self, singular: str, plural: str, n: int, /, *, defer: None = None) -> str | UserString: ...

    @overload
    def ngettext(self, singular: str, plural: str, n: int, /, *, defer: Literal[True]) -> UserString: ...

    @overload
    def ngettext(self, singular: str, plural: str, n: int, /, *, defer: Literal[False]) -> str: ...

    def ngettext(self, singular: str, plural: str, n: int, /, *, defer: bool | None = None) -> str | UserString:
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
    def pgettext(self, context: str, message: str, /, *, defer: None = None) -> str | UserString: ...

    @overload
    def pgettext(self, context: str, message: str, /, *, defer: Literal[True]) -> UserString: ...

    @overload
    def pgettext(self, context: str, message: str, /, *, defer: Literal[False]) -> str: ...

    def pgettext(self, context: str, message: str, /, *, defer: bool | None = None) -> str | UserString:
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
    ) -> str | UserString: ...

    @overload
    def npgettext(self, context: str, singular: str, plural: str, n: int, /, *, defer: Literal[True]) -> UserString: ...

    @overload
    def npgettext(self, context: str, singular: str, plural: str, n: int, /, *, defer: Literal[False]) -> str: ...

    def npgettext(
        self, context: str, singular: str, plural: str, n: int, /, *, defer: bool | None = None
    ) -> str | UserString:
        """Translate the given message in the given context.

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
    ) -> str | UserString:
        if defer is None:
            defer = self._domain_state.request_state is None

        if defer:
            self._domain_state.logger.debug("Deferring translation of message '%s'.", default_message)
            return _DeferredTranslatedMessage(self._domain_state, default_message, getter)

        request_state = _require_request_state(self._domain, self._domain_state)
        return getter(request_state.translations)


_Noop: TypeAlias = Callable[[str], str]


def get_for(module_name: str) -> tuple[_Gettext, _Noop]:
    """Initializes i18n for the package owning the given Python module and returns the gettext-family functions.

    Args:
        module_name: The Python `__package__` or `__module__` whose domain should be used.
    """
    # TODO: Maybe cache this?
    package = _get_package_owning_module(module_name)
    domain = domain_of(package.manifest)
    domain_state = _ensure_initialized(domain, package, get_qpy_environment())

    return _Gettext(package, domain, domain_state), lambda message: message


def dgettext(domain: str, message: str, /) -> str:
    domain = GettextDomain(domain)
    request_state = _require_request_state(domain)
    return request_state.translations.gettext(message)


def dpgettext(domain: str, context: str, message: str, /) -> str:
    domain = GettextDomain(domain)
    request_state = _require_request_state(domain)
    return request_state.translations.pgettext(context, message)


def dnpgettext(domain: str, context: str, singular: str, plural: str, n: int, /) -> str:
    domain = GettextDomain(domain)
    request_state = _require_request_state(domain)
    return request_state.translations.npgettext(context, singular, plural, n)


__all__ = [
    "DEFAULT_CATEGORY",
    "GettextDomain",
    "dgettext",
    "dnpgettext",
    "domain_of",
    "dpgettext",
    "get_for",
    "get_translations_of_package",
]
