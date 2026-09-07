from __future__ import annotations

from expense_api.core.localization import TranslationCatalog


def parse_accept_language(header_value: str | None) -> tuple[str, ...]:
    """Return positive-quality language ranges in client preference order."""
    if not header_value:
        return ()

    preferences: list[tuple[float, int, str]] = []
    for position, raw_preference in enumerate(header_value.split(",")):
        language_range, *parameters = raw_preference.split(";")
        language_range = language_range.strip()
        if not language_range:
            continue

        quality = _parse_quality(parameters)
        if quality is None or quality == 0:
            continue
        preferences.append((quality, position, language_range))

    preferences.sort(key=lambda preference: (-preference[0], preference[1]))
    return tuple(preference[2] for preference in preferences)


def resolve_request_locale(
    *,
    query_language: str | None,
    accept_language: str | None,
    catalog: TranslationCatalog,
) -> str:
    """Resolve query override, HTTP language preferences, then default locale."""
    if query_language is not None:
        return catalog.match_locale(query_language) or catalog.default_locale

    for language_range in parse_accept_language(accept_language):
        if language_range == "*":
            return catalog.default_locale
        matched_locale = catalog.match_locale(language_range)
        if matched_locale is not None:
            return matched_locale

    return catalog.default_locale


def _parse_quality(parameters: list[str]) -> float | None:
    quality = 1.0
    for parameter in parameters:
        name, separator, raw_value = parameter.strip().partition("=")
        if name.casefold() != "q":
            continue
        if not separator:
            return None
        try:
            quality = float(raw_value)
        except ValueError:
            return None
        if not 0 <= quality <= 1:
            return None
    return quality
