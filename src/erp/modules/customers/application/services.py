"""Application services facade for Customers."""

from __future__ import annotations

from sqlalchemy.engine import Engine

from erp.modules.customers.application.create_customer import (
    CreateCustomer,
    CreateCustomerInput,
    CreateCustomerOutput,
)
from erp.modules.customers.application.find_customers import (
    CustomerView,
    FindCustomers,
    FindCustomersInput,
)
from erp.modules.customers.application.update_customer import (
    UpdateCustomer,
    UpdateCustomerInput,
    UpdateCustomerOutput,
)
from erp.modules.customers.infrastructure.unit_of_work import (
    SqlAlchemyCustomersUnitOfWork,
)


class CustomersServices:
    """Facade de casos de uso de clientes sobre SQLAlchemy."""

    def __init__(
        self,
        engine: Engine,
        user_permissions: set[str] | None = None,
    ) -> None:
        self._engine = engine
        self._user_permissions = user_permissions or set()

    def create_customer(
        self,
        *,
        name: str,
        phone: str = "",
        document: str | None = None,
        credit_limit_cents: int = 0,
        user_id: int | None = None,
        username: str = "",
        company_id: int | None = None,
    ) -> CreateCustomerOutput:
        with SqlAlchemyCustomersUnitOfWork(self._engine) as uow:
            assert uow.customers is not None
            result = CreateCustomer(uow.customers, self._user_permissions).execute(
                CreateCustomerInput(
                    name=name,
                    phone=phone,
                    document=document,
                    credit_limit_cents=credit_limit_cents,
                    user_id=user_id,
                    username=username,
                    company_id=company_id,
                )
            )
            uow.commit()
            return result

    def update_customer(
        self,
        *,
        customer_id: int,
        name: str | None = None,
        phone: str | None = None,
        document: str | None = None,
        credit_limit_cents: int | None = None,
        is_active: bool | None = None,
        user_id: int | None = None,
        username: str = "",
        company_id: int | None = None,
    ) -> UpdateCustomerOutput:
        with SqlAlchemyCustomersUnitOfWork(self._engine) as uow:
            assert uow.customers is not None
            result = UpdateCustomer(uow.customers, self._user_permissions).execute(
                UpdateCustomerInput(
                    customer_id=customer_id,
                    name=name,
                    phone=phone,
                    document=document,
                    credit_limit_cents=credit_limit_cents,
                    is_active=is_active,
                    user_id=user_id,
                    username=username,
                    company_id=company_id,
                )
            )
            uow.commit()
            return result

    def find_customers(
        self,
        *,
        company_id: int,
        name_contains: str | None = None,
        phone: str | None = None,
    ) -> list[CustomerView]:
        with SqlAlchemyCustomersUnitOfWork(self._engine) as uow:
            assert uow.customers is not None
            result = FindCustomers(uow.customers, self._user_permissions).execute(
                FindCustomersInput(
                    company_id=company_id,
                    name_contains=name_contains,
                    phone=phone,
                )
            )
            uow.commit()
            return result

    def set_user_permissions(self, permissions: set[str]) -> None:
        """Atualiza as permissões do operador logado."""
        self._user_permissions = permissions
