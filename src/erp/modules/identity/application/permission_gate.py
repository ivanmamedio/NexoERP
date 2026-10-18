"""PermissionGate — verificação de permissão dentro dos casos de uso."""

from __future__ import annotations

from erp.modules.identity.application.ports import UserRepository
from erp.shared.domain.errors import PermissionDenied


class PermissionGate:
    """Consulta permissões de um usuário e falha com PermissionDenied.

    A permissão é verificada NO CASO DE USO (não apenas escondendo botões
    na interface), conforme a regra inviolável de arquitetura.
    """

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    def has(self, user_id: int, permission_code: str) -> bool:
        """Retorna True se o usuário possui a permissão indicada."""
        user = self._user_repo.get_by_id(user_id)
        if user is None:
            return False
        return any(p.code == permission_code for p in self._user_repo.get_permissions(user))

    def require(self, user_id: int, permission_code: str) -> None:
        """Levanta PermissionDenied se o usuário não possuir a permissão."""
        if not self.has(user_id, permission_code):
            raise PermissionDenied(f"Permissão negada: '{permission_code}'.")
