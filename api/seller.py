import sys
from asyncio import sleep

from noble_tls import Session
from requests import Response

from models.wtn import Product, Account
from utils.captcha import ReCaptchaV3
from utils.config import Config
from utils.log import Log
from utils.proxy import Proxies

CSRF_URL: str = 'https://sell.wethenew.com/api/auth/csrf'
CRED_URL: str = 'https://sell.wethenew.com/api/auth/callback/credentials'
SESSION_URL: str = 'https://sell.wethenew.com/api/auth/session'
PROFILE_URL: str = 'https://api-sell.wethenew.com/sellers/me'
LISTING_URL: str = 'https://api-sell.wethenew.com/listings'
PAYMENT_URL: str = 'https://api-sell.wethenew.com/payment-infos'
SHIPPING_URL: str = 'https://api-sell.wethenew.com/addresses?type=shipping'
C3_ANCHOR: str = (
    'https://www.google.com/recaptcha/api2/anchor?ar=1&k=6LfbSlUpAAAAABNgkya850A9AtuIxEzJtv5V5cO5&co='
    'aHR0cHM6Ly9zZWxsLndldGhlbmV3LmNvbTo0NDM.&hl=en&v=Ya-Cd6PbRI5ktAHEhm9JuKEu&size=invisible&cb=gpdfxohtm66a'
)


class Seller:

    def __init__(self, proxies: Proxies, config: Config, session: Session, ua: str, account: Account, n: int):
        self.log: Log = Log('Seller', config.log_level, task_number=n)

        self.s: Session = session
        self.s.headers['content-type'] = 'application/json'
        self.s.headers['user-agent'] = ua
        self.s.timeout_seconds = int(config.monitor_timeout)

        self.proxies: Proxies = proxies
        self.delay: float = config.monitor_delay
        self.webhook_s = config.webhook_success
        self.webhook_r = config.webhook_refused
        self.webhook_m = config.webhook_monitor
        self.log_level: int = config.log_level

        self.email: str = account.email
        self.password: str = account.password
        self.price_delta: int = account.price_delta

        self.csrf_token: str | None = None
        self.access_token: str | None = None
        self.address_uuid: str | None = None
        self.payment_uuid: str | None = None
        self.first_name: str | None = None

        self.listing: list[Product] | None = None

    async def init(self) -> Session | None:
        self.csrf_token = await self._get_csrf_token()
        self.access_token = await self._get_access_token()
        self.first_name = await self._login()
        self.listing = await self._get_listing()
        self.address_uuid, self.payment_uuid = await self._get_uuids()

        self.log.info(f'Logged in as {self.first_name}, {len(self.listing)} products in listing, ready to sell!')
        return self.s

    async def _retry_with_delay(self, func, max_attempts: int) -> any:
        for attempt in range(max_attempts):
            try:
                await sleep(self.delay)
                return await func()
            except Exception as e:
                if 'Client.Timeout exceeded' in str(e):
                    self.log.warning('TLSClientException (timeout), retrying...')
                elif 'Proxy responded with non 200 code' in str(e):
                    self.log.warning('Proxy responded with non 200 code, retrying...')
                else:
                    self.log.error(f'Error while executing {func.__name__}: {e}')

                self.log.debug(f'Retrying ({attempt + 1}/{max_attempts})')
        self.log.error('Maximum attempts reached, failed to execute the operation')
        sys.exit(1)

    async def _get_csrf_token(self) -> str | None:
        async def attempt_fetch():
            r: Response = await self.s.get(url=CSRF_URL, proxy=self.proxies.random)
            if r.status_code == 200 and 'csrfToken' in r.json():
                self.log.debug('Successfully retrieved csrfToken')
                return r.json()['csrfToken']
            raise Exception(f'Failed to retrieve csrfToken, status code: {r.status_code}')

        return await self._retry_with_delay(attempt_fetch, 5)

    async def _get_access_token(self) -> str | None:
        async def attempt_fetch():
            data: dict = {
                'redirect': 'false',
                'email': self.email,
                'password': self.password,
                'recaptchaToken': ReCaptchaV3(C3_ANCHOR, 5).solve(),
                'pushToken': 'undefined',
                'os': 'undefined',
                'osVersion': 'undefined',
                'csrfToken': self.csrf_token,
                'callbackUrl': 'https://sell.wethenew.com/login',
                'json': 'true'
            }

            r: Response = await self.s.post(url=CRED_URL, json=data, proxy=self.proxies.random)
            if r.status_code != 200:
                raise Exception(f'Failed to post credentials, status code: {r.status_code}')

            r: Response = await self.s.get(url=SESSION_URL, proxy=self.proxies.random)
            if r.status_code == 200 and r.json().get('user').get('accessToken'):
                self.log.debug('Successfully retrieved accessToken token')
                return r.json().get('user').get('accessToken')
            raise Exception('Failed to retrieve accessToken token')

        return await self._retry_with_delay(attempt_fetch, 5)

    async def _login(self) -> str:
        async def attempt_login():
            self.s.headers['authorization'] = f'Bearer {self.access_token}'
            r: Response = await self.s.get(url=PROFILE_URL, proxy=self.proxies.random)
            if r.status_code == 200:
                firstname: str = r.json().get('firstname')
                self.log.debug(f'Logged in as {firstname}')
                return firstname
            raise Exception(f'Failed to login, status code: {r.status_code}')

        return await self._retry_with_delay(attempt_login, 5)

    async def _get_listing(self) -> list[Product] | None:
        async def attempt_fetch():
            listing: list[Product] = []
            skip: int = 0
            while True:
                params: dict = {'take': 100, 'skip': skip}
                r: Response = await self.s.get(url=LISTING_URL, proxy=self.proxies.random, params=params)
                if r.status_code != 200:
                    raise Exception(f'Failed to fetch listing, status code: {r.status_code}')

                results: list = r.json().get('results', [])
                if not results:
                    break

                listing.extend(
                    [
                        Product(
                            id=result['name'],
                            name=result['product']['name'],
                            image=result['product']['image'],
                            size=result['product']['europeanSize'],
                            price=result['price'],
                        ) for result in results
                    ]
                )
                skip += 100

            self.log.debug(f'Successfully fetched {len(listing)} products from listing')
            return listing

        return await self._retry_with_delay(attempt_fetch, 5)

    async def _get_uuids(self) -> tuple[str, str] | None:
        async def attempt_fetch():
            r: Response = await self.s.get(url=PAYMENT_URL, proxy=self.proxies.random)
            if r.status_code != 200:
                raise Exception(f'Failed to fetch uuids, status code: {r.status_code}')
            payment_uuid: str = r.json()[0].get('uuid')

            r: Response = await self.s.get(url=SHIPPING_URL, proxy=self.proxies.random)
            if r.status_code != 200:
                raise Exception(f'Failed to fetch uuids, status code: {r.status_code}')
            address_uuid: str = r.json().get('uuid')

            if not address_uuid or not payment_uuid:
                raise Exception('Failed to fetch uuids')

            self.log.debug('Successfully fetched uuids')
            return address_uuid, payment_uuid

        return await self._retry_with_delay(attempt_fetch, 5)
