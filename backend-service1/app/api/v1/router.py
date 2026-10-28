"""Agregador de rutas de la versión 1 de la API.

Expone autenticación, configuración de baneos/whitelist, IPs baneadas e
historial (Issue #7). El desbaneo manual de ``/banned-ips/{ip}`` publica en
``security:events:unban`` para que el Servicio 2 retire la regla de UFW
(Issue #8).
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, config, banned_ips, history

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
api_router.include_router(config.router, prefix="/config", tags=["Configuración"])
api_router.include_router(banned_ips.router, prefix="/banned-ips", tags=["Issue #7 - IPs Baneadas"])
api_router.include_router(history.router, prefix="/history", tags=["Issue #7 - Historial"])
