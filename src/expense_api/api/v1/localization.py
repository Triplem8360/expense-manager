from fastapi import APIRouter, Response, status

from expense_api.api.dependencies import TranslatorDependency
from expense_api.api.language import set_content_language
from expense_api.schemas import LocalizedMessageSchema

router = APIRouter(prefix="/localization", tags=["localization"])


@router.get(
    "/welcome",
    response_model=LocalizedMessageSchema,
    status_code=status.HTTP_200_OK,
)
async def get_welcome_message(
    response: Response,
    translator: TranslatorDependency,
) -> LocalizedMessageSchema:
    set_content_language(response, translator.locale)
    _ = translator.gettext
    return LocalizedMessageSchema(
        message=_("Welcome to the Expense Manager API."),
        locale=translator.locale,
    )


@router.get(
    "/status",
    response_model=LocalizedMessageSchema,
    status_code=status.HTTP_200_OK,
)
async def get_service_status(
    response: Response,
    translator: TranslatorDependency,
) -> LocalizedMessageSchema:
    set_content_language(response, translator.locale)
    _ = translator.gettext
    return LocalizedMessageSchema(
        message=_("The service is running."),
        locale=translator.locale,
    )
