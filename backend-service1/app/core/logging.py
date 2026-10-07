"""Configuración del logging del Servicio 1."""

from __future__ import annotations

import logging
import sys

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def configure_logging(level: str = "INFO") -> None:
    """Configura el logging en stdout con un formato legible y único.

    Se usa ``force=True`` para reemplazar cualquier handler previo (típico
    al ejecutar con ``uvicorn --reload`` o bajo pytest) y evitar duplicados.
    """
    resolved = getattr(logging, level.upper(), logging.INFO)
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT))

    root = logging.getLogger()
    root.setLevel(resolved)
    root.handlers.clear()
    root.addHandler(handler)

    # Uvicorn instala sus propios loggers; se alinean con el nivel elegido.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
