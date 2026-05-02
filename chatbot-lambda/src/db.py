import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from prisma import Prisma
else:
    Prisma = Any

logger = logging.getLogger(__name__)

_client: Prisma | None = None


def get_db() -> Prisma:
    """Return a connected Prisma client, creating one on first call."""
    global _client
    if _client is None or not _client.is_connected():
        from prisma import Prisma as PrismaClient

        _client = PrismaClient()
        _client.connect()
        logger.info("Prisma client connected")
    return _client


def disconnect_db() -> None:
    global _client
    if _client is not None and _client.is_connected():
        _client.disconnect()
        _client = None
        logger.info("Prisma client disconnected")
