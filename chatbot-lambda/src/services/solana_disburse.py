"""Solana USDC disbursement service.

Sends USDC from the SACCO treasury wallet to a member's wallet address.
Requires SOLANA_TREASURY_PRIVATE_KEY (base58-encoded 64-byte keypair) and
SOLANA_RPC_URL to be configured.
"""

from __future__ import annotations

import base64
import logging
import struct
from typing import NamedTuple

import requests
from solders.hash import Hash
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction

from src.config import settings

logger = logging.getLogger(__name__)

# Well-known Solana program IDs.
_TOKEN_PROGRAM_ID = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
_ASSOCIATED_TOKEN_PROGRAM_ID = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
_SYSTEM_PROGRAM_ID = Pubkey.from_string("11111111111111111111111111111111")

# USDC has 6 decimal places.
_USDC_DECIMALS = 6


class DisburseResult(NamedTuple):
    tx_signature: str
    error: str | None = None


def _get_ata(wallet: Pubkey, mint: Pubkey) -> Pubkey:
    """Derive the Associated Token Account (ATA) address for a given owner and mint."""
    seeds = [bytes(wallet), bytes(_TOKEN_PROGRAM_ID), bytes(mint)]
    ata, _ = Pubkey.find_program_address(seeds, _ASSOCIATED_TOKEN_PROGRAM_ID)
    return ata


def _create_ata_idempotent_instruction(
    payer: Pubkey, owner: Pubkey, mint: Pubkey, ata: Pubkey
) -> Instruction:
    """Create an ATA using the idempotent variant (no-op if ATA already exists)."""
    return Instruction(
        program_id=_ASSOCIATED_TOKEN_PROGRAM_ID,
        accounts=[
            AccountMeta(pubkey=payer, is_signer=True, is_writable=True),
            AccountMeta(pubkey=ata, is_signer=False, is_writable=True),
            AccountMeta(pubkey=owner, is_signer=False, is_writable=False),
            AccountMeta(pubkey=mint, is_signer=False, is_writable=False),
            AccountMeta(pubkey=_SYSTEM_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(pubkey=_TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
        ],
        # Discriminator 1 = CreateIdempotent instruction variant.
        data=bytes([1]),
    )


def _spl_transfer_instruction(
    source_ata: Pubkey,
    dest_ata: Pubkey,
    owner: Pubkey,
    amount_raw: int,
) -> Instruction:
    """Build an SPL Token Transfer instruction (discriminator 3)."""
    data = struct.pack("<BQ", 3, amount_raw)
    return Instruction(
        program_id=_TOKEN_PROGRAM_ID,
        accounts=[
            AccountMeta(pubkey=source_ata, is_signer=False, is_writable=True),
            AccountMeta(pubkey=dest_ata, is_signer=False, is_writable=True),
            AccountMeta(pubkey=owner, is_signer=True, is_writable=False),
        ],
        data=data,
    )


def _rpc(rpc_url: str, method: str, params: list, *, call_id: int = 1) -> dict:
    resp = requests.post(
        rpc_url,
        json={"jsonrpc": "2.0", "id": call_id, "method": method, "params": params},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()


def disburse_usdc(recipient_wallet: str, amount_usd: float, mint_address: str) -> DisburseResult:
    """Transfer USDC from the SACCO treasury to *recipient_wallet*.

    Args:
        recipient_wallet: Base58 Solana wallet address of the loan recipient.
        amount_usd: Exact loan amount in USD (USDC is 1:1).
        mint_address: SPL token mint address for USDC on the target network.

    Returns:
        DisburseResult with the transaction signature, or an error string.
    """
    private_key_b58 = settings.solana_treasury_private_key
    rpc_url = settings.solana_rpc_url

    if not private_key_b58:
        return DisburseResult(
            tx_signature="",
            error="SOLANA_TREASURY_PRIVATE_KEY is not configured",
        )
    if not rpc_url:
        return DisburseResult(tx_signature="", error="SOLANA_RPC_URL is not configured")

    try:
        keypair = Keypair.from_base58_string(private_key_b58)
        treasury_pk = keypair.pubkey()
        recipient_pk = Pubkey.from_string(recipient_wallet)
        mint_pk = Pubkey.from_string(mint_address)

        amount_raw = int(round(amount_usd * (10**_USDC_DECIMALS)))

        source_ata = _get_ata(treasury_pk, mint_pk)
        dest_ata = _get_ata(recipient_pk, mint_pk)

        # Fetch the latest blockhash.
        bh_resp = _rpc(rpc_url, "getLatestBlockhash", [{"commitment": "confirmed"}])
        blockhash_str: str = bh_resp["result"]["value"]["blockhash"]
        recent_blockhash = Hash.from_string(blockhash_str)

        # Always include CreateIdempotent so the recipient's ATA is created if needed,
        # without failing if it already exists.
        instructions = [
            _create_ata_idempotent_instruction(treasury_pk, recipient_pk, mint_pk, dest_ata),
            _spl_transfer_instruction(source_ata, dest_ata, treasury_pk, amount_raw),
        ]

        from solders.message import Message  # noqa: PLC0415

        msg = Message.new_with_blockhash(instructions, treasury_pk, recent_blockhash)
        tx = Transaction([keypair], msg, recent_blockhash)
        tx_b64 = base64.b64encode(bytes(tx)).decode("ascii")

        send_resp = _rpc(
            rpc_url,
            "sendTransaction",
            [tx_b64, {"encoding": "base64", "preflightCommitment": "confirmed"}],
            call_id=3,
        )

        if "error" in send_resp:
            err = send_resp["error"]
            logger.error("Solana sendTransaction error: %s", err)
            return DisburseResult(tx_signature="", error=str(err))

        sig: str = send_resp["result"]
        logger.info(
            "Disbursed %.2f USDC to %s tx=%s", amount_usd, recipient_wallet, sig
        )
        return DisburseResult(tx_signature=sig)

    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Solana disbursement failed for %s: %s", recipient_wallet, exc)
        return DisburseResult(tx_signature="", error=str(exc))
