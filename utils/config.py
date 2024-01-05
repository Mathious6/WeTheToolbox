import os
import sys

from dotenv import load_dotenv

from utils.log import Log, LogLevel

load_dotenv()
logger = Log('Config', LogLevel.DEBUG)


class Config:
    def __init__(self):
        self.monitor_delay: int | None = None
        self.monitor_timeout: int | None = None
        self.webhook_url: str | None = None
        self.wtn_email: str | None = None
        self.wtn_password: str | None = None
        self.get_env()

    @staticmethod
    def get_env_variable(var_name: str, is_secret: bool = False) -> str:
        value: str = os.getenv(var_name)
        if value is None:
            logger.error(f'Missing environment variable: {var_name}')
            sys.exit(1)
        if is_secret:
            logger.info(f'{var_name}: {"*" * len(value)}')
        else:
            logger.info(f'{var_name}: {value}')
        return value

    def get_env(self):
        try:
            self.monitor_delay: int = int(self.get_env_variable('MONITOR_DELAY'))
            self.monitor_timeout: int = int(self.get_env_variable('MONITOR_TIMEOUT'))
            self.webhook_url: str = self.get_env_variable('WEBHOOK_URL')
            self.wtn_email: str = self.get_env_variable('WETHENEW_EMAIL')
            self.wtn_password: str = self.get_env_variable('WETHENEW_PASSWORD', is_secret=True)
            print()
        except ValueError as e:
            logger.error(f'Error in get_env: {e}')
            logger.exception()
            sys.exit(1)
