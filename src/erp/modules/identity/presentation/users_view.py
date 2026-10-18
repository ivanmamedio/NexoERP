"""Tela de gestão de usuários (Qt). Delega ao UsersPresenter."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from erp.modules.identity.application.list_roles import RoleListItem
from erp.modules.identity.application.list_users import UserListItem
from erp.modules.identity.presentation.users_presenter import UsersPresenter


class UsersWidget(QWidget):
    """Painel de gestão de usuários: tabela + criação + atribuição de papel."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._presenter: UsersPresenter | None = None
        self._users: list[UserListItem] = []

        self._table = QTableWidget(0, 5, self)
        self._table.setHorizontalHeaderLabels(
            ["ID", "Usuário", "Papéis", "Ativo", "Status"]
        )
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)

        self._new_username = QLineEdit(self)
        self._new_password = QLineEdit(self)
        self._new_password.setEchoMode(QLineEdit.EchoMode.Password)
        self._new_role = QComboBox(self)
        create_form = QFormLayout()
        create_form.addRow("Usuário:", self._new_username)
        create_form.addRow("Senha inicial:", self._new_password)
        create_form.addRow("Papel:", self._new_role)
        self._create_button = QPushButton("Criar usuário", self)
        self._create_button.clicked.connect(self._on_create)
        create_box = QGroupBox("Novo usuário", self)
        create_layout = QVBoxLayout(create_box)
        create_layout.addLayout(create_form)
        create_btn_row = QHBoxLayout()
        create_btn_row.addStretch()
        create_btn_row.addWidget(self._create_button)
        create_layout.addLayout(create_btn_row)
        # --- atribuição de papel / ativação ---
        self._assign_role = QComboBox(self)
        self._assign_button = QPushButton("Atribuir papel", self)
        self._assign_button.clicked.connect(self._on_assign)
        self._deactivate_button = QPushButton("Desativar", self)
        self._deactivate_button.clicked.connect(self._on_deactivate)
        self._activate_button = QPushButton("Ativar", self)
        self._activate_button.clicked.connect(self._on_activate)
        actions_row = QHBoxLayout()
        actions_row.addWidget(QLabel("Papel:"))
        actions_row.addWidget(self._assign_role)
        actions_row.addWidget(self._assign_button)
        actions_row.addStretch()
        actions_row.addWidget(self._deactivate_button)
        actions_row.addWidget(self._activate_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self._table, stretch=1)
        layout.addWidget(create_box)
        layout.addLayout(actions_row)

    def set_presenter(self, presenter: UsersPresenter) -> None:
        self._presenter = presenter

    # --- UsersView protocol -------------------------------------------------

    def render_users(self, users: list[UserListItem]) -> None:
        self._users = users
        self._table.setRowCount(len(users))
        for row, user in enumerate(users):
            self._table.setItem(row, 0, QTableWidgetItem(str(user.user_id)))
            self._table.setItem(row, 1, QTableWidgetItem(user.username))
            self._table.setItem(row, 2, QTableWidgetItem(", ".join(user.role_names)))
            self._table.setItem(row, 3, QTableWidgetItem("Sim" if user.is_active else "Não"))
            self._table.setItem(row, 4, QTableWidgetItem(self._status_text(user)))
        self._table.resizeColumnsToContents()

    def render_roles(self, roles: list[RoleListItem]) -> None:
        self._new_role.clear()
        self._assign_role.clear()
        for role in roles:
            label = role.name
            if role.description:
                label = f"{role.name} — {role.description}"
            self._new_role.addItem(label, role.name)
            self._assign_role.addItem(label, role.name)

    def show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Erro", message)

    def show_info(self, message: str) -> None:
        QMessageBox.information(self, "Sucesso", message)

    def clear_user_form(self) -> None:
        self._new_username.clear()
        self._new_password.clear()

    def selected_user_id(self) -> int | None:
        row = self._table.currentRow()
        if row < 0 or row >= len(self._users):
            return None
        return self._users[row].user_id

    # --- internals ----------------------------------------------------------

    @staticmethod
    def _status_text(user: UserListItem) -> str:
        if user.is_locked:
            return "Bloqueado"
        if not user.is_active:
            return "Inativo"
        if user.must_change_password:
            return "Trocar senha"
        return "OK"

    def _on_create(self) -> None:
        if self._presenter is None:
            return
        role_name = self._new_role.currentData()
        self._presenter.create_user(
            self._new_username.text(),
            self._new_password.text(),
            role_name or "",
        )

    def _on_assign(self) -> None:
        if self._presenter is None:
            return
        role_name = self._assign_role.currentData()
        self._presenter.assign_role(role_name or "")

    def _on_deactivate(self) -> None:
        if self._presenter is not None:
            self._presenter.set_active(False)

    def _on_activate(self) -> None:
        if self._presenter is not None:
            self._presenter.set_active(True)
