"""CNPJ normalization and validation utilities."""

from __future__ import annotations


def normalize_cnpj(cnpj: str) -> str:
    """Remove all non-digits from CNPJ. Returns 14-digit string or empty."""
    if not cnpj:
        return ""
    return "".join(ch for ch in cnpj if ch.isdigit())


def format_cnpj(cnpj: str) -> str:
    """Format 14-digit CNPJ as XX.XXX.XXX/XXXX-XX."""
    digits = normalize_cnpj(cnpj)
    if len(digits) != 14:
        return cnpj  # return as-is if invalid length
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"


def is_valid_cnpj(cnpj: str) -> bool:
    """Validate CNPJ using modulus 11 algorithm."""
    digits = normalize_cnpj(cnpj)
    if len(digits) != 14:
        return False

    # Check for all same digits (invalid)
    if len(set(digits)) == 1:
        return False

    # First digit
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum1 = sum(int(digits[i]) * weights1[i] for i in range(12))
    digit1 = 11 - (sum1 % 11)
    if digit1 >= 10:
        digit1 = 0

    # Second digit
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum2 = sum(int(digits[i]) * weights2[i] for i in range(13))
    digit2 = 11 - (sum2 % 11)
    if digit2 >= 10:
        digit2 = 0

    return int(digits[12]) == digit1 and int(digits[13]) == digit2