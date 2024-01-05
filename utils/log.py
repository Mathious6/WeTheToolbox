import traceback
from datetime import datetime

from colorama import Fore, Style


class LogLevel:
    DEBUG: int = 0
    INFO: int = 1
    SUCCESS: int = 2
    WARNING: int = 3
    ERROR: int = 4
    CRITICAL: int = 5


class Log:
    COLORS = {
        LogLevel.DEBUG: Fore.WHITE,
        LogLevel.INFO: Fore.LIGHTWHITE_EX,
        LogLevel.SUCCESS: Fore.GREEN,
        LogLevel.WARNING: Fore.YELLOW,
        LogLevel.ERROR: Fore.RED,
        LogLevel.CRITICAL: Fore.LIGHTRED_EX
    }

    def __init__(self, name: str, level: int = LogLevel.DEBUG):
        self.name: str = name.upper()
        self.level: int = level

    def _log(self, level: int, message: str, task_number: int = None, line_before: int = 0, line_after: int = 0):
        if self.level <= level:
            print() if line_before else None
            timestamp = datetime.now().strftime('%H:%M:%S.%f')
            task_str = f"[{task_number}] " if task_number is not None else ""
            color = self.COLORS.get(level, Fore.WHITE)
            print(f'{color}[{timestamp}] [{self.name}] {task_str}{message}{Style.RESET_ALL}')
            print() if line_after else None

    def title(self, message: str, line_before: int = 0, line_after: int = 0):
        if self.level <= LogLevel.INFO:
            print() if line_before else None
            print(f"{Fore.BLUE}{message}{Style.RESET_ALL}")
            print() if line_after else None

    def debug(self, message: str, task_number: int = None, line_before: int = 0, line_after: int = 0):
        self._log(LogLevel.DEBUG, message, task_number, line_before, line_after)

    def info(self, message: str, task_number: int = None, line_before: int = 0, line_after: int = 0):
        self._log(LogLevel.INFO, message, task_number, line_before, line_after)

    def success(self, message: str, task_number: int = None, line_before: int = 0, line_after: int = 0):
        self._log(LogLevel.SUCCESS, message, task_number, line_before, line_after)

    def warning(self, message: str, task_number: int = None, line_before: int = 0, line_after: int = 0):
        self._log(LogLevel.WARNING, message, task_number, line_before, line_after)

    def error(self, message: str, task_number: int = None, line_before: int = 0, line_after: int = 0):
        self._log(LogLevel.ERROR, message, task_number, line_before, line_after)

    def critical(self, message: str, task_number: int = None, line_before: int = 0, line_after: int = 0):
        self._log(LogLevel.CRITICAL, message, task_number, line_before, line_after)

    def exception(self):
        if self.level <= LogLevel.DEBUG:
            print(f'{Fore.RED}{traceback.format_exc()}{Style.RESET_ALL}')
