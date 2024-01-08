from asyncio import sleep

from requests import Response

from api.seller import Seller
from models.wtn import Offer
from utils.config import Config
from utils.log import Log, LogLevel
from utils.proxy import Proxies
from utils.webhook import WebHook

logger: Log = Log('Offer', LogLevel.DEBUG)


class OfferManager:
    URL_OFFERS: str = 'https://api-sell.wethenew.com/offers'

    def __init__(self, proxies: Proxies, config: Config, seller: Seller):
        self.proxies: Proxies = proxies
        self.price_delta: int = config.price_delta
        self.monitor_delay: int = config.monitor_delay
        self.monitor_timeout: int = config.monitor_timeout
        self.webhook = WebHook(config.webhook_url)
        self.seller: Seller = seller

        self.offers_seen: set[Offer] = set[Offer]()

        self.params: dict = {
            'take': '100'
        }

    async def monitor_offers(self) -> None:
        while True:
            await sleep(self.monitor_delay)
            try:
                r: Response = await self.seller.s.get(
                    url=self.URL_OFFERS,
                    params=self.params,
                    proxy=self.proxies.random,
                )

                if r.status_code == 200:
                    data: dict = r.json()
                    if not data.get('results'):
                        logger.debug('No new offers found, monitoring...')
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
                            logger.success(f'New offer found: {offer}')
                            if offer not in self.offers_seen:
                                is_acceptable: bool = offer.price >= offer.listing_price - self.price_delta
                                await self.accept_offer(offer) if is_acceptable else await self.refuse_offer(offer)

                                self.offers_seen.add(offer)
                                self.webhook.send_offer(offer)

                elif r.status_code == 401:
                    logger.warning('Seller token expired, refreshing...')
                    await self.seller.refresh_token()
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

    async def accept_offer(self, offer: Offer) -> None:
        json: dict = {
            'name': offer.id,
            'status': 'ACCEPTED',
            'variantId': offer.variant_id,
        }

        logger.info(f'Accepting offer {offer.id} ...')
        r: Response = await self.seller.s.post(self.URL_OFFERS, json=json, proxy=self.proxies.random)

        if r.status_code == 201:
            logger.success(f'Offer {offer.id} accepted!')
            self.webhook.send_accept_offer(offer)
        else:
            logger.error(f'Error while accepting offer {offer.id}: {r.status_code}')

    async def refuse_offer(self, offer: Offer) -> None:
        json: dict = {
            'name': offer.id,
            'status': 'REFUSED_PRICE_DISAGREEMENT',
            'newListingPrice': offer.listing_price,
            'variantId': offer.variant_id,
        }

        logger.info(f'Refusing offer {offer.id} ...')
        r: Response = await self.seller.s.post(self.URL_OFFERS, json=json, proxy=self.proxies.random)

        if r.status_code == 201:
            logger.success(f'Offer {offer.id} refused!')
            self.webhook.send_refuse_offer(offer)
        else:
            logger.error(f'Error while refusing offer {offer.id}: {r.status_code}')
