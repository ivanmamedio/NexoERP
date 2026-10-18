"""SaleCompleted domain event.

Published by FinalizeSale. Catalog, cash, treasury and audit modules
react via EventBus, within the same transaction.

Re-exported here for convenience; the canonical definition lives in
``erp.shared.domain.events`` so modules do not need to depend on sales.
"""

from __future__ import annotations

from erp.shared.domain.events import SaleCompleted

__all__ = ["SaleCompleted"]
