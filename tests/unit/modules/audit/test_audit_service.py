"""Unit tests for the audit hash-chain logic using a fake repository."""

from __future__ import annotations

from datetime import UTC, datetime

from erp.modules.audit.application.ports import AuditRepository
from erp.modules.audit.domain.audit_log import AuditLog


class FakeAuditRepository(AuditRepository):
    def __init__(self) -> None:
        self._entries: list[AuditLog] = []

    def add(self, entry: AuditLog) -> None:
        entry.id = len(self._entries) + 1
        self._entries.append(entry)

    def list_all(self) -> list[AuditLog]:
        return list(self._entries)

    def verify_chain(self) -> bool:
        expected_prev = "0" * 64
        for entry in self._entries:
            expected_hash = self._compute_hash(entry, expected_prev)
            if entry.hash != expected_hash:
                return False
            expected_prev = entry.hash
        return True

    @staticmethod
    def _compute_hash(entry: AuditLog, prev_hash: str) -> str:
        import hashlib

        payload = (
            f"{prev_hash}|{entry.user_id}|{entry.username}|"
            f"{entry.action}|{entry.entity_type}|{entry.entity_id}|"
            f"{entry.before}|{entry.after}|{entry.created_at.isoformat()}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _make_entry(
    action: str = "company.create",
    username: str = "admin",
    prev_hash: str = "0" * 64,
) -> AuditLog:
    return AuditLog(
        user_id=1,
        username=username,
        action=action,
        entity_type="Company",
        entity_id=1,
        before="{}",
        after='{"name": "ACME"}',
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        prev_hash=prev_hash,
    )


def test_fake_repo_chain_valid() -> None:
    repo = FakeAuditRepository()
    entry1 = _make_entry(action="company.create")
    entry1.hash = repo._compute_hash(entry1, entry1.prev_hash)
    repo.add(entry1)

    entry2 = _make_entry(action="company.update", prev_hash=entry1.hash)
    entry2.hash = repo._compute_hash(entry2, entry1.hash)
    repo.add(entry2)

    assert repo.verify_chain() is True


def test_fake_repo_chain_detects_tampering() -> None:
    repo = FakeAuditRepository()
    entry1 = _make_entry(action="company.create")
    entry1.hash = repo._compute_hash(entry1, entry1.prev_hash)
    repo.add(entry1)

    entry2 = _make_entry(action="company.update", prev_hash=entry1.hash)
    entry2.hash = repo._compute_hash(entry2, entry1.hash)
    repo.add(entry2)

    assert repo.verify_chain() is True

    # Tamper with the first entry's after field
    entry1.after = '{"name": "TAMPERED"}'
    assert repo.verify_chain() is False
