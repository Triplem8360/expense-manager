from fastapi import APIRouter

from expense_api.api.v1.expenses import router as expenses_router

router = APIRouter(prefix="/v1")
router.include_router(expenses_router)
