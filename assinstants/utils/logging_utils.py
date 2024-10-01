import logging
from colorama import Fore, Style, init

init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    COLORS = {
        "THREAD": Fore.CYAN,
        "ASSISTANT": Fore.MAGENTA,
        "STEP": Fore.YELLOW,
        "FUNCTION": Fore.GREEN,
        "ERROR": Fore.RED,
    }

    def format(self, record):
        if not record.msg.startswith(tuple(self.COLORS.keys())):
            return logging.Formatter.format(self, record)

        category, message = record.msg.split(":", 1)
        color = self.COLORS.get(category, "")
        record.msg = f"{color}{category}:{Style.RESET_ALL}{message}"
        return logging.Formatter.format(self, record)


logger = logging.getLogger("assinstants")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter("%(message)s"))
logger.addHandler(handler)


def set_logging(enabled: bool):
    logger.disabled = not enabled


def log(category: str, message: str, level: int = logging.INFO):
    logger.log(level, f"{category}: {message}")
