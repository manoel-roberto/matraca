"""Script de automação de build dos binários do Matraca Desktop com PyInstaller (RF-15, CI/CD)."""

from __future__ import annotations

import sys
from pathlib import Path

import customtkinter
import PyInstaller.__main__


def main() -> None:
    root_dir = Path(__file__).resolve().parent
    ctk_path = Path(customtkinter.__file__).parent

    # No Windows o separador do --add-data é ';', no Linux/macOS é ':'
    sep = ";" if sys.platform == "win32" else ":"
    ctk_data_arg = f"{ctk_path}{sep}customtkinter/"
    toml_path = root_dir / "matraca" / "extractors" / "concursos_patterns.toml"
    toml_data_arg = f"{toml_path}{sep}matraca/extractors/"

    args = [
        "--clean",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name",
        "matraca-desktop",
        "--add-data",
        ctk_data_arg,
        "--add-data",
        toml_data_arg,
        "--hidden-import",
        "customtkinter",
        "--hidden-import",
        "PIL",
        "--hidden-import",
        "PIL.Image",
        "--hidden-import",
        "edge_tts",
        "--hidden-import",
        "fitz",
        "--hidden-import",
        "mutagen",
        "--hidden-import",
        "num2words",
        str(root_dir / "app_desktop.py"),
    ]

    print("Executando build do executável stand-alone...")
    print(f"Argumentos: {' '.join(args)}")
    PyInstaller.__main__.run(args)

    dist_dir = root_dir / "dist"
    binary_name = "matraca-desktop.exe" if sys.platform == "win32" else "matraca-desktop"
    out_file = dist_dir / binary_name
    if out_file.exists():
        size_mb = out_file.stat().st_size / (1024 * 1024)
        print(f"Build concluído com sucesso: {out_file} ({size_mb:.2f} MB)")
    else:
        print(f"Aviso: arquivo {out_file} não encontrado após build.")


if __name__ == "__main__":
    main()
