from PySide6.QtWidgets import (
    QWidget, QLineEdit, QLabel, QHBoxLayout
)

def _input_with_unit(default_value: str, unit: str):
    """
    Creates a composite widget containing a QLineEdit field alongside a QLabel displaying a unit.

    This is useful for input fields that require a numerical or textual value along with a unit label
    (e.g., "5.0" and "m/s").

    Args:
        default_value (str): The initial text to populate the QLineEdit.
        unit (str): The unit string to display next to the input field.

    Returns:
        tuple: A tuple containing:
            - container (QWidget): The QWidget containing the horizontal layout with input and unit label.
            - field (QLineEdit): The editable text field widget for user input.
    """
    # Create the editable input field initialized with the default value
    field = QLineEdit(default_value)

    # Create the label for the unit and style it to have a gray color and left padding
    unit_label = QLabel(unit)
    unit_label.setStyleSheet("color: gray; padding-left: 5px;")

    # Create a horizontal box layout to place input and label side by side without margins
    layout = QHBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(field)
    layout.addWidget(unit_label)

    # Create a container widget and assign the layout to it
    container = QWidget()
    container.setLayout(layout)

    return container, field
