"""Tests for the payment provider interface and Solana testnet adapter."""

import uuid
from unittest.mock import MagicMock, patch

from src.services.payments.base import PaymentIntent, PaymentStatus, SettlementResult
from src.services.payments.moonpay import MoonpayProvider
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


# ── MoonPay provider tests ──────────────────────────────────────────


@patch("src.services.payments.moonpay.settings")
def test_moonpay_create_payment_intent(mock_settings):
    mock_settings.service_fee_percent = 1.0
    mock_settings.app_env = "prod"
    mock_settings.moonpay_api_key = "pk_test_123"
    mock_settings.moonpay_wallet_address = "TreasuryWallet123"
    mock_settings.moonpay_currency_code = "usdc_sol"
    mock_settings.moonpay_network = "solana"

    provider = MoonpayProvider()
    intent = provider.create_payment_intent(amount_usd=25.0, member_id="chat-42")

    assert isinstance(intent, PaymentIntent)
    assert intent.amount_usd == 25.0
    assert intent.service_fee_usd == 0.25
    assert intent.net_pool_amount_usd == 24.75
    assert intent.asset == "USDC_SOL"
    assert intent.network == "solana"
    assert intent.status == PaymentStatus.PENDING
    assert intent.recipient_address == "TreasuryWallet123"
    assert "buy.moonpay.com" in intent.payment_url
    assert "apiKey=pk_test_123" in intent.payment_url
    assert "baseCurrencyAmount=25.0" in intent.payment_url


@patch("src.services.payments.moonpay.settings")
def test_moonpay_create_intent_uses_idempotency_key(mock_settings):
    mock_settings.service_fee_percent = 1.0
    mock_settings.app_env = "prod"
    mock_settings.moonpay_api_key = "pk_test_123"
    mock_settings.moonpay_wallet_address = "TreasuryWallet123"
    mock_settings.moonpay_currency_code = "usdc_sol"
    mock_settings.moonpay_network = "solana"

    provider = MoonpayProvider()
    key = "my-idem-key"
    intent = provider.create_payment_intent(
        amount_usd=10.0, member_id="chat-1", idempotency_key=key
    )
    assert intent.intent_id == key
    assert f"externalTransactionId={key}" in intent.payment_url


@patch("src.services.payments.moonpay.settings")
def test_moonpay_create_intent_raises_without_api_key(mock_settings):
    mock_settings.moonpay_api_key = ""
    mock_settings.moonpay_wallet_address = "TreasuryWallet123"
    mock_settings.service_fee_percent = 1.0

    provider = MoonpayProvider()
    try:
        provider.create_payment_intent(amount_usd=10.0, member_id="chat-1")
        assert False, "Should have raised ValueError"
    except ValueError as exc:
        assert "MOONPAY_API_KEY" in str(exc)


@patch("src.services.payments.moonpay.settings")
def test_moonpay_create_intent_raises_without_wallet(mock_settings):
    mock_settings.moonpay_api_key = "pk_test_123"
    mock_settings.moonpay_wallet_address = ""
    mock_settings.service_fee_percent = 1.0

    provider = MoonpayProvider()
    try:
        provider.create_payment_intent(amount_usd=10.0, member_id="chat-1")
        assert False, "Should have raised ValueError"
    except ValueError as exc:
        assert "MOONPAY_WALLET_ADDRESS" in str(exc)


@patch("src.services.payments.moonpay.requests.get")
@patch("src.services.payments.moonpay.settings")
def test_moonpay_verify_completed_order(mock_settings, mock_get):
    mock_settings.moonpay_secret_key = "sk_test_123"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {"status": "completed", "id": "order-123", "quoteCurrencyAmount": 25.0},
    ]
    mock_get.return_value = mock_resp

    provider = MoonpayProvider()
    result = provider.verify_payment_settlement(
        intent_id="intent-1", tx_signature="order-123"
    )

    assert result.status == PaymentStatus.CONFIRMED
    assert result.tx_signature == "order-123"
    assert result.settled_amount == 25.0


@patch("src.services.payments.moonpay.requests.get")
@patch("src.services.payments.moonpay.settings")
def test_moonpay_verify_pending_order(mock_settings, mock_get):
    mock_settings.moonpay_secret_key = "sk_test_123"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {"status": "pending", "id": "order-456"},
    ]
    mock_get.return_value = mock_resp

    provider = MoonpayProvider()
    result = provider.verify_payment_settlement(
        intent_id="intent-1", tx_signature="order-456"
    )

    assert result.status == PaymentStatus.PENDING


@patch("src.services.payments.moonpay.requests.get")
@patch("src.services.payments.moonpay.settings")
def test_moonpay_verify_failed_order(mock_settings, mock_get):
    mock_settings.moonpay_secret_key = "sk_test_123"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {"status": "failed", "id": "order-789", "failureReason": "Cancelled by customer"},
    ]
    mock_get.return_value = mock_resp

    provider = MoonpayProvider()
    result = provider.verify_payment_settlement(
        intent_id="intent-1", tx_signature="order-789"
    )

    assert result.status == PaymentStatus.FAILED
    assert "failed" in result.error


@patch("src.services.payments.moonpay.settings")
def test_moonpay_verify_without_secret_key(mock_settings):
    mock_settings.moonpay_secret_key = ""

    provider = MoonpayProvider()
    result = provider.verify_payment_settlement(
        intent_id="intent-1", tx_signature="order-000"
    )

    assert result.status == PaymentStatus.FAILED
    assert "MOONPAY_SECRET_KEY" in result.error


@patch("src.services.payments.moonpay.settings")
def test_moonpay_sandbox_url_in_dev(mock_settings):
    mock_settings.service_fee_percent = 1.0
    mock_settings.app_env = "dev"
    mock_settings.moonpay_api_key = "pk_test_123"
    mock_settings.moonpay_wallet_address = "TreasuryWallet123"
    mock_settings.moonpay_currency_code = "usdc_sol"
    mock_settings.moonpay_network = "solana"

    provider = MoonpayProvider()
    intent = provider.create_payment_intent(amount_usd=10.0, member_id="chat-1")

    assert "buy-sandbox.moonpay.com" in intent.payment_url
