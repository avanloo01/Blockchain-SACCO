"""Tests for the payment provider interface and Solana testnet adapter."""

import uuid
from unittest.mock import MagicMock, patch

from src.services.payments.base import PaymentIntent, PaymentStatus, SettlementResult
from src.services.payments.crossmint import CrossmintProvider
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


# ── Crossmint provider tests ────────────────────────────────────────


@patch("src.services.payments.crossmint.requests.put")
@patch("src.services.payments.crossmint.requests.post")
@patch("src.services.payments.crossmint.settings")
def test_crossmint_create_payment_intent(mock_settings, mock_post, mock_put):
    mock_settings.service_fee_percent = 1.0
    mock_settings.crossmint_server_api_key = "server_key_123"
    mock_settings.crossmint_wallet_address = "TreasuryWallet123"
    mock_settings.crossmint_token_locator = "solana:4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"
    mock_settings.website_url = "https://blockchainsacco.com"
    mock_settings.app_env = "dev"

    mock_link_resp = MagicMock()
    mock_link_resp.ok = True
    mock_put.return_value = mock_link_resp

    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {
        "clientSecret": "client_secret_123",
        "order": {"orderId": "order-123"},
    }
    mock_post.return_value = mock_resp

    provider = CrossmintProvider()
    intent = provider.create_payment_intent(
        amount_usd=25.0,
        member_id="chat-42",
        receipt_email="member@example.com",
    )

    assert isinstance(intent, PaymentIntent)
    assert intent.intent_id == "order-123"
    assert intent.amount_usd == 25.0
    assert intent.service_fee_usd == 0.25
    assert intent.net_pool_amount_usd == 24.75
    assert intent.asset == "USDC"
    assert intent.network == "solana"
    assert intent.status == PaymentStatus.PENDING
    assert intent.recipient_address == "TreasuryWallet123"
    assert "/checkout/crossmint" in intent.payment_url
    assert "orderId=order-123" in intent.payment_url
    assert "clientSecret=client_secret_123" in intent.payment_url
    payload = mock_post.call_args.kwargs["json"]
    assert payload["recipient"]["walletAddress"] == "TreasuryWallet123"
    assert payload["payment"]["method"] == "card"
    assert payload["payment"]["receiptEmail"] == "member@example.com"
    assert isinstance(payload["lineItems"], list)
    assert payload["lineItems"][0]["tokenLocator"] == mock_settings.crossmint_token_locator
    assert payload["lineItems"][0]["executionParameters"]["mode"] == "exact-in"
    assert payload["lineItems"][0]["executionParameters"]["amount"] == "25.00"
    assert "slippageBps" not in payload["lineItems"][0]["executionParameters"]
    # Wallet link should have been called before the order was created
    assert mock_put.called
    link_call_kwargs = mock_put.call_args.kwargs
    assert link_call_kwargs["json"]["chain"] == "solana"


@patch("src.services.payments.crossmint.settings")
def test_crossmint_create_intent_raises_without_server_key(mock_settings):
    mock_settings.crossmint_server_api_key = ""
    mock_settings.crossmint_wallet_address = "TreasuryWallet123"
    mock_settings.crossmint_token_locator = "solana:EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    mock_settings.service_fee_percent = 1.0

    provider = CrossmintProvider()
    try:
        provider.create_payment_intent(
            amount_usd=10.0,
            member_id="chat-1",
            receipt_email="member@example.com",
        )
        assert False, "Should have raised ValueError"
    except ValueError as exc:
        assert "CROSSMINT_SERVER_API_KEY" in str(exc)


@patch("src.services.payments.crossmint.settings")
def test_crossmint_create_intent_raises_without_recipient_email_config(mock_settings):
    mock_settings.crossmint_server_api_key = "server_key_123"
    mock_settings.crossmint_wallet_address = ""
    mock_settings.crossmint_token_locator = "solana:EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    mock_settings.service_fee_percent = 1.0

    provider = CrossmintProvider()
    try:
        provider.create_payment_intent(
            amount_usd=10.0,
            member_id="chat-1",
            receipt_email="member@example.com",
        )
        assert False, "Should have raised ValueError"
    except ValueError as exc:
        assert "CROSSMINT_WALLET_ADDRESS" in str(exc)


@patch("src.services.payments.crossmint.settings")
def test_crossmint_create_intent_raises_without_receipt_email(mock_settings):
    mock_settings.crossmint_server_api_key = "server_key_123"
    mock_settings.crossmint_wallet_address = "TreasuryWallet123"
    mock_settings.crossmint_token_locator = "solana:EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    mock_settings.service_fee_percent = 1.0

    provider = CrossmintProvider()
    try:
        provider.create_payment_intent(amount_usd=10.0, member_id="chat-1")
        assert False, "Should have raised ValueError"
    except ValueError as exc:
        assert "missing an email address" in str(exc)


@patch("src.services.payments.crossmint.requests.get")
@patch("src.services.payments.crossmint.settings")
def test_crossmint_verify_completed_order(mock_settings, mock_get):
    mock_settings.crossmint_server_api_key = "server_key_123"
    mock_settings.app_env = "dev"

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "orderId": "order-123",
        "phase": "completed",
        "payment": {"status": "completed"},
        "lineItems": [{"delivery": {"status": "completed", "txId": "tx-123"}}],
    }
    mock_get.return_value = mock_resp

    provider = CrossmintProvider()
    result = provider.verify_payment_settlement(
        intent_id="intent-1", tx_signature="order-123"
    )

    assert result.status == PaymentStatus.CONFIRMED
    assert result.tx_signature == "tx-123"


@patch("src.services.payments.crossmint.requests.get")
@patch("src.services.payments.crossmint.settings")
def test_crossmint_verify_pending_order(mock_settings, mock_get):
    mock_settings.crossmint_server_api_key = "server_key_123"
    mock_settings.app_env = "dev"

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "orderId": "order-456",
        "phase": "payment",
        "payment": {"status": "awaiting-payment"},
        "lineItems": [{"delivery": {"status": "awaiting-payment"}}],
    }
    mock_get.return_value = mock_resp

    provider = CrossmintProvider()
    result = provider.verify_payment_settlement(
        intent_id="intent-1", tx_signature="order-456"
    )

    assert result.status == PaymentStatus.PENDING


@patch("src.services.payments.crossmint.requests.get")
@patch("src.services.payments.crossmint.settings")
def test_crossmint_verify_failed_order(mock_settings, mock_get):
    mock_settings.crossmint_server_api_key = "server_key_123"
    mock_settings.app_env = "dev"

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "orderId": "order-789",
        "phase": "payment",
        "payment": {"status": "failed-kyc"},
        "lineItems": [{"delivery": {"status": "awaiting-payment"}}],
    }
    mock_get.return_value = mock_resp

    provider = CrossmintProvider()
    result = provider.verify_payment_settlement(
        intent_id="intent-1", tx_signature="order-789"
    )

    assert result.status == PaymentStatus.FAILED
    assert "failed-kyc" in result.error


@patch("src.services.payments.crossmint.settings")
def test_crossmint_verify_without_server_key(mock_settings):
    mock_settings.crossmint_server_api_key = ""

    provider = CrossmintProvider()
    result = provider.verify_payment_settlement(
        intent_id="intent-1", tx_signature="order-000"
    )

    assert result.status == PaymentStatus.FAILED
    assert "CROSSMINT_SERVER_API_KEY" in result.error
