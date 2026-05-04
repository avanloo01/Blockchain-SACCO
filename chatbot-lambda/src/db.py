import logging
from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from prisma import Prisma
else:
    Prisma = Any

logger = logging.getLogger(__name__)

_client: Prisma | None = None


def _load_prisma_client_class() -> type[Prisma]:
    for module_name in ("generated.prisma", "prisma"):
        try:
            module = import_module(module_name)
            return module.Prisma
        except ModuleNotFoundError:
            continue

    raise RuntimeError(
        "Prisma client is unavailable. Run `python -m prisma generate --schema prisma/schema.prisma` before deploying."
    )


def get_db() -> Prisma:
    """Return a connected Prisma client, creating one on first call."""
    global _client
    if _client is None or not _client.is_connected():
        prisma_client_class = _load_prisma_client_class()
        _client = prisma_client_class()
        _client.connect()
        logger.info("Prisma client connected")
    return _client


def disconnect_db() -> None:
    global _client
    if _client is not None and _client.is_connected():
        _client.disconnect()
        _client = None
        logger.info("Prisma client disconnected")
