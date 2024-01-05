# Bypassing reCaptcha v3: https://github.com/xHossein/PyPasser
from pypasser import reCaptchaV3
from pypasser.structs import Proxy as ProxyPypasser

from utils.proxy import Proxy


class ReCaptchaV3:
    def __init__(self, anchor_url: str, timeout: int = 10, proxy: Proxy = None):
        self.anchor_url: str = anchor_url
        self.timeout: int = timeout
        self.proxy: ProxyPypasser = ProxyPypasser(
            ProxyPypasser.type.HTTPs,
            proxy.hostname,
            str(proxy.port),
            proxy.username,
            proxy.password
        ) if proxy else None

    def solve(self) -> reCaptchaV3:
        return reCaptchaV3(anchor_url=self.anchor_url, timeout=self.timeout, proxy=self.proxy)
