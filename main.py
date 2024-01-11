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
    await noble_tls.update_if_necessary()

    s: Session = Session(client=Client.CHROME_120, random_tls_extension_order=True)
    ua: str = UserAgent().random

    proxies: Proxies = Proxies()
    config: Config = Config()

    seller: Seller = Seller(s, proxies, config, ua)
    offers: OfferManager = OfferManager(proxies, config, seller)
    consigns: ConsignManager = ConsignManager(proxies, config, seller)

    async def start_mode(mode):
        mode_actions: dict = {
            0: (offers.monitor_offers(), consigns.monitor_consigns()),
            1: (offers.monitor_offers(),),
            2: (consigns.monitor_consigns(),)
        }

        actions = mode_actions.get(mode)
        if actions:
            logger.info(f'Starting mode {mode}: {" + ".join(action.__name__ for action in actions)}')
            await asyncio.gather(*actions)
        else:
            logger.error(f'Invalid mode: {mode}')

    await start_mode(config.mode)


if __name__ == '__main__':
    logger.title(
        """
        __        __  _____ _         _____           _ _               
        \ \      / /_|_   _| |__   __|_   _|__   ___ | | |__   _____  __
         \ \ /\ / / _ \| | | '_ \ / _ \| |/ _ \ / _ \| | '_ \ / _ \ \/ /
          \ V  V /  __/| | | | | |  __/| | (_) | (_) | | |_) | (_) >  < 
           \_/\_/ \___||_| |_| |_|\___||_|\___/ \___/|_|_.__/ \___/_/\_\ v1.1         
        """
    )

    print('Welcome to the WTN AIO toolbox coded by @Mathious6')

    asyncio.run(main())
