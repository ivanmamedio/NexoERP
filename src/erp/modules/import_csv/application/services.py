"""Application services for import CSV module."""

from __future__ import annotations

from pathlib import Path

from erp.modules.import_csv.application.import_products_use_case import (
    ImportProductsInput,
    ImportProductsOutput,
    ImportProductsUseCase,
)
from erp.modules.import_csv.application.ports import (
    ImportResultRepositoryPort,
    ProductCatalogPort,
)


class ImportProductsServices:
    """Facade de serviços de importação de produtos."""

    def __init__(
        self,
        product_repo: ProductCatalogPort,
        result_repo: ImportResultRepositoryPort,
        user_permissions: set[str] | None = None,
    ) -> None:
        self._product_repo = product_repo
        self._result_repo = result_repo
        self._user_permissions = user_permissions or set()

    def import_csv(
        self,
        *,
        file_path: str | Path,
        company_id: int,
        user_id: int | None = None,
        username: str = "",
        skip_invalid: bool = False,
        encoding: str = "utf-8",
    ) -> ImportProductsOutput:
        """Importa produtos de um arquivo CSV."""

        use_case = ImportProductsUseCase(
            product_repo=self._product_repo,
            result_repo=self._result_repo,
            user_permissions=self._user_permissions,
        )

        return use_case.execute(
            ImportProductsInput(
                file_path=str(file_path),
                company_id=company_id,
                user_id=user_id,
                username=username,
                skip_invalid=skip_invalid,
                encoding=encoding,
            )
        )

    def set_user_permissions(self, permissions: set[str]) -> None:
        """Atualiza as permissões do operador logado."""
        self._user_permissions = permissions
