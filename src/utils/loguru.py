import logging
import logging.config
import logging.handlers
import os
import re
from colorama import Fore, Back, Style, init

init(autoreset=True)

LOG_COLORS = {
    logging.DEBUG: Fore.BLACK + Style.BRIGHT,
    logging.INFO: Fore.GREEN,
    logging.WARNING: Fore.YELLOW,
    logging.ERROR: Fore.RED,
    logging.CRITICAL: Back.RED + Fore.WHITE,
}

CLI_LOG_FORMAT = (
    f"{Fore.BLACK + Style.BRIGHT}[%(asctime)s]{Style.RESET_ALL}"
    f"{Fore.CYAN}>{Style.RESET_ALL} $RESET%(levelname).1s: %(message)s{Style.RESET_ALL}"
)
CLI_TIME_FORMAT = "%d-%m-%Y %H:%M:%S"

FILE_LOG_FORMAT = "[%(asctime)s][%(filename)s:%(lineno)d]> %(levelname).1s: %(message)s"
FILE_TIME_FORMAT = "%H:%M:%S"

CLEAR_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")


def add_colors(text: str) -> str:
    colors = {
        "$YELLOW": Fore.YELLOW,
        "$CYAN": Fore.CYAN,
        "$MAGENTA": Fore.MAGENTA,
        "$BLUE": Fore.BLUE,
        "$GREEN": Fore.GREEN,
        "$BLACK": Fore.BLACK,
        "$WHITE": Fore.WHITE,
        "$B_YELLOW": Back.YELLOW,
        "$B_CYAN": Back.CYAN,
        "$B_MAGENTA": Back.MAGENTA,
        "$B_BLUE": Back.BLUE,
        "$B_GREEN": Back.GREEN,
        "$B_BLACK": Back.BLACK,
        "$B_WHITE": Back.WHITE,
    }
    for key, color in colors.items():
        text = text.replace(key, color)
    return text


# ---------------- CLI formatter ----------------
class CLILoggerFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        msg = record.getMessage()
        msg = add_colors(msg)

        color = LOG_COLORS.get(record.levelno, "")
        msg = msg.replace("$RESET", color)

        record.msg = msg
        record.args = ()  # 🔥 ОБЯЗАТЕЛЬНО

        fmt = CLI_LOG_FORMAT.replace(
            "$RESET", Style.RESET_ALL + color
        )
        formatter = logging.Formatter(fmt, CLI_TIME_FORMAT)
        return formatter.format(record)


# ---------------- File formatter ----------------
class FileLoggerFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        msg = record.getMessage()
        msg = CLEAR_RE.sub("", msg)

        record.msg = msg
        record.args = ()  # 🔥 ОБЯЗАТЕЛЬНО

        formatter = logging.Formatter(FILE_LOG_FORMAT, FILE_TIME_FORMAT)
        return formatter.format(record)


# ---------------- CONFIG ----------------
LOGGER_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "cli_handler": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "cli_formatter",
        },
        "file_handler": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": "DEBUG",
            "formatter": "file_formatter",
            "filename": "logs/log.log",
            "when": "midnight",
            "encoding": "utf-8",
        },
    },
    "formatters": {
        "cli_formatter": {
            "()": "src.utils.loguru.CLILoggerFormatter"
        },
        "file_formatter": {
            "()": "src.utils.loguru.FileLoggerFormatter"
        },
    },
    "loggers": {
        "TGBot": {
            "handlers": ["cli_handler", "file_handler"],
            "level": "DEBUG",
            "propagate": False,
        },
        "aiogram": {
            "handlers": ["cli_handler", "file_handler"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {  # добавляем root
        "handlers": ["cli_handler", "file_handler"],
        "level": "DEBUG",
    }
}


def setup_logging() -> logging.Logger:
    os.makedirs("logs", exist_ok=True)
    logging.config.dictConfig(LOGGER_CONFIG)
    return logging.getLogger("TGBot")
