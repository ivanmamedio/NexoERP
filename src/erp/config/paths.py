import os

from platformdirs import user_data_dir

APP_NAME = "ERP_Pequenos_Comercios"
APP_AUTHOR = "OpenSource"


def get_data_dir() -> str:
    path = user_data_dir(APP_NAME, APP_AUTHOR)
    os.makedirs(path, exist_ok=True)
    return path


def get_logs_dir() -> str:
    path = os.path.join(get_data_dir(), "logs")
    os.makedirs(path, exist_ok=True)
    return path
