"""Unit tests for the password policy."""

from __future__ import annotations

import pytest

from erp.modules.identity.domain.password_policy import (
    MIN_PASSWORD_LENGTH,
    validate_password_policy,
)


def test_password_meeting_policy_is_accepted() -> None:
    assert validate_password_policy("senha123") is None


def test_password_with_letters_and_digits_is_accepted() -> None:
    assert validate_password_policy("Abc12345") is None


def test_password_shorter_than_min_is_rejected() -> None:
    short = "a" * (MIN_PASSWORD_LENGTH - 1)
    with pytest.raises(ValueError, match="caracteres"):
        validate_password_policy(short)


def test_password_without_digit_is_rejected() -> None:
    with pytest.raises(ValueError, match="letra e um dígito"):
        validate_password_policy("senhaletrasonly")


def test_password_without_letter_is_rejected() -> None:
    with pytest.raises(ValueError, match="letra e um dígito"):
        validate_password_policy("12345678")