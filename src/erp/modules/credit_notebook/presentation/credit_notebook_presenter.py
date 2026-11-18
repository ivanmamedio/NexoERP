"""Credit Notebook presenter (domain- and application-layer only)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from erp.modules.credit_notebook.application.create_customer import (
    CreateCreditCustomerInput,
    CreateCreditCustomerOutput,
)
from erp.modules.credit_notebook.application.create_entry import (
    CreateCreditEntryInput,
    CreateCreditEntryOutput,
)
from erp.modules.credit_notebook.application.services import CreditNotebookServices
from erp.modules.credit_notebook.application.update_customer import (
    UpdateCreditCustomerInput,
    UpdateCreditCustomerOutput,
)
from erp.modules.credit_notebook.application.apply_payment import ApplyPaymentInput
from erp.shared.application.session import CurrentSession
from erp.shared.domain.errors import NotFound, ValidationError


@runtime_checkable
class CreditNotebookView(Protocol):
    """Contrato da tela do Caderno de Fiado."""

    def show_error(self, message: str) -> None: ...
    def show_success(self, message: str) -> None: ...
    def set_customers(self, customers: list) -> None: ...
    def set_entries(self, entries: list) -> None: ...


class CreditNotebookPresenter:
    """Orquestra o Caderno de Fiado sem depender de Qt."""

    def __init__(
        self,
        view: CreditNotebookView,
        services: CreditNotebookServices,
        session: CurrentSession,
    ) -> None:
        self._view = view
        self._services = services
        self._session = session

    def load_customers(self) -> None:
        try:
            output = self._services.list_customers(
                company_id=self._session.company_id,
            )
            self._view.set_customers(list(output.customers))
        except Exception as exc:
            self._view.show_error(str(exc))

    def save_customer(
        self,
        *,
        name: str,
        phone: str,
        email: str = "",
        address: str = "",
        credit_limit_cents: int = 0,
        status: str = "active",
        notes: str = "",
    ) -> bool:
        if not name:
            self._view.show_error("Nome é obrigatório.")
            return False
        if not phone:
            self._view.show_error("Telefone é obrigatório.")
            return False

        try:
            # Try to update if we have a customer in context, else create
            # For now, always create new (the view handles edit vs new)
            output = self._services.create_customer(
                CreateCreditCustomerInput(
                    name=name,
                    phone=phone,
                    email=email,
                    address=address,
                    credit_limit_cents=credit_limit_cents,
                    company_id=self._session.company_id,
                )
            )
            self._view.show_success(f"Cliente criado (ID: {output.customer_id})")
            self.load_customers()
            return True
        except ValidationError as exc:
            self._view.show_error(str(exc))
            return False
        except Exception as exc:
            self._view.show_error(f"Erro inesperado: {exc}")
            return False

    def update_customer(
        self,
        *,
        customer_id: int,
        name: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        address: str | None = None,
        credit_limit_cents: int | None = None,
        status: str | None = None,
        notes: str | None = None,
    ) -> bool:
        try:
            self._services.update_customer(
                UpdateCreditCustomerInput(
                    customer_id=customer_id,
                    name=name,
                    phone=phone,
                    email=email,
                    address=address,
                    credit_limit_cents=credit_limit_cents,
                    status=status,
                    notes=notes,
                    company_id=self._session.company_id,
                )
            )
            self._view.show_success("Cliente atualizado.")
            self.load_customers()
            return True
        except (NotFound, ValidationError) as exc:
            self._view.show_error(str(exc))
            return False
        except Exception as exc:
            self._view.show_error(f"Erro inesperado: {exc}")
            return False

    def save_entry(
        self,
        *,
        customer_id: int,
        entry_type: str,
        description: str,
        amount_cents: int,
        due_date: datetime | None = None,
        notes: str = "",
    ) -> bool:
        if not description:
            self._view.show_error("Descrição é obrigatória.")
            return False
        if amount_cents <= 0:
            self._view.show_error("Valor deve ser maior que zero.")
            return False

        try:
            from erp.modules.credit_notebook.application.create_entry import CreateCreditEntryInput
            output = self._services.create_entry(
                CreateCreditEntryInput(
                    customer_id=customer_id,
                    company_id=self._session.company_id,
                    entry_type=entry_type,
                    description=description,
                    amount_cents=amount_cents,
                    due_date=due_date,
                    notes=notes,
                    created_by_user_id=self._session.user_id,
                    created_by_username=self._session.username or "",
                )
            )
            self._view.show_success(f"Lançamento criado (ID: {output.entry_id})")
            return True
        except (NotFound, ValidationError) as exc:
            self._view.show_error(str(exc))
            return False
        except Exception as exc:
            self._view.show_error(f"Erro inesperado: {exc}")
            return False

    def apply_payment(
        self,
        *,
        entry_id: int,
        amount_cents: int,
    ) -> bool:
        try:
            self._services.apply_payment(
                ApplyPaymentInput(
                    entry_id=entry_id,
                    amount_cents=amount_cents,
                    paid_at=None,  # Use current time
                    company_id=self._session.company_id,
                )
            )
            self._view.show_success("Pagamento aplicado com sucesso!")
            return True
        except (NotFound, ValidationError) as exc:
            self._view.show_error(str(exc))
            return False
        except Exception as exc:
            self._view.show_error(f"Erro inesperado: {exc}")
            return False

    def load_entries(
        self,
        *,
        customer_id: int | None = None,
        company_id: int | None = None,
        status: str | None = None,
        entry_type: str | None = None,
    ) -> None:
        try:
            output = self._services.list_entries(
                customer_id=customer_id,
                company_id=company_id,
                status=status,
                entry_type=entry_type,
            )
            self._view.set_entries(list(output.entries))
        except Exception as exc:
            self._view.show_error(str(exc))


# Need to import datetime for the type hint
from datetime import datetime