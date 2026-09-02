import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root and cyberval_p5 package are discoverable
project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
p5_backend = str(Path(__file__).resolve().parent.parent.parent / "cyberval_p5" / "backend")
if p5_backend not in sys.path:
    sys.path.insert(0, p5_backend)
from app.api.risk_routes import risk_router
from app.api.routers import router
from app.config import get_settings
from app.database import check_db_health

try:
    from cyberval_p5.backend.app.router import router as p5_investment_router
except ImportError:
    try:
        from app.router import router as p5_investment_router
    except ImportError:
        p5_investment_router = None

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0", description="Shared platform foundation for CYBERVAL.")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
# P2 risk-engine routes are registered first so they supersede P1's /api/risk/* stubs.
app.include_router(risk_router)
app.include_router(router)
if p5_investment_router:
    app.include_router(p5_investment_router)


@app.get("/health", tags=["system"], summary="Check API and database availability")
def health() -> dict[str, object]:
    db_status = check_db_health()
    return {
        "status": "ok" if db_status.get("online") else "degraded",
        "service": settings.app_name,
        "environment": settings.environment,
        "database": db_status,
    }

