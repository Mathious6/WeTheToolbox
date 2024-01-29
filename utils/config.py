import csv
import os
import sys

from dotenv import load_dotenv

from models.wtn import Account
from utils.log import Log, LogLevel

load_dotenv()
logger = Log('Config', LogLevel.DEBUG)


class Config:
    def __init__(self):
        self.monitor_delay: float = 5
        self.monitor_timeout: float = 10
        self.webhook_success: str | None = None
        self.webhook_refused: str | None = None
        self.webhook_monitor: str | None = None
        self.log_level: int = 0

        self.accounts: list[Account] = []

        self.get_env()

    @staticmethod
    def get_env_variable(var_name: str, is_secret: bool = False, optional: bool = False) -> str | None:
        value: str = os.getenv(var_name)
        if value is None or value == '':
            if optional:
                return None
            logger.error(f'Missing environment variable: {var_name}')
            sys.exit(1)
        if is_secret:
            logger.info(f'{var_name}: {"*" * len(value)}')
        else:
            logger.info(f'{var_name}: {value}')
        return value

    @staticmethod
    def get_accounts(path: str) -> list[Account]:
        accounts: list[Account] = []
        try:
            with open(path, 'r') as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    accounts.append(Account(row[0], row[1], int(row[2])))
            logger.info(f'Loaded {len(accounts)} accounts from {path}')
            return accounts
        except FileNotFoundError as e:
            logger.error(f'Error in get_csv_variable: {e}')
            logger.exception()
            sys.exit(1)

    def get_env(self):
        try:
            self.monitor_delay: float = float(self.get_env_variable('MONITOR_DELAY'))
            self.monitor_timeout: float = float(self.get_env_variable('MONITOR_TIMEOUT'))
            self.webhook_success: str = self.get_env_variable('WEBHOOK_SUCCESS')
            self.webhook_monitor: str = self.get_env_variable('WEBHOOK_REFUSED', optional=True)
            self.webhook_monitor: str = self.get_env_variable('WEBHOOK_MONITOR', optional=True)
            self.log_level: int = int(self.get_env_variable('LOG_LEVEL', optional=True) or 0)

            self.accounts = self.get_accounts('accounts.csv')

            print()
        except ValueError as e:
            logger.error(f'Error in get_env: {e}')
            logger.exception()
            sys.exit(1)
