"""Companies list presenter (domain- and application-layer only)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from erp.modules.companies.application.services import CompaniesServices
from erp.modules.companies.domain.company import Company
from erp.shared.application.session import CurrentSession
from erp.shared.domain.errors import NotFound


@runtime_checkable
class CompaniesListView(Protocol):
    """Contrato da tela de listagem de empresas."""

    def show_error(self, message: str) -> None: ...
    def show_loading(self, on: bool) -> None: ...
    def set_companies(self, companies: list[Company]) -> None: ...


class CompaniesListPresenter:
    """Orquestra a listagem de empresas sem depender de Qt."""

    def __init__(
        self,
        view: CompaniesListView,
        services: CompaniesServices,
        session: CurrentSession,
    ) -> None:
        self._view = view
        self._services = services
        self._session = session

    def load(self) -> None:
        try:
            self._view.show_loading(True)
            output = self._services.list_active_companies()
            self._view.set_companies(output.companies)
        except NotFound as exc:
            self._view.show_error(str(exc))
        except Exception as exc:  # pragma: no cover - defensive
            self._view.show_error(str(exc))
        finally:
            self._view.show_loading(False)
