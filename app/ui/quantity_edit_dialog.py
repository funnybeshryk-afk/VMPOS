from app.ui.numeric_entry_dialog import NumericEntryDialog
from app.utils.units import is_weight_unit

_WEIGHT_PRESETS = (("0,5", 0.5), ("1", 1), ("2", 2), ("5", 5))


class QuantityEditDialog(NumericEntryDialog):
    """Korzinadagi miqdorni o'zgartirish — sensorli (raqamli blok)."""

    def __init__(self, product, current_quantity, parent=None, price_for=None):
        weight = is_weight_unit(product.unit)

        super().__init__(
            title="Miqdorni o'zgartirish",
            product=product,
            unit=(product.unit or "").strip() if weight else "ta",
            allow_decimal=weight,
            minimum=0.001 if weight else 1,
            initial=current_quantity,
            presets=_WEIGHT_PRESETS if weight else (),
            price_for=price_for,
            parent=parent,
        )

    def get_quantity(self):
        return self.get_value()
