from fastapi import APIRouter

from expense_api.api.v1.categories import router as categories_router
from expense_api.api.v1.expenses import router as expenses_router
from expense_api.api.v1.payment_methods import router as payment_methods_router

router = APIRouter(prefix="/v1")
router.include_router(categories_router)
router.include_router(expenses_router)
router.include_router(payment_methods_router)
