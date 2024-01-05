from asyncio import sleep

from noble_tls import Session
from requests import Response

from utils.captcha import ReCaptchaV3
from utils.config import Config
from utils.log import Log, LogLevel
from utils.proxy import Proxies

logger = Log('Seller', LogLevel.DEBUG)
RECAPTCHAV3_ANCHOR = ('https://www.google.com/recaptcha/api2/anchor?ar=1&k=6LeJBSAdAAAAACyoWxmCY7q5G-_6GnKBdpF4raee&co'
                      '=aHR0cHM6Ly9zZWxsLndldGhlbmV3LmNvbTo0NDM.&hl=en&v=u-xcq3POCWFlCr3x8_IPxgPu&size=invisible&cb'
                      '=k30rgwzggens')


class Seller:
    CSRF_URL: str = 'https://sell.wethenew.com/api/auth/csrf'
    CRED_URL: str = 'https://sell.wethenew.com/api/auth/callback/credentials'
    SESSION_URL: str = 'https://sell.wethenew.com/api/auth/session'
    PROFILE_URL: str = 'https://api-sell.wethenew.com/sellers/me'

    def __init__(self, session: Session, proxies: Proxies, config: Config, ua: str):
        self.s: Session = session
        self.proxies: Proxies = proxies
        self.config: Config = config
        self.csrf_token: str | None = None
        self.access_token: str | None = None

        self.s.headers['content-type'] = 'application/json'
        self.s.headers['user-agent'] = ua
        self.s.timeout_seconds = config.monitor_timeout

    async def refresh_token(self) -> Session:
        self.csrf_token: str = await self._get_csrf_token()
        self.access_token: str = await self._get_access_token()
        await self._login()
        return self.s

    async def _retry_with_delay(self, func, max_attempds: int) -> any:
        for attempt in range(max_attempds):
            try:
                await sleep(self.config.monitor_delay)
                return await func()
            except Exception as e:
                if 'Client.Timeout exceeded' in str(e):
                    logger.warning('TLSClientException (timeout), retrying...')
                elif 'Proxy responded with non 200 code' in str(e):
                    logger.warning('Proxy responded with non 200 code, retrying...')
                else:
                    logger.error(f'Error while fetching offers: {e}')

                logger.debug(f'Retrying ({attempt + 1}/{max_attempds})')
        logger.error('Maximun attempts reached, failed to execute the operation')
        return None

    async def _get_csrf_token(self) -> str | None:
        async def attempt_fetch():
            r: Response = await self.s.get(url=self.CSRF_URL, proxy=self.proxies.random)
            if r.status_code == 200 and 'csrfToken' in r.json():
                logger.success('Successfully retrieved csrfToken')
                return r.json()['csrfToken']
            raise Exception(f'Failed to retrieve csrfToken, status code: {r.status_code}')

        return await self._retry_with_delay(attempt_fetch, 5)

    async def _get_access_token(self) -> str | None:
        async def attempt_fetch():
            data: dict = {
                'redirect': 'false',
                'email': self.config.wtn_email,
                'password': self.config.wtn_password,
                'recaptchaToken': ReCaptchaV3(RECAPTCHAV3_ANCHOR, 5).solve(),
                'pushToken': 'undefined',
                'os': 'undefined',
                'osVersion': 'undefined',
                'csrfToken': self.csrf_token,
                'callbackUrl': 'https://sell.wethenew.com/login',
                'json': 'true'
            }

            r: Response = await self.s.post(url=self.CRED_URL, json=data, proxy=self.proxies.random)
            if r.status_code != 200:
                raise Exception(f'Failed to post credentials, status code: {r.status_code}')

            r: Response = await self.s.get(url=self.SESSION_URL, proxy=self.proxies.random)
            if r.status_code == 200 and r.json().get('user').get('accessToken'):
                logger.success('Successfully retrieved accessToken token')
                return r.json().get('user').get('accessToken')
            raise Exception('Failed to retrieve accessToken token')

        return await self._retry_with_delay(attempt_fetch, 5)

    async def _login(self) -> None:
        async def attempt_login():
            self.s.headers['authorization'] = f'Bearer {self.access_token}'
            r: Response = await self.s.get(url=self.PROFILE_URL, proxy=self.proxies.random)
            if r.status_code == 200:
                logger.success(f'Logged in as {r.json().get("firstname")}')
                return
            raise Exception(f'Failed to login, status code: {r.status_code}')

        return await self._retry_with_delay(attempt_login, 5)
