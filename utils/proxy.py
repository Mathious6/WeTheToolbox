import sys
from random import choice

from utils.log import Log, LogLevel

logger = Log('Proxy', LogLevel.DEBUG)


class Proxy:
    def __init__(self, hostname: str, port: int, username: str = None, password: str = None):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.validate_proxy()

    def validate_proxy(self):
        if not self.hostname or not isinstance(self.port, int):
            raise ValueError(f'Hostname or port is invalid: {self.hostname}:{self.port}')
        if not 1 <= self.port <= 65535:
            raise ValueError(f'Port is invalid: {self.port}')

    def get_proxy(self) -> dict[str, str]:
        auth: str = f'{self.username}:{self.password}' if self.username and self.password else ''
        return {
            'http': f'http://{auth}@{self.hostname}:{str(self.port)}',
            'https': f'https://{auth}@{self.hostname}:{str(self.port)}'
        }

    def __str__(self):
        return f'Proxy(hostname={self.hostname}, port={self.port}, username={self.username}, password={self.password})'


class Proxies:
    def __init__(self, path: str = 'proxies.txt'):
        self.path = path
        self.proxies = self.read_auth()

    def read_auth(self) -> list[Proxy]:
        proxies: list[Proxy] = []
        with open(file=self.path, mode='r', encoding='utf-8') as f:
            for line in f.readlines():
                proxy_parts: list[str] = line.strip().split(':')
                if len(proxy_parts) == 4:
                    hostname, port, username, password = proxy_parts
                    try:
                        port: int = int(port)
                        proxies.append(Proxy(hostname, port, username, password))
                    except ValueError:
                        logger.warning(f'Invalid proxy port: {line}')
                        continue
                else:
                    logger.warning(f'Invalid proxy: {line}')
        logger.info(f'Loaded {len(proxies)} proxies', line_before=1)
        return proxies

    @property
    def random(self) -> dict[str, str]:
        if self.proxies:
            return choice(self.proxies).get_proxy()
        else:
            logger.error('No proxies available')
            sys.exit(1)
