"""Tail no bloqueante de un archivo de logs.

Se comporta como ``tail -f``: por defecto empieza al final del archivo y
entrega solo las líneas nuevas. También tolera dos casos habituales en
producción:

* **truncado** (``logrotate`` con ``copytruncate``): detecta que el tamaño
  bajó y vuelve al inicio;
* **rotación** (cambio de inodo): cierra el descriptor viejo y lee el archivo
  nuevo desde el principio.
"""

from __future__ import annotations

import os
from pathlib import Path


class LogTailer:
    """Lee líneas completas de un archivo conforme se agregan."""

    def __init__(
        self,
        path: str | Path,
        *,
        from_start: bool = False,
        encoding: str = "utf-8",
    ) -> None:
        self.path = Path(path)
        self.from_start = from_start
        self.encoding = encoding
        self._file = None
        self._inode: int | None = None
        self._ever_opened = False
        self._appeared_after_start = False

    def __enter__(self) -> "LogTailer":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        """Cierra el descriptor abierto, si existe."""
        if self._file is not None:
            self._file.close()
            self._file = None
        self._inode = None

    def read_available(self) -> list[str]:
        """Devuelve las líneas completas disponibles desde la última lectura."""
        if not self._prepare_file():
            return []

        assert self._file is not None
        lines: list[str] = []
        while True:
            position = self._file.tell()
            line = self._file.readline()
            if not line:
                break
            if not line.endswith("\n"):
                # Línea a medio escribir: se reintenta en el próximo sondeo.
                self._file.seek(position)
                break
            lines.append(line.rstrip("\r\n"))
        return lines

    # ------------------------------------------------------------------
    # Manejo del descriptor
    # ------------------------------------------------------------------
    def _prepare_file(self) -> bool:
        """Abre o reabre el archivo si hace falta; ``False`` si no existe."""
        try:
            stat = self.path.stat()
        except FileNotFoundError:
            # Durante una rotación el archivo puede desaparecer un instante.
            self.close()
            self._appeared_after_start = True
            return False

        if self._file is None:
            seek_to_end = (
                not self.from_start
                and not self._ever_opened
                and not self._appeared_after_start
            )
            self._open(seek_to_end=seek_to_end)
            return True

        if stat.st_ino != self._inode:
            # Rotación: el archivo nuevo se procesa desde el principio.
            self._open(seek_to_end=False)
        elif stat.st_size < self._file.tell():
            # Truncado in-place.
            self._file.seek(0)

        return True

    def _open(self, *, seek_to_end: bool) -> None:
        self.close()
        self._file = self.path.open("r", encoding=self.encoding, errors="replace")
        self._ever_opened = True
        if seek_to_end:
            self._file.seek(0, os.SEEK_END)
        self._inode = os.fstat(self._file.fileno()).st_ino
