"""Security audit utilities and evidence collection."""

from __future__ import annotations

import logging
import re
from pathlib import Path


class SecurityAuditor:
    """Security auditor for collecting evidence of security compliance."""

    def __init__(self, project_root: Path | None = None) -> None:
        self._project_root = project_root or Path.cwd()
        self._logger = logging.getLogger("erp.security")

    def check_permissions_not_only_in_ui(self) -> dict[str, list[str]]:
        """Check that permission checks exist in application layer, not only UI.

        Returns:
            Dict mapping module names to list of use cases with permission checks.
        """
        results = {}

        # Check application services for permission checks
        app_dirs = list(self._project_root.glob("src/erp/modules/*/application/"))
        for app_dir in app_dirs:
            module_name = app_dir.parent.name
            service_files = list(app_dir.glob("**/services.py")) + list(
                app_dir.glob("**/service.py")
            )
            use_cases_with_perms = []

            for svc_file in service_files:
                content = svc_file.read_text(encoding="utf-8")
                # Look for permission checks
                if re.search(r"permission|Permission|can_|requires_", content):
                    use_cases_with_perms.append(svc_file.relative_to(self._project_root).as_posix())

            if use_cases_with_perms:
                results[module_name] = use_cases_with_perms

        return results

    def check_no_passwords_in_logs(self) -> dict[str, list[str]]:
        """Check that passwords/hashes are never logged.

        Returns:
            Dict with 'violations' list of files/lines where passwords might be logged.
        """
        violations = []

        # Patterns that might indicate password logging
        password_patterns = [
            r"password",
            r"password_hash",
            r"senha",
            r"hash",
            r"credentials?",
            r"token",
            r"secret",
        ]

        py_files = list(self._project_root.glob("src/**/*.py"))
        for py_file in py_files:
            content = py_file.read_text(encoding="utf-8")
            lines = content.splitlines()

            for i, line in enumerate(lines, 1):
                # Skip comments and strings that are clearly not logging
                if line.strip().startswith("#"):
                    continue

                # Check for logging calls with password-like terms
                logging_pattern = r"logger\.(debug|info|warning|error|critical)\("
                log_pattern = r"log\.(debug|info|warning|error|critical)\("
                if re.search(logging_pattern, line) or re.search(log_pattern, line):
                    for pattern in password_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            violations.append(
                                f"{py_file.relative_to(self._project_root)}:{i}: {line.strip()}"
                            )

        return {"violations": violations}

    def check_sql_injection_risk(self) -> dict[str, list[str]]:
        """Check for potential SQL injection risks (text() with f-strings/concatenation).

        Returns:
            Dict with 'risks' list of files/lines where SQL is built dynamically.
        """
        risks = []

        py_files = list(self._project_root.glob("src/**/*.py"))
        for py_file in py_files:
            content = py_file.read_text(encoding="utf-8")
            lines = content.splitlines()

            for i, line in enumerate(lines, 1):
                # Look for text() with f-strings or string concatenation
                if "text(" in line:
                    # Check if it contains f-string or concatenation
                    has_fstring = 'f"' in line or "f'" in line
                    has_concat = "+" in line
                    is_param = ":param" in line or ":cid" in line or ":id" in line
                    if (has_fstring or has_concat) and not is_param:
                        risks.append(
                            f"{py_file.relative_to(self._project_root)}:{i}: {line.strip()}"
                        )

        return {"risks": risks}

    def check_company_id_filtering(self) -> dict[str, list[str]]:
        """Check that repository queries on company-scoped tables filter by company_id.

        Returns:
            Dict with 'missing_filters' list of files/queries that might miss company_id.
        """
        missing = []

        # Tables that should always be filtered by company_id
        company_tables = [
            "products",
            "categories",
            "suppliers",
            "sales",
            "sale_items",
            "sale_payments",
            "cash_sessions",
            "cash_movements",
            "cash_registers",
            "financial_entries",
            "stock_movements",
            "price_histories",
            "payables",
            "payable_installments",
            "receivables",
            "financial_categories",
        ]

        py_files = list(self._project_root.glob("src/**/repository*.py")) + list(
            self._project_root.glob("src/**/infrastructure/repository.py")
        )
        for py_file in py_files:
            content = py_file.read_text(encoding="utf-8")

            for table in company_tables:
                # Look for SELECT/UPDATE/DELETE on company tables
                pattern = rf"(SELECT|UPDATE|DELETE).*\b{table}\b"
                matches = re.finditer(pattern, content, re.IGNORECASE)

                for match in matches:
                    # Get surrounding context
                    start = max(0, match.start() - 200)
                    end = min(len(content), match.end() + 200)
                    context = content[start:end]

                    # Check if company_id filter is present
                    if "company_id" not in context:
                        # Get line number
                        line_no = content[: match.start()].count("\n") + 1
                        missing.append(
                            f"{py_file.relative_to(self._project_root)}:{line_no}: "
                            f"Query on {table} may miss company_id filter"
                        )

        return {"missing_filters": missing}

    def run_full_audit(self) -> dict[str, dict[str, list[str]] | dict[str, list[object]]]:
        """Run all security checks and return combined results."""
        return {
            "permissions_in_app_layer": self.check_permissions_not_only_in_ui(),
            "no_passwords_in_logs": self.check_no_passwords_in_logs(),
            "sql_injection_risk": self.check_sql_injection_risk(),
            "company_id_filtering": self.check_company_id_filtering(),
        }


def run_security_audit() -> dict[str, dict[str, list[str]] | dict[str, list[object]]]:
    """Run security audit from project root."""
    auditor = SecurityAuditor()
    return auditor.run_full_audit()


if __name__ == "__main__":
    import json

    results = run_security_audit()
    print(json.dumps(results, indent=2, ensure_ascii=False))
