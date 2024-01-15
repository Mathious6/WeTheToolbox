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
    URL_PLACE_CONSIGN: str = 'https://api-sell.wethenew.com/consignments'

    def __init__(self, proxies: Proxies, config: Config, seller: Seller):
        self.proxies: Proxies = proxies
        self.monitor_delay: int = config.monitor_delay
        self.monitor_timeout: int = config.monitor_timeout
        self.webhook_m = WebHook(config.webhook_monitor)
        self.webhook_s = WebHook(config.webhook_success)
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
                                        await self.place_consignment(consign.name, consign.id, added_sizes)
                                        self.webhook_m.send_consign(consign, added_sizes)
                                    if removed_sizes:
                                        logger.info(f'Consign {consign.id} has removed sizes: {removed_sizes}')
                                    self.consign_seen.remove(existing_consign)
                                    self.consign_seen.add(consign)
                            else:
                                logger.info(f'New consign: {consign}')
                                await self.place_consignment(consign.name, consign.id, set(consign.sizes))
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

    async def place_consignment(self, name: str, c_id: int, sizes: set[str]) -> None:
        new_products: list[Product] = [Product(name, size) for size in sizes]
        for product in new_products:
            if product in self.seller.listing:
                url_product: str = f'https://api-sell.wethenew.com/products/{c_id}/consignments'
                try:
                    r: Response = await self.seller.s.get(
                        url=url_product,
                        proxy=self.proxies.random,
                    )

                    if r.status_code != 200:
                        logger.error(f'Error while fetching consignments: {r.status_code}')
                        continue

                    v_id: int = next((v['id'] for v in r.json()['variants'] if v['europeanSize'] == product.size), None)

                    for p in self.seller.listing:
                        if p == product:
                            product.image = p.image
                            product.price = p.price
                            product.id = p.id
                            break

                    json_data: dict = {
                        'consignments': [
                            {
                                'quantity': 1,
                                'variantId': v_id,
                                'price': product.price,
                                'paymentOptionType': 'STANDARD',
                            },
                        ],
                        'paymentInfoUuid': self.seller.payment_uuid,
                        'addressUuid': self.seller.address_uuid,
                        'isTermsAndConditionsAccepted': True,
                        'isDepositConditionsAccepted': True,
                    }
                    r: Response = await self.seller.s.post(
                        url=self.URL_PLACE_CONSIGN,
                        json=json_data,
                        proxy=self.proxies.random,
                    )

                    if r.status_code == 201:
                        logger.success(f'Consigned {product}')
                        await self.delete_listing(product)
                        self.webhook_s.send_accept_consign(product)
                    else:
                        logger.error(f'Error while consigning {product}: {r.status_code}')

                except Exception as e:
                    logger.error(f'Error while consigning {product}: {e}')

            else:
                logger.debug(f'{product} is not in your listing, cannot consign')

    async def delete_listing(self, product: Product) -> None:
        try:
            url_product: str = f'https://api-sell.wethenew.com/listings/{product.id}'
            r: Response = await self.seller.s.delete(
                url=url_product,
                proxy=self.proxies.random,
            )
            if r.status_code != 200:
                await sleep(self.monitor_delay)
                await self.delete_listing(product)
        except Exception as e:
            logger.error(f'Error while deleting {product}: {e}')
