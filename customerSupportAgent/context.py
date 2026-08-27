from dataclasses import dataclass, field
import secrets


@dataclass
class PendingCheckout:
    product_id: int
    quantity: int
    address_id: int
    idempotency_key: str = field(
        default_factory=lambda: secrets.token_urlsafe(24)
    )


@dataclass
class SupportContext:
    customer_id: int
    pending_checkout: PendingCheckout | None = None