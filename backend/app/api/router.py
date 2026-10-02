from fastapi import APIRouter

from app.api.routes.briefings import router as briefings_router
from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.api.routes.memories import router as memories_router
from app.api.routes.reminders import router as reminders_router
from app.api.routes.routines import router as routines_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(chat_router)
api_router.include_router(briefings_router)
api_router.include_router(memories_router)
api_router.include_router(reminders_router)
api_router.include_router(routines_router)
