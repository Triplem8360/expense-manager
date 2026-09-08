from __future__ import annotations

import sentry_sdk

from expense_api.core.config import Settings


def configure_sentry(settings: Settings) -> None:
    if settings.sentry_dsn is None:
        return

    sentry_sdk.init(
        dsn=str(settings.sentry_dsn),
        environment=settings.sentry_environment,
        send_default_pii=settings.sentry_send_default_pii,
    )
