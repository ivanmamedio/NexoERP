"""Unit tests for User domain entity."""

from __future__ import annotations

import pytest

from erp.modules.identity.domain.user import User


def test_user_creation() -> None:
    user = User(
        username="joao",
        password_hash="hash123",
        must_change_password=True,
        is_active=True,
    )
    assert user.username == "joao"
    assert user.must_change_password is True
    assert user.is_active is True
    assert user.failed_login_attempts == 0


def test_user_record_failed_login_blocks_after_5() -> None:
    """Bloqueia após 5 tentativas falhas."""
    user = User(username="joao", password_hash="hash123", is_active=True)
    for _ in range(4):
        user.record_failed_login()
    assert user.failed_login_attempts == 4
    assert user.is_locked() is False

    user.record_failed_login()
    assert user.failed_login_attempts == 5
    assert user.is_locked() is True


def test_user_reset_failed_logins() -> None:
    user = User(username="joao", password_hash="hash123", is_active=True)
    user.record_failed_login()
    user.record_failed_login()
    assert user.failed_login_attempts == 2

    user.reset_failed_logins()
    assert user.failed_login_attempts == 0
    assert user.is_locked() is False
