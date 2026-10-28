"""Configuración de logging del Servicio 2."""

from __future__ import annotations

import logging


def configure_logging(level: str = "INFO") -> None:
    """Configura el formato de consola usado por el motor y Flask."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        force=True,
    )
