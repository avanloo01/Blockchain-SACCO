"""Abstract payment provider interface.

Every adapter must implement these methods so command handlers stay
provider-agnostic. The normalized PaymentIntent response schema is the
contract between providers and the rest of the application.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class PaymentStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass(frozen=True)
class PaymentIntent:
    """Normalized response returned by every provider."""
    intent_id: str
    member_id: str
    amount_usd: float
    service_fee_usd: float
    net_pool_amount_usd: float
    asset: str
    network: str
    status: PaymentStatus
    recipient_address: str
    memo: str | None = None
    payment_url: str | None = None


@dataclass(frozen=True)
class SettlementResult:
    """Normalized verification result."""
    intent_id: str
    status: PaymentStatus
    tx_signature: str | None = None
    settled_amount: float | None = None
    error: str | None = None


class PaymentProvider(ABC):
    """Contract that every payment adapter must satisfy."""

    @abstractmethod
    def create_payment_intent(
        self,
        amount_usd: float,
        member_id: str,
        idempotency_key: str | None = None,
    ) -> PaymentIntent:
        """Build a payment intent with transfer instructions for the member."""

    @abstractmethod
    def verify_payment_settlement(
        self,
        intent_id: str,
        tx_signature: str,
    ) -> SettlementResult:
        """Check whether a transaction has settled on-chain."""
