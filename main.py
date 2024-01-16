import asyncio

import noble_tls
from colorama import init
from fake_useragent import UserAgent
from noble_tls import Session, Client

from api.offer import OfferManager
from api.seller import Seller
from models.wtn import Account
from utils.config import Config
from utils.log import Log, LogLevel
from utils.proxy import Proxies

init()
logger = Log('Home', LogLevel.DEBUG)


async def main():
    await noble_tls.update_if_necessary()
    proxies: Proxies = Proxies()
    config: Config = Config()

    async def handle_account(account: Account, n: int):
        logger.info(f'Starting task {n} for {account.email}')
        s: Session = Session(client=Client.CHROME_120, random_tls_extension_order=True)
        ua: str = UserAgent().random

        seller: Seller = Seller(proxies, config, s, ua, account, n)
        offers: OfferManager = OfferManager(seller)

        await seller.init()
        await offers.monitor_offers()

    tasks = [handle_account(account, task) for task, account in enumerate(config.accounts, start=1)]
    await asyncio.gather(*tasks)


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
