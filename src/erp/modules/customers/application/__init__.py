"""Application module init for customers."""

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

__all__ = [
    "CreateCustomer",
    "CreateCustomerInput",
    "CreateCustomerOutput",
    "CustomerView",
    "FindCustomers",
    "FindCustomersInput",
    "UpdateCustomer",
    "UpdateCustomerInput",
    "UpdateCustomerOutput",
]
