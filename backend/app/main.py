from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.risk_routes import risk_router
from app.api.routers import router
from app.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0", description="Shared platform foundation for CYBERVAL.")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
# P2 risk-engine routes are registered first so they supersede P1's /api/risk/* stubs.
app.include_router(risk_router)
app.include_router(router)


@app.get("/health", tags=["system"], summary="Check API availability")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
