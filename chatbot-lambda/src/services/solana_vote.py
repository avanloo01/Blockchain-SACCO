"""On-chain governance vote anchoring via the Solana Memo program.

Posts a signed memo transaction to Solana to create an immutable, auditable
record of each governance vote.  The memo format is:
    governance:vote:<loan_id>:<member_id>:<yes|no>

The treasury keypair signs the transaction so votes are attributable to the
SACCO treasury authority on-chain.  This is best-effort — callers should still
persist the vote in Postgres regardless of whether the on-chain write succeeds.
"""

from __future__ import annotations

import logging

from solders.hash import Hash
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction

from src.services.solana_disburse import _rpc
from src.config import settings

logger = logging.getLogger(__name__)

# Solana Memo program v2 (mainnet and devnet).
_MEMO_PROGRAM_ID = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")


def anchor_vote_on_chain(loan_id: str, member_id: str, vote: str) -> str | None:
    """Submit a memo transaction recording the governance vote.

    Returns the base58 transaction signature on success, or None on failure.
    """
    private_key_b58 = settings.solana_treasury_private_key
    rpc_url = settings.solana_rpc_url

    if not private_key_b58 or not rpc_url:
        logger.warning("Solana not configured — skipping on-chain vote anchor")
        return None

    try:
        keypair = Keypair.from_base58_string(private_key_b58)
        payer = keypair.pubkey()

        memo_text = f"governance:vote:{loan_id}:{member_id}:{vote}"
        memo_bytes = memo_text.encode("utf-8")

        memo_ix = Instruction(
            program_id=_MEMO_PROGRAM_ID,
            accounts=[AccountMeta(pubkey=payer, is_signer=True, is_writable=False)],
            data=memo_bytes,
        )

        bh_resp = _rpc(rpc_url, "getLatestBlockhash", [{"commitment": "confirmed"}])
        recent_blockhash = Hash.from_string(bh_resp["result"]["value"]["blockhash"])

        tx = Transaction.new_signed_with_payer(
            instructions=[memo_ix],
            payer=payer,
            signing_keypairs=[keypair],
            recent_blockhash=recent_blockhash,
        )

        import base64  # noqa: PLC0415
        tx_b64 = base64.b64encode(bytes(tx)).decode("utf-8")
        send_resp = _rpc(
            rpc_url,
            "sendTransaction",
            [tx_b64, {"encoding": "base64", "preflightCommitment": "confirmed"}],
        )

        if "error" in send_resp:
            logger.error(
                "On-chain vote anchor failed loan=%s member=%s: %s",
                loan_id, member_id, send_resp["error"],
            )
            return None

        sig = send_resp["result"]
        logger.info(
            "On-chain vote anchored loan=%s member=%s vote=%s sig=%s",
            loan_id, member_id, vote, sig,
        )
        return sig

    except Exception:
        logger.exception(
            "Unexpected error anchoring vote on-chain loan=%s member=%s", loan_id, member_id
        )
        return None
