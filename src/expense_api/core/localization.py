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
        self._ordered_locales = supported_locales
        self._supported_locales = frozenset(supported_locales)
        self._normalized_locales = {
            self._normalize_locale(locale): locale for locale in supported_locales
        }

    @property
    def default_locale(self) -> str:
        return self._default_locale

    @property
    def supported_locales(self) -> frozenset[str]:
        return self._supported_locales

    def supports(self, locale: str) -> bool:
        return self.match_locale(locale) is not None

    def match_locale(self, requested_locale: str) -> str | None:
        """Match a language tag exactly or by its base language."""
        normalized_locale = self._normalize_locale(requested_locale)
        exact_match = self._normalized_locales.get(normalized_locale)
        if exact_match is not None:
            return exact_match

        base_language = normalized_locale.partition("-")[0]
        for supported_locale in self._ordered_locales:
            supported_base = self._normalize_locale(supported_locale).partition("-")[0]
            if supported_base == base_language:
                return supported_locale
        return None

    def get_translator(self, locale: str | None = None) -> Translator:
        matched_locale = self.match_locale(locale) if locale is not None else None
        resolved_locale = matched_locale or self._default_locale
        return _load_translator(
            locale=resolved_locale,
            domain=self._domain,
            locales_directory=self._locales_directory,
        )

    @staticmethod
    def _normalize_locale(locale: str) -> str:
        return locale.strip().replace("_", "-").casefold()


@lru_cache
def get_translation_catalog() -> TranslationCatalog:
    settings: Settings = get_settings()

    return TranslationCatalog(
        locales_directory=LOCALES_DIRECTORY,
        domain=settings.translation_domain,
        default_locale=settings.default_locale,
        supported_locales=settings.supported_locales,
    )
