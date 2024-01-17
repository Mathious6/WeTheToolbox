from asyncio import sleep
from random import randint

from noble_tls import Session
from requests import Response

from api.seller import Seller
from models.wtn import Consign, Product
from utils.log import Log
from utils.proxy import Proxies
from utils.webhook import WebHook

URL_CONSIGN_ALL: str = 'https://api-sell.wethenew.com/consignment-slots'
URL_PLACE_CONSIGN: str = 'https://api-sell.wethenew.com/consignments'


class ConsignManager:

    def __init__(self, sellers: list[Seller]):
        self.sellers: list[Seller] = sellers
        r_seller: Seller = sellers[randint(0, len(sellers) - 1)]

        self.log: Log = Log('Consign', r_seller.log_level)

        self.s: Session = r_seller.s
        self.proxies: Proxies = r_seller.proxies
        self.delay: float = r_seller.delay
        self.webhook_m: WebHook = WebHook(r_seller.webhook_m)
        self.webhook_s: WebHook = WebHook(r_seller.webhook_s)

        self.consign_seen: set[Consign] = set[Consign]()

    async def monitor_consigns(self) -> None:
        first_run: bool = True
        while True:
            await sleep(self.delay)
            try:
                params: dict = {'take': '100', 'nocache': randint(0, 999999999)}
                r: Response = await self.s.get(url=URL_CONSIGN_ALL, params=params, proxy=self.proxies.random)

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
                        self.log.debug('Initial consigns fetched, monitoring...')
                        continue
                    else:
                        for consign in current_consigns:
                            if consign in self.consign_seen:
                                existing_consign = next((c for c in self.consign_seen if c == consign), None)
                                if existing_consign and existing_consign.sizes != consign.sizes:
                                    added_sizes = set(consign.sizes) - set(existing_consign.sizes)
                                    removed_sizes = set(existing_consign.sizes) - set(consign.sizes)
                                    if added_sizes:
                                        self.log.info(f'New size: {consign}')
                                        await self._place_consignment(consign.name, consign.id, added_sizes)
                                        self.webhook_m.send_consign(consign, added_sizes)
                                    if removed_sizes:
                                        self.log.debug(f'Deleted size: {consign}')
                                    self.consign_seen.remove(existing_consign)
                                    self.consign_seen.add(consign)
                            else:
                                self.log.info(f'New consign: {consign}')
                                await self._place_consignment(consign.name, consign.id, set(consign.sizes))
                                self.consign_seen.add(consign)
                                self.webhook_m.send_consign(consign, set(consign.sizes))
                        for consign in self.consign_seen - current_consigns:
                            self.log.debug(f'Consign removed: {consign}')
                            self.consign_seen.remove(consign)

                        cache: str = '' if r.headers['Cf-Cache-Status'] == 'MISS' else ' (cached)'
                        self.log.debug(f'Monitoring consigns{cache} [{len(self.consign_seen)} items]')

                else:
                    self.log.error(f'Error while monitoring consigns: {r.status_code}')
                    continue

            except Exception as e:
                if 'Client.Timeout exceeded' in str(e):
                    self.log.warning('TLSClientException (timeout), retrying...')
                elif 'Proxy responded with non 200 code' in str(e):
                    self.log.warning('Proxy responded with non 200 code, retrying...')
                else:
                    self.log.error(f'Error while monitoring consigns: {e}')

    async def _place_consignment(self, name: str, c_id: int, sizes: set[str]) -> None:
        new_products: list[Product] = [Product(name, size) for size in sizes]
        for product in new_products:
            for seller in self.sellers:
                s_log: Log = Log(f'Consign', seller.log_level, seller.log.task_number)
                if product in seller.listing:
                    url_product: str = f'https://api-sell.wethenew.com/products/{c_id}/consignments'
                    try:
                        r: Response = await seller.s.get(url=url_product, proxy=self.proxies.random)
                        if r.status_code != 200:
                            s_log.error(f'Error while fetching consignments: {r.status_code}')
                            continue

                        v_id: int = next(
                            (v['id'] for v in r.json()['variants'] if v['europeanSize'] == product.size),
                            None
                        )

                        for p in seller.listing:
                            if p == product:
                                product.brand = p.brand
                                product.image = p.image
                                product.price = p.price
                                product.id = p.id
                                break

                        data: dict = {
                            'consignments': [
                                {
                                    'quantity': 1,
                                    'variantId': v_id,
                                    'price': product.price,
                                    'paymentOptionType': 'STANDARD',
                                },
                            ],
                            'paymentInfoUuid': seller.payment_uuid,
                            'addressUuid': seller.address_uuid,
                            'isTermsAndConditionsAccepted': True,
                            'isDepositConditionsAccepted': True,
                        }
                        r: Response = await seller.s.post(url=URL_PLACE_CONSIGN, json=data, proxy=self.proxies.random)
                        if r.status_code == 201:
                            s_log.success(f'Consigned {product}')
                            await self._delete_listing(seller, product)
                            self.webhook_s.send_accept_consign(product)
                        else:
                            s_log.error(f'Error while consigning {product}: {r.status_code}')

                    except Exception as e:
                        s_log.error(f'Error while consigning {product}: {e}')
                else:
                    s_log.debug(f'{product} is not in your listing, cannot consign')

    async def _delete_listing(self, seller: Seller, product: Product) -> None:
        try:
            url_product: str = f'https://api-sell.wethenew.com/listings/{product.id}'
            r: Response = await seller.s.delete(url=url_product, proxy=self.proxies.random)
            if r.status_code != 200:
                await sleep(self.delay)
                await self._delete_listing(seller, product)
        except Exception as e:
            self.log.error(f'Error while deleting listing {product}: {e}')
