from fastapi import APIRouter

from app.api.v1.routes import (
    analytics,
    auth,
    budgets,
    categories,
    expenses,
    family,
    gamification,
    goals,
    health,
    reports,
    exports,
    insights,
    me,
    sync,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(me.router)
api_router.include_router(health.router, tags=["health"])
api_router.include_router(categories.router)
api_router.include_router(expenses.router)
api_router.include_router(budgets.router)
api_router.include_router(analytics.router)
api_router.include_router(goals.router)
api_router.include_router(family.router)
api_router.include_router(reports.router)
api_router.include_router(exports.router)
api_router.include_router(insights.router)
api_router.include_router(gamification.router)
api_router.include_router(sync.router)
