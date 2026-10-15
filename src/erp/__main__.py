"""Entry point: python -m erp."""
from __future__ import annotations

import logging
import os
import sys

from erp.bootstrap import bootstrap

_logger = logging.getLogger(__name__)


def main() -> int:
    try:
        ctx = bootstrap()
        _logger.info("Bootstrap successful. DB path: %s", ctx.db_path)
    except Exception:
        _logger.exception("Bootstrap failed")
        return 1

    # Detecta ambiente headless (GitHub Codespaces)
    if "CODESPACES" in os.environ or not os.environ.get("DISPLAY"):
        _logger.info("Running in headless environment. Skipping UI launch.")
        _logger.info("Run 'uv run pytest' to validate the infrastructure.")
        return 0

    # Lazy import para não carregar PySide6 se não for necessário
    from PySide6 import QtWidgets

    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QMainWindow()
    window.setWindowTitle("ERP")
    window.resize(800, 600)
    window.show()

    _logger.info("ERP started (db=%s)", ctx.db_path)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
