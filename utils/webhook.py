import dataclasses
import json

from requests import post

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

    def send_offer(self, offer) -> None:
        try:
            webhook_data = {
                'embeds': [
                    {
                        'title': f'New offer found [{offer.sku}] 🔎',
                        'url': 'https://sell.wethenew.com/fr/offers',
                        'thumbnail': {'url': offer.image},
                        'color': 0xC8DEDC,
                        'fields': [
                            {'name': 'Product', 'value': f'{offer.brand} - {offer.name}\n\u200b', 'inline': False},
                            {'name': 'Size', 'value': offer.size, 'inline': True},
                            {'name': 'Listing Price', 'value': f'{offer.listing_price}€', 'inline': True},
                            {'name': 'Offer Price', 'value': f'{offer.price}€\n\u200b', 'inline': True},
                            {'name': 'Created', 'value': offer.createTime, 'inline': False},
                        ],
                        'footer': {
                            'text': self.default_embed.footer.text,
                            'icon_url': self.default_embed.footer.icon_url
                        }
                    }
                ]
            }

            post(self.webhook_url, headers=self.webhook_headers, data=json.dumps(webhook_data))
        except Exception as e:
            print(str(e))
