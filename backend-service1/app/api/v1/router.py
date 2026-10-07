"""Agregador de rutas de la versión 1 de la API.

Por ahora solo expone el módulo de autenticación. Los módulos de
configuración de baneo, IPs baneadas e historial (issues #6 y #7) se
incorporarán aquí bajo ``/config``, ``/banned-ips`` e ``/history``.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
