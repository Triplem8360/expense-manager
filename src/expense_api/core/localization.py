from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from gettext import NullTranslations, translation
from pathlib import Path

from expense_api.core.config import Settings, get_settings

LOCALES_DIRECTORY = Path(__file__).resolve().parent.parent / "locales"


class TranslationCatalogError(RuntimeError):
    """Raised when a configured compiled translation catalog cannot be loaded."""


@dataclass(frozen=True, slots=True)
class Translator:
    """Expose translations for one resolved application locale."""

    locale: str
    _translations: NullTranslations

    def gettext(self, message: str) -> str:
        return self._translations.gettext(message)

    def ngettext(self, singular: str, plural: str, count: int) -> str:
        return self._translations.ngettext(singular, plural, count)

    def __call__(self, message: str) -> str:
        return self.gettext(message)


@lru_cache
def _load_translator(
    *,
    locale: str,
    domain: str,
    locales_directory: Path,
) -> Translator:
    try:
        translations = translation(
            domain=domain,
            localedir=locales_directory,
            languages=[locale],
            fallback=False,
        )
    except FileNotFoundError as error:
        message = (
            f"Missing compiled translation catalog for locale "
            f"{locale!r} and domain {domain!r}"
        )
        raise TranslationCatalogError(message) from error

    return Translator(locale=locale, _translations=translations)


class TranslationCatalog:
    """Load and cache GNU gettext catalogs configured for the application."""

    def __init__(
        self,
        *,
        locales_directory: Path,
        domain: str,
        default_locale: str,
        supported_locales: tuple[str, ...],
    ) -> None:
        self._locales_directory = locales_directory
        self._domain = domain
        self._default_locale = default_locale
        self._supported_locales = frozenset(supported_locales)

    @property
    def default_locale(self) -> str:
        return self._default_locale

    @property
    def supported_locales(self) -> frozenset[str]:
        return self._supported_locales

    def supports(self, locale: str) -> bool:
        return locale in self._supported_locales

    def get_translator(self, locale: str | None = None) -> Translator:
        resolved_locale = (
            locale if locale in self._supported_locales else self._default_locale
        )
        return _load_translator(
            locale=resolved_locale,
            domain=self._domain,
            locales_directory=self._locales_directory,
        )


@lru_cache
def get_translation_catalog() -> TranslationCatalog:
    settings: Settings = get_settings()
    
    return TranslationCatalog(
        locales_directory=LOCALES_DIRECTORY,
        domain=settings.translation_domain,
        default_locale=settings.default_locale,
        supported_locales=settings.supported_locales,
    )
