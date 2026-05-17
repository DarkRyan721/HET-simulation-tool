from PySide6.QtWidgets import (
    QWidget, QLineEdit, QLabel, QHBoxLayout
)

from gui_styles.stylesheets import input_unit_chip_style


def _input_with_unit(default_value: str, unit: str):
    """
    Composite widget: QLineEdit + unit chip label.

    The unit is rendered as a small pill on the right side of the input,
    consistent with the rest of the design system.
    """
    field = QLineEdit(default_value)
    field.setClearButtonEnabled(False)

    unit_label = QLabel(unit.strip("[]").strip() if unit else "")
    unit_label.setObjectName("UnitChip")
    unit_label.setStyleSheet(input_unit_chip_style())
    unit_label.setVisible(bool(unit_label.text()))

    layout = QHBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    layout.addWidget(field, 1)
    layout.addWidget(unit_label, 0)

    container = QWidget()
    container.setLayout(layout)

    return container, field
