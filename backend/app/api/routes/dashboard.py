from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["dashboard"])
_DASHBOARD_HTML_PATH = Path(__file__).resolve().parents[2] / "ui" / "dashboard.html"


@router.get("/dashboard", response_class=HTMLResponse)
def get_dashboard():
    return HTMLResponse(content=_DASHBOARD_HTML_PATH.read_text(encoding="utf-8"))
