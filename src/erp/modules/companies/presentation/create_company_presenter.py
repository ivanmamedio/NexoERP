"""Create company presenter (domain- and application-layer only)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from erp.modules.companies.application.create_company import CreateCompanyInput
from erp.modules.companies.application.services import CompaniesServices
from erp.modules.companies.domain.company import Company
from erp.shared.application.session import CurrentSession
from erp.shared.domain.errors import NotFound


@runtime_checkable
class CompaniesCreateView(Protocol):
    """Contrato da tela de create/edit de empresas."""

    def show_error(self, message: str) -> None: ...
    def accept(self) -> None: ...


class CompaniesCreatePresenter:
    """Orquestra o cadastro/edição de empresas sem depender de Qt."""

    def __init__(
        self,
        view: CompaniesCreateView,
        services: CompaniesServices,
        session: CurrentSession,
    ) -> None:
        self._view = view
        self._services = services
        self._session = session

    def save(
        self,
        *,
        name: str,
        trade_name: str,
        tax_id: str,
        address: str,
        phone: str,
        email: str,
        active: bool,
    ) -> bool:
        if not name:
            self._view.show_error("Informe a razão social.")
            return False
        if not tax_id:
            self._view.show_error("Informe o CNPJ.")
            return False

        try:
            self._services.create_company(
                CreateCompanyInput(
                    name=name,
                    trade_name=trade_name,
                    tax_id=tax_id,
                    address=address,
                    phone=phone,
                    email=email,
                    active=active,
                )
            )
        except NotFound as exc:
            self._view.show_error(str(exc))
            return False
        except Exception as exc:  # pragma: no cover - defensive
            self._view.show_error(str(exc))
            return False

        self._view.accept()
        return True

    def load(self, company: Company | None) -> None:
        # The view handles loading; presenter only exposes active entity.
        _ = company  # no-op, kept explicit for the view protocol

    def update(self, company: Company) -> None:
        """Preenche o form de edição."""
        _ = company  # used by the view via load_company
