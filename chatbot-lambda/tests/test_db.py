from unittest.mock import call, patch

from src.db import _load_prisma_client_class


class _GeneratedPrisma:
    pass


class _InstalledPrisma:
    pass


class _Module:
    def __init__(self, prisma_cls):
        self.Prisma = prisma_cls


@patch("src.db.import_module")
def test_load_prisma_client_class_prefers_generated_package(mock_import_module) -> None:
    mock_import_module.side_effect = [
        _Module(_GeneratedPrisma),
    ]

    prisma_client_class = _load_prisma_client_class()

    assert prisma_client_class is _GeneratedPrisma
    mock_import_module.assert_called_once_with("generated.prisma")


@patch("src.db.import_module")
def test_load_prisma_client_class_falls_back_to_installed_package(mock_import_module) -> None:
    mock_import_module.side_effect = [
        ModuleNotFoundError("No module named 'generated'"),
        _Module(_InstalledPrisma),
    ]

    prisma_client_class = _load_prisma_client_class()

    assert prisma_client_class is _InstalledPrisma
    assert mock_import_module.call_args_list == [call("generated.prisma"), call("prisma")]


@patch("src.db.import_module")
def test_load_prisma_client_class_raises_clear_error_when_no_client_exists(mock_import_module) -> None:
    mock_import_module.side_effect = [
        ModuleNotFoundError("No module named 'generated'"),
        ModuleNotFoundError("No module named 'prisma'"),
    ]

    try:
        _load_prisma_client_class()
        assert False, "Expected RuntimeError"
    except RuntimeError as exc:
        assert "prisma generate" in str(exc)