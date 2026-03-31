from src.tool_calling_example import calculate


def test_calculate_basic_arithmetic() -> None:
    assert calculate("2 + 2") == 4.0


def test_calculate_complex_expression() -> None:
    assert calculate("(123 * 456) + 789") == 56877.0


def test_calculate_division() -> None:
    assert calculate("100 / 4") == 25.0
