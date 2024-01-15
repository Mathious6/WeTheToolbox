import dataclasses
import json
from datetime import datetime

from requests import post

from models.wtn import Offer, Consign, Product
from utils.log import Log, LogLevel

logger: Log = Log('Webhook', LogLevel.DEBUG)


@dataclasses.dataclass
class Footer:
    text: str = 'Wethenew toolbox by @mathious6'
    icon_url: str = 'https://github.githubassets.com/assets/GitHub-Mark-ea2971cee799.png'


@dataclasses.dataclass
class Thumbnail:
    url: str = \
        'https://play-lh.googleusercontent.com/zw5ET1s9lKQo0jw3CisDqglzvIiVvw1X9_tbx1w4VIyoztKYSUb8O6JELPH2AwmEqw'


@dataclasses.dataclass
class Embed:
    title: str = None
    url: str = None
    color: int = None
    fields: list[dict[str, str]] = dataclasses.field(default_factory=list)
    thumbnail: Thumbnail = dataclasses.field(default_factory=Thumbnail)
    footer: Footer = dataclasses.field(default_factory=Footer)


class WebHook:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.webhook_headers = {'Content-Type': 'application/json'}
        self.default_embed = Embed()

    @staticmethod
    def _embed_to_dict(embed: Embed) -> dict:
        embed_dict = dataclasses.asdict(embed)
        embed_dict['footer'] = dataclasses.asdict(embed.footer)
        embed_dict['thumbnail'] = dataclasses.asdict(embed.thumbnail)
        return embed_dict

    def send(self, embed: Embed) -> None:
        embed = embed or self.default_embed
        webhook_data = {'embeds': [self._embed_to_dict(embed)]}

        try:
            post(self.webhook_url, headers=self.webhook_headers, data=json.dumps(webhook_data))
        except Exception as e:
            logger.error(f'Error while sending webhook: {e}')

    def _build_webhook_data(
            self, image: str | None, title: str, color: int, fields: list[dict], pid: int = None
    ) -> dict:
        url: str = 'https://sell.wethenew.com/fr/offers'
        if pid:
            url = f'https://sell.wethenew.com/fr/consignment/product/{pid}'
        return {
            'embeds': [
                {
                    'title': title,
                    'url': url,
                    'thumbnail': {'url': image},
                    'color': color,
                    'fields': fields,
                    'footer': {
                        'text': self.default_embed.footer.text,
                        'icon_url': self.default_embed.footer.icon_url
                    }
                }
            ],
            'username': 'WeTheToolbox',
            'avatar_url': 'https://s3-eu-west-1.amazonaws.com/tpd/logos/5c741846c666770001962f39/0x0.png'
        }

    def _send_webhook(self, webhook_data: dict) -> None:
        try:
            post(self.webhook_url, headers=self.webhook_headers, data=json.dumps(webhook_data))
        except Exception as e:
            logger.error(f'Error while sending webhook: {e}')

    def send_offer(self, offer: Offer) -> None:
        fields: list[dict] = [
            {'name': 'Product', 'value': f'{offer.brand} - {offer.name}', 'inline': False},
            {'name': 'Size', 'value': offer.size, 'inline': True},
            {'name': 'Listing Price', 'value': f'{offer.listing_price}€', 'inline': True},
            {'name': 'Offer Price', 'value': f'{offer.price}€', 'inline': True},
            {'name': 'Created', 'value': offer.createTime, 'inline': False},
        ]
        webhook_data: dict = self._build_webhook_data(offer.image, f'New offer found [{offer.sku}] 🔎', 0xC8DEDC, fields)
        self._send_webhook(webhook_data)

    def send_accept_offer(self, offer: Offer) -> None:
        fields: list[dict] = [
            {'name': 'Product', 'value': f'{offer.brand} - {offer.name}', 'inline': False},
            {'name': 'Size', 'value': offer.size, 'inline': True},
            {'name': 'Sale Price', 'value': f'{offer.price}€', 'inline': True},
            {'name': 'Price Diff', 'value': f'{offer.price - offer.listing_price}€', 'inline': True},
            {'name': 'Accepted', 'value': datetime.utcnow().isoformat()[:-3] + 'Z', 'inline': False},
        ]
        webhook_data: dict = self._build_webhook_data(offer.image, f'Offer accepted [{offer.sku}] 🎉', 0xA0E062, fields)
        self._send_webhook(webhook_data)

    def send_refuse_offer(self, offer: Offer) -> None:
        fields: list[dict] = [
            {'name': 'Product', 'value': f'{offer.brand} - {offer.name}', 'inline': False},
            {'name': 'Size', 'value': offer.size, 'inline': True},
            {'name': 'Offer Price', 'value': f'{offer.price}€', 'inline': True},
            {'name': 'Price Diff', 'value': f'{offer.price - offer.listing_price}€', 'inline': True},
            {'name': 'Refused', 'value': datetime.utcnow().isoformat()[:-3] + 'Z', 'inline': False},
        ]
        webhook_data: dict = self._build_webhook_data(offer.image, f'Offer refused [{offer.sku}] ❌', 0xFF0000, fields)
        self._send_webhook(webhook_data)

    def send_consign(self, consign: Consign, added_sizes: set[str]) -> None:
        if not self.webhook_url:
            logger.debug('Webhook URL is None, not sending webhook')
            return
        updated_sizes: list[str] = []
        for size in consign.sizes:
            if size in added_sizes:
                updated_sizes.append('**' + size + '**')
            else:
                updated_sizes.append('' + size)

        fields: list[dict] = [
            {
                'name': 'Sizes',
                'value': '\n'.join(updated_sizes),
                'inline': False
            },
        ]
        webhook_data: dict = self._build_webhook_data(
            consign.image, f'{consign.brand} - {consign.name} 🔎', 0x000000, fields, consign.id
        )
        self._send_webhook(webhook_data)

    def send_accept_consign(self, product: Product) -> None:
        fields: list[dict] = [
            {'name': 'Product', 'value': f'{product.name}', 'inline': False},
            {'name': 'Size', 'value': product.size, 'inline': True},
            {'name': 'Consignment Price', 'value': f'{product.price}€', 'inline': True},
        ]
        webhook_data: dict = self._build_webhook_data(None, 'Consignment placed 🎉', 0xA0E062, fields)
        self._send_webhook(webhook_data)
