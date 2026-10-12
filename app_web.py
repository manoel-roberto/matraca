"""Ponto de entrada da aplicação Web Streamlit (python app_web.py ou streamlit run app_web.py)."""

from __future__ import annotations

import sys
from pathlib import Path

from matraca.web.streamlit_app import main


def run() -> None:
    """Executa a aplicação no navegador via Streamlit CLI ou diretamente se já em runtime."""
    try:
        import streamlit.runtime as st_runtime
        from streamlit.web import cli as stcli

        if not st_runtime.exists():
            sys.argv = ["streamlit", "run", str(Path(__file__).resolve()), *sys.argv[1:]]
            sys.exit(stcli.main())
    except (ImportError, AttributeError):
        pass

    main()


if __name__ == "__main__":
    run()
