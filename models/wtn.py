import dataclasses


@dataclasses.dataclass
class Offer:
    id: str
    name: str
    variant_id: int
    sku: str
    brand: str
    image: str
    size: str
    listing_price: int
    price: int
    createTime: str

    def __post_init__(self):
        self.listing_price = int(self.listing_price)
        self.price = int(self.price)

    def __eq__(self, other):
        if not isinstance(other, Offer):
            return NotImplemented
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return f'Offer(id={self.id}, sku={self.sku}, size={self.size}, price={self.price}'


@dataclasses.dataclass
class Consign:
    brand: str
    name: str
    id: int
    sizes: list[str]
    image: str

    def __eq__(self, other):
        if not isinstance(other, Consign):
            return NotImplemented
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return f'Consign(id={self.id}, sizes={self.sizes})'
