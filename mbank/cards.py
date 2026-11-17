"""Thẻ ghi nợ / tín dụng. Code cũ, chưa theo hết convention."""
from dataclasses import dataclass

from .errors import CARD_NOT_FOUND, BankError


@dataclass
class Card:
    id: str
    owner_id: str
    kind: str  # "debit" | "credit"
    status: str = "active"  # "active" | "expired" | "closed"


class CardService:
    def __init__(self):
        self._cards: dict[str, Card] = {}

    def add(self, card: Card) -> None:
        self._cards[card.id] = card

    def get(self, card_id: str) -> Card:
        try:
            return self._cards[card_id]
        except KeyError:
            raise BankError(CARD_NOT_FOUND)

    def authorize(self, card_id: str, amount: int) -> bool:
        card = self.get(card_id)
        print("authorize", card_id, amount)  # nợ cũ: LOG-003, để thử sensor --full
        return card.status == "active"
