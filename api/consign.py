from asyncio import sleep
from random import randint

from requests import Response

from api.seller import Seller
from models.wtn import Consign, Product
from utils.config import Config
from utils.log import LogLevel, Log
from utils.proxy import Proxies
from utils.webhook import WebHook

logger: Log = Log('Consign', LogLevel.DEBUG)


class ConsignManager:
    URL_CONSIGN_ALL: str = 'https://api-sell.wethenew.com/consignment-slots'

    def __init__(self, proxies: Proxies, config: Config, seller: Seller):
        self.proxies: Proxies = proxies
        self.monitor_delay: int = config.monitor_delay
        self.monitor_timeout: int = config.monitor_timeout
        self.webhook_m = WebHook(config.webhook_monitor)
        self.seller: Seller = seller

        self.consign_seen: set[Consign] = set[Consign]()

    async def monitor_consigns(self) -> None:
        first_run: bool = True
        while True:
            await sleep(self.monitor_delay)
            try:
                params: dict = {
                    'take': '100',
                    'nocache': randint(0, 999999999),
                }

                r: Response = await self.seller.s.get(
                    url=self.URL_CONSIGN_ALL,
                    params=params,
                    proxy=self.proxies.random,
                )

                if r.status_code == 200:
                    current_consigns: set[Consign] = set[Consign]([Consign(
                        brand=result['brand'],
                        name=result['name'],
                        id=result['id'],
                        sizes=result['sizes'],
                        image=result['image'],
                    ) for result in r.json()['results']])

                    if first_run:
                        self.consign_seen = current_consigns
                        first_run = False
                        logger.debug('Initial consigns fetched, monitoring...')
                        continue
                    else:
                        for consign in current_consigns:
                            if consign in self.consign_seen:
                                existing_consign = next((c for c in self.consign_seen if c == consign), None)
                                if existing_consign and existing_consign.sizes != consign.sizes:
                                    added_sizes = set(consign.sizes) - set(existing_consign.sizes)
                                    removed_sizes = set(existing_consign.sizes) - set(consign.sizes)
                                    if added_sizes:
                                        logger.info(f'Consign {consign.id} has added sizes: {added_sizes}')
                                        await self.place_consignment(consign.name, added_sizes)
                                        self.webhook_m.send_consign(consign, added_sizes)
                                    if removed_sizes:
                                        logger.info(f'Consign {consign.id} has removed sizes: {removed_sizes}')
                                    self.consign_seen.remove(existing_consign)
                                    self.consign_seen.add(consign)
                            else:
                                logger.info(f'New consign: {consign}')
                                self.consign_seen.add(consign)
                                self.webhook_m.send_consign(consign, set(consign.sizes))
                        for consign in self.consign_seen - current_consigns:
                            logger.info(f'Consign removed: {consign}')
                            self.consign_seen.remove(consign)
                        cache: str = '' if r.headers['Cf-Cache-Status'] == 'MISS' else ' (cached)'
                        logger.debug(f'Monitoring consigns{cache} [{len(self.consign_seen)} items]')

                else:
                    logger.error(f'Error while fetching offers: {r.status_code}')
                    continue

            except Exception as e:
                if 'Client.Timeout exceeded' in str(e):
                    logger.warning('TLSClientException (timeout), retrying...')
                elif 'Proxy responded with non 200 code' in str(e):
                    logger.warning('Proxy responded with non 200 code, retrying...')
                else:
                    logger.error(f'Error while fetching offers: {e}')

    async def place_consignment(self, name: str, sizes: set[str]) -> None:
        new_products: list[Product] = [Product(name, size) for size in sizes]
        for product in new_products:
            if product in self.seller.listing:
                logger.success(f'{product} is ready to be consigned')
            else:
                logger.error(f'{product} is not in your listing, cannot consign')
