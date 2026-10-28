"""Pruebas del tail no bloqueante y de la rotación de archivos."""

from __future__ import annotations

from pathlib import Path

from app.tailer import LogTailer


def append(path: Path, text: str) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)


def test_from_start_reads_existing_lines(tmp_path: Path) -> None:
    path = tmp_path / "auth.log"
    path.write_text("old-1\nold-2\n", encoding="utf-8")

    with LogTailer(path, from_start=True) as tailer:
        assert tailer.read_available() == ["old-1", "old-2"]


def test_default_mode_only_reads_new_lines(tmp_path: Path) -> None:
    path = tmp_path / "auth.log"
    path.write_text("old\n", encoding="utf-8")

    with LogTailer(path) as tailer:
        assert tailer.read_available() == []
        append(path, "new\n")
        assert tailer.read_available() == ["new"]


def test_partial_line_waits_for_newline(tmp_path: Path) -> None:
    path = tmp_path / "auth.log"
    path.write_text("", encoding="utf-8")

    with LogTailer(path, from_start=True) as tailer:
        append(path, "linea-a-medias")
        assert tailer.read_available() == []

        append(path, "\nsegunda\n")
        assert tailer.read_available() == ["linea-a-medias", "segunda"]


def test_truncated_file_is_read_from_the_beginning(tmp_path: Path) -> None:
    path = tmp_path / "auth.log"
    path.write_text("linea-larga\n", encoding="utf-8")

    with LogTailer(path, from_start=True) as tailer:
        assert tailer.read_available() == ["linea-larga"]
        path.write_text("x\n", encoding="utf-8")
        assert tailer.read_available() == ["x"]


def test_rotated_file_is_reopened_by_inode(tmp_path: Path) -> None:
    path = tmp_path / "auth.log"
    path.write_text("viejo\n", encoding="utf-8")

    with LogTailer(path, from_start=True) as tailer:
        assert tailer.read_available() == ["viejo"]
        rotated = tmp_path / "auth.log.1"
        path.rename(rotated)
        path.write_text("nuevo\n", encoding="utf-8")
        assert tailer.read_available() == ["nuevo"]


def test_missing_file_is_waited_and_then_read_from_start(tmp_path: Path) -> None:
    path = tmp_path / "auth.log"

    with LogTailer(path) as tailer:
        assert tailer.read_available() == []
        path.write_text("primera\n", encoding="utf-8")
        assert tailer.read_available() == ["primera"]
