"""Servicio 2 de Bannedbyabrejeet: motor SSH, UFW y workers de baneo.

Piezas principales:

* :mod:`app.parser` — convierte líneas de ``auth.log`` en eventos SSH.
* :mod:`app.engine` — aplica whitelist, ventana ``findtime`` y umbral.
* :mod:`app.tailer` / :mod:`app.monitor` — lectura continua del archivo.
* :mod:`app.ufw` — ejecuta reglas de bloqueo/desbloqueo en UFW.
* :mod:`app.bans` — ciclo de vida del baneo en UFW y Redis.
* :mod:`app.unban_worker` — consume órdenes manuales del stream.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "1.0.0"
