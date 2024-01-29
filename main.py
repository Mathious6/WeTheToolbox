import asyncio

import noble_tls
from colorama import init
from fake_useragent import UserAgent
from noble_tls import Session, Client

from api.consign import ConsignManager
from api.offer import OfferManager
from api.seller import Seller
from utils.config import Config
from utils.log import Log, LogLevel
from utils.proxy import Proxies

init()
logger = Log('Home', LogLevel.DEBUG)


async def main():
    try:
        await noble_tls.update_if_necessary()
    except Exception as e:
        logger.warning(f'Failed to update noble_tls: {e}')
    proxies: Proxies = Proxies()
    config: Config = Config()
    sellers: list[Seller] = []

    for task, account in enumerate(config.accounts, start=1):
        s: Session = Session(client=Client.CHROME_120, random_tls_extension_order=True)
        ua: str = UserAgent().random

        seller: Seller = Seller(proxies, config, s, ua, account, task)
        await seller.init()
        sellers.append(seller)

    async def start_offer(x: Seller):
        offers: OfferManager = OfferManager(x)
        await offers.monitor_offers()

    async def start_consign(x: list[Seller]):
        consigns: ConsignManager = ConsignManager(x)
        await consigns.monitor_consigns()

    offer_tasks = [start_offer(x) for x in sellers]
    await asyncio.gather(start_consign(sellers), *offer_tasks)


if __name__ == '__main__':
    logger.title(
        """
        __        __  _____ _         _____           _ _               
        \ \      / /_|_   _| |__   __|_   _|__   ___ | | |__   _____  __
         \ \ /\ / / _ \| | | '_ \ / _ \| |/ _ \ / _ \| | '_ \ / _ \ \/ /
          \ V  V /  __/| | | | | |  __/| | (_) | (_) | | |_) | (_) >  < 
           \_/\_/ \___||_| |_| |_|\___||_|\___/ \___/|_|_.__/ \___/_/\_\ v1.3        
        """
    )

    print('Welcome to the WTN AIO toolbox coded by @Mathious6')

    asyncio.run(main())
