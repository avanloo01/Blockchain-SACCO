"""Tests for the payment provider interface and Solana testnet adapter."""

import uuid
from unittest.mock import MagicMock, patch

from src.services.payments.base import PaymentIntent, PaymentStatus, SettlementResult
from src.services.payments.solana_testnet import SolanaTestnetProvider


@patch("src.services.payments.solana_testnet.settings")
def test_create_payment_intent_builds_solana_pay_url(mock_settings):
    mock_settings.service_fee_percent = 1.0
    mock_settings.solana_treasury_address = "TreasuryABC123"

    provider = SolanaTestnetProvider()
    intent = provider.create_payment_intent(amount_usd=25.0, member_id="chat-42")

    assert isinstance(intent, PaymentIntent)
    assert intent.amount_usd == 25.0
    assert intent.service_fee_usd == 0.25
    assert intent.net_pool_amount_usd == 24.75
    assert intent.asset == "USDC"
    assert intent.network == "solana_devnet"
    assert intent.status == PaymentStatus.PENDING
    assert intent.recipient_address == "TreasuryABC123"
    assert "solana:TreasuryABC123" in intent.payment_url
    assert "amount=25.0" in intent.payment_url
    assert intent.memo.startswith("sacco:")


@patch("src.services.payments.solana_testnet.settings")
def test_create_payment_intent_uses_idempotency_key(mock_settings):
    mock_settings.service_fee_percent = 1.0
    mock_settings.solana_treasury_address = "TreasuryABC123"

    provider = SolanaTestnetProvider()
    key = "my-idem-key"
    intent = provider.create_payment_intent(
        amount_usd=10.0, member_id="chat-1", idempotency_key=key
    )
    assert intent.intent_id == key


@patch("src.services.payments.solana_testnet.settings")
def test_create_payment_intent_raises_without_treasury(mock_settings):
    mock_settings.service_fee_percent = 1.0
    mock_settings.solana_treasury_address = ""

    provider = SolanaTestnetProvider()
    try:
        provider.create_payment_intent(amount_usd=10.0, member_id="chat-1")
        assert False, "Should have raised ValueError"
    except ValueError as exc:
        assert "SOLANA_TREASURY_ADDRESS" in str(exc)


@patch("src.services.payments.solana_testnet.requests.post")
@patch("src.services.payments.solana_testnet.settings")
def test_verify_confirmed_transaction(mock_settings, mock_post):
    mock_settings.solana_rpc_url = "https://api.devnet.solana.com"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "jsonrpc": "2.0",
        "result": {
            "meta": {"err": None},
            "slot": 12345,
        },
    }
    mock_post.return_value = mock_resp

    provider = SolanaTestnetProvider()
    result = provider.verify_payment_settlement(
        intent_id="intent-1", tx_signature="sig123"
    )

    assert isinstance(result, SettlementResult)
    assert result.status == PaymentStatus.CONFIRMED
    assert result.tx_signature == "sig123"


@patch("src.services.payments.solana_testnet.requests.post")
@patch("src.services.payments.solana_testnet.settings")
def test_verify_pending_transaction(mock_settings, mock_post):
    mock_settings.solana_rpc_url = "https://api.devnet.solana.com"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"jsonrpc": "2.0", "result": None}
    mock_post.return_value = mock_resp

    provider = SolanaTestnetProvider()
    result = provider.verify_payment_settlement(
        intent_id="intent-1", tx_signature="sig456"
    )

    assert result.status == PaymentStatus.PENDING


@patch("src.services.payments.solana_testnet.requests.post")
@patch("src.services.payments.solana_testnet.settings")
def test_verify_failed_transaction(mock_settings, mock_post):
    mock_settings.solana_rpc_url = "https://api.devnet.solana.com"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "jsonrpc": "2.0",
        "result": {
            "meta": {"err": {"InstructionError": [0, "Custom"]}},
        },
    }
    mock_post.return_value = mock_resp

    provider = SolanaTestnetProvider()
    result = provider.verify_payment_settlement(
        intent_id="intent-1", tx_signature="sig789"
    )

    assert result.status == PaymentStatus.FAILED
    assert result.error is not None


@patch("src.services.payments.solana_testnet.settings")
def test_verify_without_rpc_url(mock_settings):
    mock_settings.solana_rpc_url = ""

    provider = SolanaTestnetProvider()
    result = provider.verify_payment_settlement(
        intent_id="intent-1", tx_signature="sig000"
    )

    assert result.status == PaymentStatus.FAILED
    assert "SOLANA_RPC_URL" in result.error
