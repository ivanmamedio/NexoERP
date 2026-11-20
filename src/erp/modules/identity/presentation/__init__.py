"""Identity presentation layer."""

from erp.modules.identity.presentation.change_password_presenter import (
    ChangePasswordPresenter,
    ChangePasswordView,
)
from erp.modules.identity.presentation.change_password_view import (
    ChangePasswordDialog,
    create_change_password_dialog,
)
from erp.modules.identity.presentation.first_use_presenter import (
    FirstUsePresenter,
    FirstUseView,
)
from erp.modules.identity.presentation.first_use_view import (
    FirstUseDialog,
    create_first_use_dialog,
)
from erp.modules.identity.presentation.login_presenter import (
    LoginPresenter,
    LoginView,
)
from erp.modules.identity.presentation.login_view import (
    LoginDialog,
    create_login_dialog,
)
from erp.modules.identity.presentation.select_company_view import (
    SelectCompanyDialog,
    create_select_company_dialog,
)
from erp.modules.identity.presentation.users_presenter import (
    UsersPresenter,
    UsersView,
)
from erp.modules.identity.presentation.users_view import (
    UsersWidget,
)

__all__ = [
    "ChangePasswordDialog",
    "ChangePasswordPresenter",
    "ChangePasswordView",
    "FirstUseDialog",
    "FirstUsePresenter",
    "FirstUseView",
    "LoginDialog",
    "LoginPresenter",
    "LoginView",
    "SelectCompanyDialog",
    "UsersPresenter",
    "UsersView",
    "UsersWidget",
    "create_change_password_dialog",
    "create_first_use_dialog",
    "create_login_dialog",
    "create_select_company_dialog",
]
