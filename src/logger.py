from datetime import datetime
from typing import Optional

class Logger:
    COLORS = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "gray": "\033[90m",
        None: ""
    }
    RESET = "\033[0m"

    @staticmethod
    def print(text: str, color: Optional[str] = None) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color_code = Logger.COLORS.get(color, "")
        reset_code = Logger.RESET if color_code else ""
        print(f"{color_code}[{timestamp}] {text}{reset_code}")
