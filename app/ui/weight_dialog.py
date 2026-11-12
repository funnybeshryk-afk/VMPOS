from app.ui.numeric_entry_dialog import NumericEntryDialog

_PRESETS = (("0,5", 0.5), ("1", 1), ("2", 2), ("5", 5))


class WeightDialog(NumericEntryDialog):
    """Og'irlikni kiritish (kg) — sensorli: raqamli blok va tezkor
    qiymatlar; jami summa real vaqtda."""

    def __init__(self, product, parent=None, price_for=None):
        super().__init__(
            title="Og'irlikni kiriting",
            product=product,
            unit="kg",
            allow_decimal=True,
            minimum=0.001,
            initial=1,
            presets=_PRESETS,
            price_for=price_for,
            price_caption="so'm / kg",
            parent=parent,
        )

    def get_weight(self):
        return self.get_value()
