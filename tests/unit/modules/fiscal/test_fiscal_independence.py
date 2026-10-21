"""Tests proving sales flow doesn't depend on fiscal adapters."""

from __future__ import annotations

import pytest

from erp.modules.fiscal.application.ports import FiscalPort
from erp.modules.fiscal.application.service import create_fiscal_service
from erp.modules.fiscal.domain import (
    FiscalDocument,
    FiscalDocumentStatus,
    FiscalDocumentType,
    FiscalOperationResult,
)
from erp.modules.fiscal.infrastructure.noop_adapter import NoOpFiscalAdapter


class MockFiscalAdapter(FiscalPort):
    """Mock fiscal adapter for testing."""

    def __init__(self) -> None:
        self.emit_called = False
        self.cancel_called = False
        self.consult_called = False

    def emit_document(self, document: FiscalDocument) -> FiscalOperationResult:
        self.emit_called = True
        return FiscalOperationResult.success_result(
            document_id="mock-doc-123",
            protocol="MOCK-PROTOCOL",
        )

    def cancel_document(self, document_id: str, justification: str) -> FiscalOperationResult:
        self.cancel_called = True
        return FiscalOperationResult.success_result(document_id=document_id)

    def consult_document(self, document_id: str) -> FiscalOperationResult:
        self.consult_called = True
        return FiscalOperationResult.success_result(document_id=document_id)

    def get_supported_types(self) -> list[FiscalDocumentType]:
        return [FiscalDocumentType.NFCE]


class TestFiscalPortInterface:
    """Tests for FiscalPort interface."""

    def test_fiscal_port_is_protocol(self) -> None:
        """FiscalPort should be a Protocol (structural subtyping)."""
        from typing import Protocol

        assert issubclass(FiscalPort, Protocol)

    def test_noop_adapter_implements_port(self) -> None:
        """NoOpFiscalAdapter should implement FiscalPort."""
        adapter = NoOpFiscalAdapter()
        assert isinstance(adapter, FiscalPort)

    def test_mock_adapter_implements_port(self) -> None:
        """MockFiscalAdapter should implement FiscalPort."""
        adapter = MockFiscalAdapter()
        assert isinstance(adapter, FiscalPort)

    def test_fiscal_service_without_adapter(self) -> None:
        """FiscalService should work without adapter (return errors)."""
        service = create_fiscal_service()

        assert not service.is_configured()

        doc = FiscalDocument(
            document_type=FiscalDocumentType.NFCE,
            company_id=1,
            series="1",
            number=1,
        )
        result = service.emit_document(doc)

        assert not result.success
        assert result.error_code == "NO_ADAPTER"

    def test_fiscal_service_with_noop_adapter(self) -> None:
        """FiscalService should work with NoOpFiscalAdapter."""
        adapter = NoOpFiscalAdapter()
        service = create_fiscal_service(adapter)

        assert service.is_configured()

        doc = FiscalDocument(
            document_type=FiscalDocumentType.NFCE,
            company_id=1,
            series="1",
            number=1,
        )
        result = service.emit_document(doc)

        assert result.success
        assert result.document_id.startswith("noop-")

    def test_fiscal_service_with_mock_adapter(self) -> None:
        """FiscalService should work with MockFiscalAdapter."""
        adapter = MockFiscalAdapter()
        service = create_fiscal_service(adapter)

        doc = FiscalDocument(
            document_type=FiscalDocumentType.NFE,
            company_id=1,
            series="1",
            number=1,
        )
        result = service.emit_document(doc)

        assert result.success
        assert result.document_id == "mock-doc-123"
        assert adapter.emit_called


class TestSalesFlowIndependence:
    """Tests proving sales flow doesn't depend on fiscal adapters."""

    def test_sales_services_does_not_import_fiscal(self) -> None:
        """SalesServices should not import fiscal module."""
        # This test verifies that the sales module doesn't have
        # any direct dependency on the fiscal module.
        # Check that SalesServices doesn't reference fiscal
        import inspect

        import erp.modules.sales.application.services as sales_services

        source = inspect.getsource(sales_services.SalesServices)
        assert "fiscal" not in source.lower()
        assert "FiscalPort" not in source
        assert "FiscalService" not in source

    def test_sale_completed_event_no_fiscal(self) -> None:
        """SaleCompleted event should not contain fiscal data."""
        from erp.shared.domain.events import SaleCompleted

        # SaleCompleted should not have fiscal fields
        event = SaleCompleted(
            sale_id=1,
            company_id=1,
            total_cents=10000,
            items=[],
        )

        # Verify no fiscal-related attributes
        assert not hasattr(event, "fiscal_document")
        assert not hasattr(event, "nfe_key")
        assert not hasattr(event, "nfce_key")
        assert not hasattr(event, "fiscal_protocol")

    def test_catalog_sale_subscriber_no_fiscal(self) -> None:
        """CatalogSaleSubscriber should not depend on fiscal."""
        import inspect

        import erp.modules.catalog.application.sale_subscriber as cat_sub

        source = inspect.getsource(cat_sub.CatalogSaleSubscriber)
        assert "fiscal" not in source.lower()
        assert "FiscalPort" not in source

    def test_cash_sale_subscriber_no_fiscal(self) -> None:
        """CashSaleSubscriber should not depend on fiscal."""
        import inspect

        import erp.modules.cash.application.sale_subscriber as cash_sub

        source = inspect.getsource(cash_sub.CashSaleSubscriber)
        assert "fiscal" not in source.lower()
        assert "FiscalPort" not in source

    def test_treasury_sale_subscriber_no_fiscal(self) -> None:
        """TreasurySaleSubscriber should not depend on fiscal."""
        import inspect

        import erp.modules.treasury.application.sale_subscriber as treas_sub

        source = inspect.getsource(treas_sub.TreasurySaleSubscriber)
        assert "fiscal" not in source.lower()
        assert "FiscalPort" not in source

    def test_bootstrap_can_work_without_fiscal_adapter(self) -> None:
        """Bootstrap should work without configuring fiscal adapter."""
        # The bootstrap.py creates AppContext without requiring fiscal
        import inspect

        import erp.bootstrap as bootstrap_module

        source = inspect.getsource(bootstrap_module.bootstrap)
        # Fiscal service is optional in bootstrap
        # (it's created but adapter can be None)
        assert "FiscalService" not in source or "create_fiscal_service" not in source


class TestFiscalDocumentTypes:
    """Tests for fiscal document types."""

    def test_document_types_enum(self) -> None:
        """FiscalDocumentType should have all expected types."""
        assert FiscalDocumentType.NFE == "nfe"
        assert FiscalDocumentType.NFCE == "nfce"
        assert FiscalDocumentType.SAT == "sat"
        assert FiscalDocumentType.CTE == "cte"
        assert FiscalDocumentType.MDFE == "mdfe"
        assert FiscalDocumentType.CFE == "cfe"

    def test_operation_result_helpers(self) -> None:
        """FiscalOperationResult helpers should work correctly."""
        success = FiscalOperationResult.success_result("doc-1", "prot-1")
        assert success.success
        assert success.document_id == "doc-1"
        assert success.protocol == "prot-1"
        assert success.status == FiscalDocumentStatus.AUTHORIZED

        error = FiscalOperationResult.error_result("ERR-001", "Error message")
        assert not error.success
        assert error.error_code == "ERR-001"
        assert error.error_message == "Error message"
        assert error.status == FiscalDocumentStatus.ERROR


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
