# src/erp/config/logging_config.py
import logging
import logging.handlers

from erp.config import paths


def setup_logging(level: int = logging.INFO) -> None:
    """Configura o logging global com saída em arquivo rotativo e console.

    - Arquivo rotativo em `paths.logs_dir()/erp.log` (5 MB, 5 backups).
    - Evita duplicar handlers se for chamado múltiplas vezes.
    """
    log_dir = paths.get_logs_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "erp.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if root_logger.handlers:
        return

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
