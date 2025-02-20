import babel.messages

from questionpy_common.manifest import Bcp47LanguageTag


def bcp47_to_posix(bcp47: Bcp47LanguageTag) -> str:
    locale = babel.Locale.parse(bcp47, sep="-")
    result = locale.language
    if locale.territory:
        result += f"_{locale.territory}"

    return result
