from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QCheckBox, QPushButton, QHBoxLayout, QLabel, QDoubleSpinBox

from gui_styles.stylesheets import button_parameters_style, box_render_style, checkbox_style

class FieldLinesControlPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Field line options", parent)
        self.setStyleSheet(box_render_style())
        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        # Plane: XY or ZX
        self.cb_xy = QCheckBox("XY plane")
        self.cb_xy.setChecked(True)
        self.cb_zx = QCheckBox("ZX plane")
        for cb in (self.cb_xy, self.cb_zx):
            cb.setStyleSheet(checkbox_style())

        row1 = QHBoxLayout()
        row1.addWidget(self.cb_xy)
        row1.addWidget(self.cb_zx)

        # Central solenoid / all
        self.cb_center = QCheckBox("Central solenoid")
        self.cb_center.setChecked(True)
        self.cb_all = QCheckBox("All solenoids")
        self.cb_all.setChecked(True)
        for cb in (self.cb_center, self.cb_all):
            cb.setStyleSheet(checkbox_style())

        row2 = QHBoxLayout()
        row2.addWidget(self.cb_center)
        row2.addWidget(self.cb_all)

        # Plane value
        self.label_plane_value = QLabel("Plane value (Z/Y):")
        self.spin_plane_value = QDoubleSpinBox()
        self.spin_plane_value.setRange(-1.0, 1.0)
        self.spin_plane_value.setDecimals(3)
        self.spin_plane_value.setSingleStep(0.01)
        self.spin_plane_value.setValue(0.01)

        row3 = QHBoxLayout()
        row3.addWidget(self.label_plane_value)
        row3.addWidget(self.spin_plane_value)

        # Resolution
        self.label_resolution = QLabel("Resolution:")
        self.spin_resolution = QDoubleSpinBox()
        self.spin_resolution.setRange(10, 500)
        self.spin_resolution.setValue(100)
        self.spin_resolution.setSingleStep(10)

        row4 = QHBoxLayout()
        row4.addWidget(self.label_resolution)
        row4.addWidget(self.spin_resolution)

        self.btn_update = QPushButton("Update field lines")
        self.btn_update.setStyleSheet(button_parameters_style())

        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addLayout(row3)
        layout.addLayout(row4)
        layout.addWidget(self.btn_update)
        self.setLayout(layout)

    def get_params(self):
        return dict(
            XY=self.cb_xy.isChecked(),
            ZX=self.cb_zx.isChecked(),
            Solenoid_Center=self.cb_center.isChecked(),
            All_Solenoids=self.cb_all.isChecked(),
            Plane_Value=self.spin_plane_value.value(),
            resolution=int(self.spin_resolution.value())
        )
