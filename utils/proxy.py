import sys
from random import choice

from utils.log import Log, LogLevel

logger = Log('Proxy', LogLevel.DEBUG)


class Proxy:
    def __init__(self, hostname: str, port: int, username: str = None, password: str = None, protocol: str = 'http'):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.protocol = protocol
        self.validate_proxy()

    def validate_proxy(self):
        if not self.hostname or not isinstance(self.port, int):
            raise ValueError(f'Hostname or port is invalid: {self.hostname}:{self.port}')
        if not 1 <= self.port <= 65535:
            raise ValueError(f'Port is invalid: {self.port}')

    def get_proxy(self) -> dict[str, str]:
        auth: str = f'{self.username}:{self.password}@' if self.username and self.password else ''
        proxy_protocol = self.protocol if self.protocol in ['http', 'socks4', 'socks5'] else 'http'
        proxy_url = f'{proxy_protocol}://{auth}{self.hostname}:{self.port}'

        return {'http': proxy_url, 'https': proxy_url}

    def __str__(self):
        return (
            f'Proxy('
            f'hostname={self.hostname}, '
            f'port={self.port}, '
            f'username={self.username}, '
            f'password={self.password}), '
            f'protocol={self.protocol}'
        )


class Proxies:
    def __init__(self, path: str = 'proxies.txt'):
        self.path = path
        self.proxies = self.read()

    def read(self) -> list[Proxy]:
        proxies: list[Proxy] = []
        with open(file=self.path, mode='r', encoding='utf-8') as f:
            for line in f.readlines():
                proxy_parts: list[str] = line.strip().split(':')
                try:
                    if len(proxy_parts) in [2, 3, 4, 5]:
                        hostname = proxy_parts[0]
                        port = int(proxy_parts[1])
                        username = proxy_parts[2] if len(proxy_parts) > 3 else None
                        password = proxy_parts[3] if len(proxy_parts) > 4 else None
                        protocol = proxy_parts[-1] if len(proxy_parts) in [3, 5] else None
                        proxies.append(Proxy(hostname, port, username, password, protocol))
                    else:
                        raise ValueError("Invalid proxy format")
                except ValueError as e:
                    logger.warning(f'{e}: {line.strip()}')
        if len(proxies) == 0:
            logger.error('No proxies found', line_before=1)
            sys.exit(1)

        logger.info(f'Loaded {len(proxies)} proxies', line_before=1)
        return proxies

    @property
    def random(self) -> dict[str, str]:
        if self.proxies:
            return choice(self.proxies).get_proxy()
        else:
            logger.error('No proxies available')
            sys.exit(1)
