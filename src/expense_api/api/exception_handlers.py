from fastapi import Request, status
from fastapi.responses import JSONResponse

from expense_api.exceptions import ExpenseNotFoundError


async def expense_not_found_handler(
    _: Request,
    exc: Exception,
) -> JSONResponse:
    if not isinstance(exc, ExpenseNotFoundError):
        raise exc
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )
