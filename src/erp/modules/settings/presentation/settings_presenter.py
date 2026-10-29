"""Settings presenter — orquestra a tela de configurações sem dependência de Qt."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from erp.modules.settings.application.services import SettingsServices
from erp.shared.application.session import CurrentSession


@runtime_checkable
class SettingsView(Protocol):
    """Contrato da tela de configurações consumido pelo presenter."""

    def show_error(self, message: str) -> None: ...
    def show_success(self, message: str) -> None: ...
    def set_company_name(self, name: str) -> None: ...
    def set_cnpj(self, cnpj: str) -> None: ...
    def set_address(self, address: str) -> None: ...
    def set_receipt_header(self, message: str) -> None: ...
    def set_receipt_footer(self, message: str) -> None: ...
    def set_idle_timeout_minutes(self, minutes: int) -> None: ...
    def get_company_name(self) -> str: ...
    def get_cnpj(self) -> str: ...
    def get_address(self) -> str: ...
    def get_receipt_header(self) -> str: ...
    def get_receipt_footer(self) -> str: ...
    def get_idle_timeout_minutes(self) -> int: ...
    def accept(self) -> None: ...


class SettingsPresenter:
    """Gerencia leitura e gravação de configurações da empresa."""

    def __init__(
        self,
        view: SettingsView,
        services: SettingsServices,
        session: CurrentSession,
        company_name: str,
    ) -> None:
        self._view = view
        self._services = services
        self._session = session
        self._company_name = company_name

    def load_settings(self) -> None:
        """Carrega as configurações da empresa ativa."""
        company_id = self._session.company_id
        if company_id is None:
            self._view.show_error("Nenhuma empresa ativa na sessão.")
            return

        try:
            # Dados da empresa para cabeçalho/rodapé do cupom
            company_name = self._services.get_setting(company_id=company_id, key="company_name")
            self._view.set_company_name(company_name.value)

            cnpj = self._services.get_setting(company_id=company_id, key="cnpj")
            self._view.set_cnpj(cnpj.value)

            address = self._services.get_setting(company_id=company_id, key="address")
            self._view.set_address(address.value)

            receipt_header = self._services.get_setting(company_id=company_id, key="receipt_header")
            self._view.set_receipt_header(receipt_header.value)

            receipt_footer = self._services.get_setting(company_id=company_id, key="receipt_footer")
            self._view.set_receipt_footer(receipt_footer.value)

            # Timeout de sessão ociosa
            idle_timeout = self._services.get_setting(
                company_id=company_id, key="idle_timeout_minutes"
            )
            try:
                minutes = int(idle_timeout.value)
            except (ValueError, TypeError):
                minutes = 30
            self._view.set_idle_timeout_minutes(minutes)
        except Exception as exc:  # pragma: no cover - erro inesperado de infraestrutura
            self._view.show_error(f"Erro ao carregar configurações: {exc}")

    def save_settings(self) -> None:
        """Salva as configurações da empresa ativa."""
        company_id = self._session.company_id
        if company_id is None:
            self._view.show_error("Nenhuma empresa ativa na sessão.")
            return

        user_id = self._session.user_id
        username = self._session.username or ""

        try:
            self._services.update_setting(
                company_id=company_id,
                key="company_name",
                value=self._view.get_company_name(),
                value_type="string",
                user_id=user_id,
                username=username,
            )
            self._services.update_setting(
                company_id=company_id,
                key="cnpj",
                value=self._view.get_cnpj(),
                value_type="string",
                user_id=user_id,
                username=username,
            )
            self._services.update_setting(
                company_id=company_id,
                key="address",
                value=self._view.get_address(),
                value_type="string",
                user_id=user_id,
                username=username,
            )
            self._services.update_setting(
                company_id=company_id,
                key="receipt_header",
                value=self._view.get_receipt_header(),
                value_type="string",
                user_id=user_id,
                username=username,
            )
            self._services.update_setting(
                company_id=company_id,
                key="receipt_footer",
                value=self._view.get_receipt_footer(),
                value_type="string",
                user_id=user_id,
                username=username,
            )
            self._services.update_setting(
                company_id=company_id,
                key="idle_timeout_minutes",
                value=str(self._view.get_idle_timeout_minutes()),
                value_type="int",
                user_id=user_id,
                username=username,
            )

            self._view.show_success("Configurações salvas com sucesso.")
            self._view.accept()
        except Exception as exc:  # pragma: no cover - erro inesperado de infraestrutura
            self._view.show_error(f"Erro ao salvar configurações: {exc}")
