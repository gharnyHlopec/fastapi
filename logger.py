import logging.config
from config import settings
import os
from utils import get_current_strfdatetime

os.makedirs(settings.LOG_DIR, exist_ok=True)


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "file": {
            "format": "[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
        },
        "console": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s [%(asctime)s] %(name)s - %(message)s",
            "use_colors": True,
        },
        "console_access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
            "use_colors": True,
        },
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": str(settings.LOG_DIR / f"log_fastapi_{get_current_strfdatetime()}.log"),
            "formatter": "file",
            "level": "DEBUG",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
            "level": "DEBUG",
        },
        "console_access": {
            "class": "logging.StreamHandler",
            "formatter": "console_access",
            "level": "INFO",
        },
    },
    "loggers": {
        "app": {
            "handlers": ["file", "console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "uvicorn": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["file", "console_access"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)
