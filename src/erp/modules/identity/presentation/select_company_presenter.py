"""SelectCompanyPresenter — orquestra a seleção de empresa após o login."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from erp.shared.application.session import CurrentSession


@runtime_checkable
class SelectCompanyView(Protocol):
    """Contrato da tela de seleção de empresa consumido pelo presenter."""

    def show_error(self, message: str) -> None: ...
    def show_info(self, message: str) -> None: ...
    def render_companies(self, companies: list[tuple[int, str]]) -> None: ...
    def get_selected_company_id(self) -> int | None: ...
    def accept(self) -> None: ...


class SelectCompanyPresenter:
    """Define a empresa selecionada na sessão corrente."""

    def __init__(
        self,
        view: SelectCompanyView,
        session: CurrentSession,
    ) -> None:
        self._view = view
        self._session = session

    def select_company(self, company_id: int) -> None:
        """Registra a empresa escolhida na sessão e aceita o diálogo."""
        self._session.company_id = company_id
        self._view.accept()
