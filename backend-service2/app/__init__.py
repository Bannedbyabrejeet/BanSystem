"""Servicio 2 de Bannedbyabrejeet: lector de logs SSH y motor de seguridad.

El paquete expone tres piezas independientes y testeables:

* :mod:`app.parser` — convierte líneas de ``auth.log`` en eventos SSH.
* :mod:`app.engine` — aplica whitelist, ventana ``findtime`` y umbral.
* :mod:`app.tailer` / :mod:`app.monitor` — lectura continua del archivo.

La ejecución del firewall (UFW) queda fuera del alcance de esta entrega.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "1.0.0"
