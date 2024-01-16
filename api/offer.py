from asyncio import sleep
from random import randint

from noble_tls import Session
from requests import Response

from api.seller import Seller
from models.wtn import Offer
from utils.log import Log
from utils.proxy import Proxies
from utils.webhook import WebHook

URL_OFFERS: str = 'https://api-sell.wethenew.com/offers'


class OfferManager:
    def __init__(self, seller: Seller):
        self.log: Log = Log('Offer', seller.log_level, task_number=seller.log.task_number)

        self.s: Session = seller.s
        self.proxies: Proxies = seller.proxies
        self.delay: float = seller.delay
        self.webhook_s: WebHook = WebHook(seller.webhook_s)

        self.seller = seller

    async def monitor_offers(self) -> None:
        while True:
            await sleep(self.delay)
            try:
                params: dict = {'take': '100', 'nocache': randint(0, 999999999)}
                r: Response = await self.s.get(url=URL_OFFERS, params=params, proxy=self.proxies.random)

                if r.status_code == 200:
                    data: dict = r.json()
                    if not data.get('results'):
                        self.log.debug('No new offers found, monitoring...')
                    else:
                        results: list = data['results']
                        for result in results:
                            offer: Offer = Offer(
                                id=result['id'],
                                name=result['name'],
                                variant_id=result['variantId'],
                                sku=result['sku'],
                                brand=result['brand'],
                                image=result['image'],
                                size=result['europeanSize'],
                                listing_price=result['listingPrice'],
                                price=result['price'],
                                createTime=result['createTime'],
                            )

                            self.log.success(f'New offer found: {offer}')
                            is_acceptable: bool = offer.price >= offer.listing_price - self.seller.price_delta
                            await self._accept_offer(offer) if is_acceptable else await self._refuse_offer(offer)

                elif r.status_code == 401:
                    self.log.warning('Seller token expired, refreshing...')
                    await self.seller.init()
                else:
                    self.log.error(f'Error while fetching offers: {r.status_code}')
                    continue

            except Exception as e:
                if 'Client.Timeout exceeded' in str(e):
                    self.log.warning('TLSClientException (timeout), retrying...')
                elif 'Proxy responded with non 200 code' in str(e):
                    self.log.warning('Proxy responded with non 200 code, retrying...')
                else:
                    self.log.error(f'Error while fetching offers: {e}')

    async def _accept_offer(self, offer: Offer) -> None:
        try:
            self.log.info(f'Accepting offer {offer.id} ...')
            json: dict = {'name': offer.id, 'status': 'ACCEPTED', 'variantId': offer.variant_id}
            r: Response = await self.seller.s.post(URL_OFFERS, json=json, proxy=self.proxies.random)

            if r.status_code == 201:
                self.log.success(f'Offer {offer.id} accepted!')
                self.webhook_s.send_accept_offer(offer)
            else:
                self.log.error(f'Error while accepting offer {offer.id}: {r.status_code}')
        except Exception as e:
            self.log.error(f'Error while accepting offer {offer.id}: {e}')

    async def _refuse_offer(self, offer: Offer) -> None:
        try:
            self.log.info(f'Refusing offer {offer.id} ...')
            json: dict = {
                'name': offer.id,
                'status': 'REFUSED_PRICE_DISAGREEMENT',
                'newListingPrice': offer.listing_price,
                'variantId': offer.variant_id
            }
            r: Response = await self.seller.s.post(URL_OFFERS, json=json, proxy=self.proxies.random)
            if r.status_code == 201:
                self.log.success(f'Offer {offer.id} refused!')
                self.webhook_s.send_refuse_offer(offer)
            else:
                self.log.error(f'Error while refusing offer {offer.id}: {r.status_code}')
        except Exception as e:
            self.log.error(f'Error while refusing offer {offer.id}: {e}')
