def format_money(value):
    amount = int(round(float(value or 0)))
    return f"{amount:,}".replace(",", " ")


def format_quantity(value):
    number = float(value or 0)

    if number.is_integer():
        return str(int(number))

    return (
        f"{number:.3f}"
        .rstrip("0")
        .rstrip(".")
        .replace(".", ",")
    )


def parse_number(value):
    normalized_value = (
        str(value)
        .replace(" ", "")
        .replace(",", ".")
    )

    return float(normalized_value or 0)