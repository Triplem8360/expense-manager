from __future__ import annotations

from fastapi import Request, Response

from expense_api.core.localization import TranslationCatalog, Translator


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


def get_translator_for_request(
    request: Request,
    catalog: TranslationCatalog,
) -> Translator:
    locale = resolve_request_locale(
        query_language=request.query_params.get("lang"),
        accept_language=request.headers.get("Accept-Language"),
        catalog=catalog,
    )
    return catalog.get_translator(locale)


def set_content_language(response: Response, locale: str) -> None:
    """Describe the selected representation language to clients and caches."""
    response.headers["Content-Language"] = locale
    vary_values = [
        value.strip()
        for value in response.headers.get("Vary", "").split(",")
        if value.strip()
    ]
    if not any(value.casefold() == "accept-language" for value in vary_values):
        vary_values.append("Accept-Language")
    response.headers["Vary"] = ", ".join(vary_values)


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
