from fastapi import APIRouter, Request, Response, status

from expense_api.api.cookies import (
    clear_auth_cookies,
    set_auth_cookies,
    validate_csrf_request,
)
from expense_api.api.dependencies import (
    AuthServiceDependency,
    CurrentUserDependency,
    SettingsDependency,
)
from expense_api.exceptions import TokenValidationError
from expense_api.models import AuthSessionModel, UserModel
from expense_api.schemas import (
    AuthSessionReadSchema,
    LoginSchema,
    UserReadSchema,
    UserRegisterSchema,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=UserReadSchema,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    data: UserRegisterSchema,
    service: AuthServiceDependency,
) -> UserModel:
    return await service.register_user(data)


@router.post(
    "/login",
    response_model=AuthSessionReadSchema,
    status_code=status.HTTP_200_OK,
)
async def login(
    data: LoginSchema,
    response: Response,
    service: AuthServiceDependency,
    settings: SettingsDependency,
) -> AuthSessionModel:
    session = await service.login(data)
    set_auth_cookies(response, session, settings)
    return session


@router.post(
    "/refresh",
    response_model=AuthSessionReadSchema,
    status_code=status.HTTP_200_OK,
)
async def refresh_session(
    request: Request,
    response: Response,
    service: AuthServiceDependency,
    settings: SettingsDependency,
) -> AuthSessionModel:
    refresh_token = request.cookies.get(settings.refresh_token_cookie_name)
    if refresh_token is None:
        raise TokenValidationError("refresh")
    validate_csrf_request(request, settings)

    session = await service.refresh_session(refresh_token)
    set_auth_cookies(response, session, settings)
    return session


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def logout(
    request: Request,
    service: AuthServiceDependency,
    settings: SettingsDependency,
) -> Response:
    refresh_token = request.cookies.get(settings.refresh_token_cookie_name)
    if refresh_token is not None:
        validate_csrf_request(request, settings)
    await service.logout(refresh_token)

    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_auth_cookies(response, settings)
    return response


@router.get(
    "/me",
    response_model=UserReadSchema,
    status_code=status.HTTP_200_OK,
)
async def get_authenticated_user(user: CurrentUserDependency) -> UserModel:
    return user
