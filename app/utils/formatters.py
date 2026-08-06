from decimal import Decimal, ROUND_HALF_UP


def parse_number(value):
    normalized_value = (
        str(value)
        .replace(" ", "")
        .replace(",", ".")
    )

    return float(normalized_value or 0)


def format_money(value):
    amount = Decimal(str(value or 0)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    formatted_value = f"{amount:,.2f}"
    formatted_value = (
        formatted_value
        .replace(",", " ")
        .replace(".", ",")
    )

    if formatted_value.endswith(",00"):
        return formatted_value[:-3]

    return formatted_value


def format_quantity(value):
    number = Decimal(str(value or 0)).quantize(
        Decimal("0.001"),
        rounding=ROUND_HALF_UP,
    )

    formatted_value = f"{number:f}".replace(".", ",")

    return formatted_value.rstrip("0").rstrip(",")