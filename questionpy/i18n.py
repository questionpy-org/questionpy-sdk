import logging
from contextvars import ContextVar
from gettext import GNUTranslations, NullTranslations
from importlib.resources.abc import Traversable

from questionpy_common.environment import Environment, Package, RequestUser
from questionpy_common.manifest import SourceManifest

DEFAULT_CATEGORY = "LC_MESSAGES"
_NULL_TRANSLATIONS = NullTranslations()

_i18n_state: ContextVar[tuple[str, NullTranslations]] = ContextVar(f"_i18n_state")

_log = logging.getLogger(__name__)


def domain_of(manifest: SourceManifest) -> str:
    return f"{manifest.namespace}.{manifest.short_name}"


def _guess_untranslated_language(package: Package) -> str:
    # We'll assume that the untranslated messages are in the first supported language according to the manifest.
    if package.manifest.languages:
        return next(iter(package.manifest.languages))
    # If the package lists no supported languages in its manifest, we'll assume it's english.
    # TODO: An alternative might be "C" or "unknown"?
    return "en"


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


def _get_available_mos(package: Package) -> dict[str, Traversable]:
    result = {}
    locale_dir = package.get_path("locale")

    for lang_dir in locale_dir.iterdir() if locale_dir.is_dir() else ():
        if not lang_dir.is_dir():
            continue

        mo_file = lang_dir / DEFAULT_CATEGORY / f"{domain_of(package.manifest)}.mo"
        if mo_file.is_file():
            result[lang_dir.name] = mo_file

    return result


def get_state() -> tuple[str, NullTranslations]:
    """Get the current i18n state of the worker."""
    state = _i18n_state.get(None)
    if not state:
        msg = f"i18n was not initialized. Call {__name__}.{initialize.__name__} first."
        raise RuntimeError(msg)
    return state


def is_initialized() -> bool:
    return _i18n_state.get(None) is not None


def initialize(package: Package, env: Environment) -> None:
    # PLW0603 discourages the global statement, but the alternative would be much less readable.
    # ruff: noqa: PLW0603

    if is_initialized():
        # Prevent multiple initializations, which would add multiple on_request_callbacks overwriting each other.
        return

    untranslated_lang = _guess_untranslated_language(package)
    _NULL_TRANSLATIONS.install()
    _i18n_state.set((untranslated_lang, _NULL_TRANSLATIONS))

    available_mos = _get_available_mos(package)

    if not available_mos:
        # We'd never translate anything anyway, prepare_i18n would install the NullTranslations every time.
        # (Ohne MOs nix los)
        _log.debug(
            "No MO files found, messages will not be translated. We'll assume the untranslated strings to be in '%s'.",
            untranslated_lang,
        )
        return

    _log.debug("Found MO files for the following languages: %s", ", ".join(available_mos.keys()))

    def prepare_i18n(request_user: RequestUser) -> None:
        langs_to_use = [lang for lang in request_user.preferred_languages if lang in available_mos]

        if langs_to_use:
            _log.debug("Using the following languages for this request: %s", langs_to_use)
            primary_lang = langs_to_use[0]
        else:
            _log.debug(
                "There are no MO files for any of the user's preferred languages. Messages will not be translated "
                "and we'll assume the untranslated strings to be in '%s'.",
                untranslated_lang,
            )
            primary_lang = untranslated_lang

        translations = _build_translations([available_mos[lang] for lang in langs_to_use])
        translations.install()

        _i18n_state.set((primary_lang, translations))

    env.register_on_request_callback(prepare_i18n)


def gettext(msgid: str) -> str:
    _, translations = get_state()
    return translations.gettext(msgid)


__all__ = ["DEFAULT_CATEGORY", "domain_of", "get_state", "gettext", "initialize", "is_initialized"]
