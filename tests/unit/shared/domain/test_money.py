from erp.shared.domain.value_objects import Money


def test_money_creation() -> None:
    m = Money(12345)
    assert m.cents == 12345

def test_money_addition() -> None:
    m1 = Money(1000)
    m2 = Money(500)
    assert (m1 + m2).cents == 1500

def test_money_subtraction() -> None:
    m1 = Money(1000)
    m2 = Money(300)
    assert (m1 - m2).cents == 700

def test_money_multiply_by_integer() -> None:
    m = Money(150)
    assert (m * 3).cents == 450

def test_money_multiply_by_qty() -> None:
    m = Money(1000)
    result = m.multiply_by_qty(1500)
    assert result.cents == 1500

    m2 = Money(1)
    assert m2.multiply_by_qty(1500).cents == 2

    m3 = Money(2)
    assert m3.multiply_by_qty(1500).cents == 3

def test_money_multiply_by_pct() -> None:
    m = Money(10000)
    result = m.multiply_by_pct(600)
    assert result.cents == 600

    m2 = Money(1)
    assert m2.multiply_by_pct(600).cents == 0

def test_money_format_brl() -> None:
    assert Money(123456).format_brl() == "R$ 1.234,56"
    assert Money(50).format_brl() == "R$ 0,50"
    assert Money(0).format_brl() == "R$ 0,00"
    assert Money(-1234).format_brl() == "-R$ 12,34"
