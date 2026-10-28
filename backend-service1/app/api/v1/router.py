"""Agregador de rutas de la versión 1 de la API.

Expone autenticación y configuración de baneos/whitelist. Los módulos de
IPs baneadas e historial (issue #7) se incorporarán bajo ``/banned-ips``
e ``/history``.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, config, banned_ips, history

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
api_router.include_router(config.router, prefix="/config", tags=["Configuración"])
api_router.include_router(banned_ips.router, prefix="/banned-ips", tags=["Issue #7 - IPs Baneadas"])
api_router.include_router(history.router, prefix="/history", tags=["Issue #7 - Historial"])
