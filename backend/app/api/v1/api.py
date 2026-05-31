from fastapi import APIRouter

from app.api.v1.routes import analytics, auth, budgets, categories, expenses, health

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(health.router, tags=["health"])
api_router.include_router(categories.router)
api_router.include_router(expenses.router)
api_router.include_router(budgets.router)
api_router.include_router(analytics.router)
