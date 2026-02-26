import os
import time

import numpy as np
import pyvista as pv

from pyvistaqt import QtInteractor

from widgets.panels.collapse import CollapsibleBox
from PySide6.QtWidgets import QMessageBox

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, QLineEdit, QLabel,
    QHBoxLayout, QPushButton, QCheckBox, QSlider, QComboBox
)
from PySide6.QtCore import Qt
import PySide6.QtWidgets as QtW
from PySide6.QtCore import QThread, Signal, QObject, QTimer

from PySide6.QtWidgets import QProgressDialog

import subprocess
import json
from PySide6.QtCore import QTimer

# ──────────────────────────────────────────────
# 🧩 Módulos propios
from mesh_generator import HallThrusterMesh
from electric_field_solver import ElectricFieldSolver
from gui_styles.stylesheets import *
from widgets.parameter_views import ParameterPanel
from widgets.options_panel import OptionsPanel
from widgets.view_panel import ViewPanel
from utils.loader_thread import LoaderWorker
from utils.ui_helpers import _input_with_unit
from project_paths import data_file, model, temp_data_file, project_file, worker
from PySide6.QtWidgets import QVBoxLayout, QPushButton, QWidget, QLabel, QFrame
from PySide6.QtWidgets import QVBoxLayout, QPushButton, QWidget, QLabel, QFrame
from utils.loading_bar import ProgressBarWidget

class FieldOptionsPanel(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.solver_instance = ElectricFieldSolver()
        self.simulation_state = self.main_window.simulation_state
        self.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(self)

        # ──────────────────────────────────────────────────────────────
        # 1. Grupo: Parámetros de simulación física
        field_box = QGroupBox("⚡ Parámetros físicos (Simulación)")
        field_box.setStyleSheet(box_render_style())
        sim_layout = QFormLayout()

        lbl_volt = QLabel("Voltaje de ánodo [V]:")
        lbl_volt.setToolTip("Diferencia de potencial aplicada entre el ánodo y el cátodo.")
        self.input_Volt_container, self.input_Volt = _input_with_unit(str(self.simulation_state.voltage), "[V]")

        lbl_cath = QLabel("Voltaje de cátodo [V]:")
        lbl_cath.setToolTip("Potencial aplicado al cátodo respecto a tierra.")

        self.input_Volt_Cath_container, self.input_Volt_Cath = _input_with_unit(str(self.simulation_state.voltage_cathode), "[V]")

        sim_layout.addRow(lbl_volt, self.input_Volt_container)
        sim_layout.addRow(lbl_cath, self.input_Volt_Cath_container)

        self.charge_density_check = QCheckBox("Habilitar densidad de carga")
        self.charge_density_check.setToolTip("Activa la resolución de Poisson incluyendo densidad electrónica.")
        self.charge_density_check.setChecked(False)
        self.charge_density_check.setStyleSheet(checkbox_parameters_style())
        # self.charge_density_check.stateChanged.connect(
        #     lambda state: self.main_window.launch_worker(
        #         LoaderWorker(
        #             mode="field",
        #             params={"validate_density": (state == Qt.Checked)}
        #         ),
        #         self.on_field_loaded
        #     )
        # )
        sim_layout.addRow(self.charge_density_check)

        field_box.setLayout(sim_layout)
        layout.addWidget(field_box)

        # ──────────────────────────────────────────────────────────────
        # 2. Grupo: Acciones de simulación
        actions_box = QGroupBox("Acciones de simulación")
        actions_box.setStyleSheet(box_render_style())
        actions_layout = QHBoxLayout()
        self.update_btn = QPushButton("Actualizar campo")
        self.update_btn.setStyleSheet(button_parameters_style())
        self.update_btn.setToolTip("Ejecuta el cálculo del campo eléctrico con los parámetros actuales.")
        self.update_btn.clicked.connect(self.on_update_clicked_Electric_field)
        actions_layout.addWidget(self.update_btn)
        actions_box.setLayout(actions_layout)
        layout.addWidget(actions_box)

        # ──────────────────────────────────────────────────────────────
        # 3. Grupo: Visualización
        vis_box = QGroupBox("Parámetros de visualización")
        vis_box.setStyleSheet(box_render_style())
        vis_layout = QFormLayout()

        lbl_quantity = QLabel("Magnitud a visualizar:")
        lbl_quantity.setToolTip("Selecciona entre campo eléctrico o densidad electrónica.")
        self.combo = QComboBox()
        self.combo.addItems(["Electric Field", "Electron Density"])
        self.combo.setStyleSheet(box_render_style())
        self.combo.currentTextChanged.connect(self.switch_dataset)
        vis_layout.addRow(lbl_quantity, self.combo)

        lbl_viewmode = QLabel("Modo de vista:")
        lbl_viewmode.setToolTip("Vista 3D o corte 2D en el plano ZY.")
        self.view_mode_combo = QComboBox()
        self.view_mode_combo.addItems(["3D", "2D Slice ZY"])
        self.view_mode_combo.setStyleSheet(box_render_style())
        self.view_mode_combo.currentTextChanged.connect(self.update_view_mode)
        vis_layout.addRow(lbl_viewmode, self.view_mode_combo)

        lbl_zslice = QLabel("Plano X para corte (solo modo 2D):")
        lbl_zslice.setToolTip("Valor de X donde se realiza el corte (en metros).")
        self.z_value_edit = QLineEdit()
        self.z_value_edit.setPlaceholderText("Ej: 0.01")
        self.z_value_edit.setEnabled(False)
        self.z_value_edit.editingFinished.connect(self.update_z_value)
        vis_layout.addRow(lbl_zslice, self.z_value_edit)

        lbl_viewdir = QLabel("Orientación de cámara:")
        self.view_direction_combo = QComboBox()
        self.view_direction_combo.addItems([
            "Isometric", "XY (Top)", "ZY (Front)", "ZX (Side)", "XZ (Bottom)", "YX (Back)"
        ])
        self.view_direction_combo.setStyleSheet(box_render_style())
        self.view_direction_combo.currentTextChanged.connect(self.change_view_direction)
        vis_layout.addRow(lbl_viewdir, self.view_direction_combo)
        vis_box.setLayout(vis_layout)
        layout.addWidget(vis_box)

        self.progress_bar = ProgressBarWidget("Calculando campo eléctrico...")
        layout.addWidget(self.progress_bar)
        self.progress_bar.hide()


        # ──────────────────────────────────────────────────────────────
        # 4. Visualizador 3D
        self.field_viewer = self._create_viewer()
        layout.addWidget(self.field_viewer)

        layout.addStretch()
        self.setLayout(layout)

        # Carga inicial de datos si existen
        self.current_field = None
        self.current_density = None
        self.current_z_value = 0.01
        self.current_z_index = 0
        self.z_values = None
        self._load_initial_field_if_exists()
        self._load_initial_density_if_exists()


    def update_view(self):
        if self.combo.currentText() == "Electric Field":
            self.visualize_field()
        elif self.combo.currentText() == "Electron Density":
            self.visualize_density()

    def _create_viewer(self):
        viewer = QtInteractor()
        viewer.set_background("white")
        viewer.setStyleSheet("background-color: white; border-radius: 5px;")
        viewer.add_axes(interactive=False)
        viewer.setSizePolicy(QtW.QSizePolicy.Expanding, QtW.QSizePolicy.Expanding)
        viewer.view_zx()
        return viewer

    def on_update_clicked_Electric_field(self):
        campos = {
            'Voltaje': self.input_Volt.text(),
            'Voltaje_Cath': self.input_Volt_Cath.text(),
        }

        try:
            valores = self.validar_numeros(campos)
        except ValueError as e:
            from PySide6.QtWidgets import QMessageBox
            print(str(e))
            QMessageBox.critical(self, "Error de validación", str(e))
            return

        voltaje = valores['Voltaje']
        voltaje_Cath = valores['Voltaje_Cath']
        validate_density = self.charge_density_check.isChecked()

        self.simulation_state.voltage = voltaje
        self.simulation_state.voltage_cathode = voltaje_Cath

        new_params = [voltaje, voltaje_Cath]
        params = {
            "voltage": voltaje,
            "voltage_cathode": voltaje_Cath,
            "validate_density": validate_density
        }
        print("validate density:", validate_density)
        if new_params != self.simulation_state.prev_params_field or self.simulation_state.field_outdated:
            print("🔄 ¡Parámetros cambiaron:", new_params)
            self.simulation_state.prev_params_field = new_params
            self.simulation_state.save_to_json(model("simulation_state.json"))
            self.progress_bar.start("Calculando campo eléctrico...")
            self.update_btn.setEnabled(False)

            self.run_process_and_reload(
                process_script="electric_field_process.py",
                loader_mode="field",
                finished_callback= self.on_field_loaded_file
            )
            return
        else:
            from PySide6.QtWidgets import QMessageBox
            print("⚠️ No se han realizado cambios en los parámetros del campo.")
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Sin cambios detectados")
            msg.setText("Debe cambiar los parámetros para ejecutar una nueva simulación del campo eléctrico.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setStyleSheet("QLabel{min-width: 300px;}")
            msg.exec()

        self.loader_worker_field = LoaderWorker(
            mode="field",
            params=params,
        )
        self.main_window.launch_worker(self.loader_worker_field, self.on_field_loaded)

        print("Finalizando con la actualización")
        self.simulation_state.print_state()

        self.field_viewer.setEnabled(True)
        self.field_viewer.show()
        self.worker = None
        self.thread = None

    def validar_numeros(self, campos):
        """
        Valida que todos los valores sean numéricos y no vacíos.
        """
        resultados = {}
        for nombre, texto in campos.items():
            texto = str(texto).strip()
            if not texto:
                raise ValueError(f"El campo '{nombre}' es obligatorio y está vacío.")
            try:
                valor = float(texto)
            except ValueError:
                raise ValueError(f"El campo '{nombre}' debe ser un número válido. Valor recibido: '{texto}'")
            resultados[nombre] = valor
        return resultados

    def on_field_loaded(self, data):
        self.current_field = data
        self.update_view()

    def on_field_loaded_file(self, data):
        self.simulation_state.field_outdated = False
        self.current_field = data
        self.simulation_state.field_outdated = False
        self.simulation_state.save_to_json(model("simulation_state.json"))
        self.update_view()

    def on_density_loaded(self, data):
        self.current_density = data
        if self.view_mode_combo.currentText() == "2D Slice ZY":
            self.update_z_slider_range()
        self.update_view()

    def change_view_direction(self, text):
        # Elimina los métodos interactivos del viewer si hay alguno
        viewer = self.field_viewer
        # Puedes limpiar la cámara o ejes si lo deseas aquí

        if text == "Isometric":
            viewer.view_isometric()
        elif text == "XY (Top)":
            viewer.view_xy()
        elif text == "ZY (Front)":
            viewer.view_zy()
        elif text == "ZX (Side)":
            viewer.view_zx()
        elif text == "XZ (Bottom)":
            viewer.view_xz()
        elif text == "YX (Back)":
            viewer.view_yx()
        # Después de cambiar, puedes resetear la cámara si es necesario
        viewer.reset_camera()

    def visualize_field(self):
        if self.current_field is None:
            print("No hay datos de campo eléctrico para visualizar.")
            return

        self.field_viewer.clear()
        self.field_viewer.set_background("white")
        self.field_viewer.add_axes(interactive=False)

        mode = self.view_mode_combo.currentText()
        if mode == "3D":
            # glyphs = self.current_field.glyph(orient="E_field", scale=False, factor=0.01)
            # self.field_viewer.add_mesh(glyphs, scalars="magnitude", cmap="plasma")
            glyphs = self.current_field.glyph(
                orient="E_field",       # nombre del vector en tu PolyData
                scale=False,            # no escalar por magnitud
                factor=0.01

            )
            self.field_viewer.add_mesh(
                glyphs,
                cmap="plasma",                   # paleta académica
                scalars="magnitude",            # colorea por magnitud del campo
                clim=[
                    self.current_field["magnitude"].min(),
                    self.current_field["magnitude"].max()
                ],
                line_width=0.03,                 # flechas delgadas
                opacity=1,                    # ligeramente transparente
                show_scalar_bar=True,           # barra de colores (quita si no la quieres)
                render_points_as_spheres=False, # no muestres nodos como esferas
                lighting=True,
                scalar_bar_args={"title": "|Log10(E)| [V/m]"}

            )
            self.field_viewer.view_isometric()
            pos, fp, viewup = self.field_viewer.camera_position
            # Invertir la dirección de la cámara respecto al foco (fp)
            inverted_pos = (2*fp[0] - pos[0], 2*fp[1] - pos[1], 2*fp[2] - pos[2])
            self.field_viewer.camera_position = [inverted_pos, fp, viewup]
            self.field_viewer.reset_camera()
            self.field_viewer.add_text("Campo eléctrico", position='upper_edge', font_size=6, color='black')
        elif mode == "2D Slice ZY":
            # ---- PROYECTAR EN EL PLANO X = x_plane ----
            x_plane = self.current_z_value
            tolerance = 0.008
            mesh = self.current_field
            mask = np.abs(mesh.points[:, 0] - x_plane) <= tolerance

            if not np.any(mask):
                self.field_viewer.add_text("Sin datos en este plano", color="black", font_size=16)
                return

            # Proyectar puntos al plano X=x_plane
            points = mesh.points[mask].copy()
            points[:, 0] = x_plane

            # Proyectar solo las componentes Z, Y del campo (poniendo X=0)
            if "E_field" not in mesh.point_data:
                self.field_viewer.add_text("No hay campo E_field en los datos", color="black", font_size=16)
                return
            vectors = mesh.point_data["E_field"][mask]
            vectors_proj = vectors.copy()
            vectors_proj[:, 0] = 0  # Quitar la componente X

            # PolyData con los puntos proyectados y vectores proyectados
            projected = pv.PolyData(points)
            projected["vectors"] = vectors_proj
            # Si quieres, también puedes proyectar el escalar de magnitud
            if "magnitude" in mesh.point_data:
                projected["magnitude"] = mesh.point_data["magnitude"][mask]

            # ---- GRAFICAR GLYPHS (FLECHAS) ----
            glyphs = projected.glyph(    orient="vectors",
            scale=False,
            factor=0.01)
            self.field_viewer.add_mesh(    glyphs,
            cmap="plasma",            # Paleta neutra y académica
            scalars="magnitude",
            clim=[
                self.current_field["magnitude"].min(),
                self.current_field["magnitude"].max()
            ],
            line_width=0.45,            # Muy delgadas
            opacity=0.7,              # Suave, no saturado
            show_scalar_bar=True,      # Quita si no lo necesitas
            render_points_as_spheres=False,
            lighting=False,
            # scalar_bar_args={"title": "|E| [V/m]"})
            scalar_bar_args={"title": "|Log10(E)| [V/m]"})


            self.field_viewer.view_zy()
            self.field_viewer.add_text("Campo eléctrico (proyección ZY)", position='upper_edge', font_size=12, color='black')
        # Puedes agregar aquí el modo de líneas de campo (ver más abajo)
        self.field_viewer.reset_camera()

    def project_to_plane(mesh, z_plane=0.0, tolerance=None):
        points = mesh.points.copy()
        # Si quieres proyectar TODOS los puntos al plano Z
        points[:, 2] = z_plane

        # Si solo quieres proyectar puntos dentro de un rango de Z (por ejemplo +-0.01)
        if tolerance is not None:
            mask = np.abs(mesh.points[:, 2] - z_plane) <= tolerance
            points = points[mask]
            # Asegúrate de filtrar los datos asociados si usas esta opción (ver abajo)

        # Crear un nuevo mesh con los puntos proyectados (manteniendo los scalars y/o vectors)
        projected = pv.PolyData(points)
        # Copia scalars (ejemplo: 'n0_log')
        for name in mesh.point_data:
            data = mesh.point_data[name]
            if tolerance is not None:
                data = data[mask]
            projected.point_data[name] = data
        return projected

    def filter_and_project_to_plane_z(self, mesh, z_plane=0.0, tolerance=0.015):
        # Filtra solo los puntos cercanos al plano Z
        mask = np.abs(mesh.points[:, 2] - z_plane) <= tolerance
        if not np.any(mask):
            return None
        points = mesh.points[mask].copy()
        points[:, 2] = z_plane  # Proyecta a plano Z exacto

        projected = pv.PolyData(points)
        # Copia point_data (por ejemplo, 'n0_log' o 'magnitude')
        for name in mesh.point_data:
            projected.point_data[name] = mesh.point_data[name][mask]
        # Copia vectores si existen (ejemplo: 'vectors' o 'E_field')
        for name in mesh.point_data:
            if mesh.point_data[name].ndim == 2 and mesh.point_data[name].shape[1] == 3:
                projected.point_data[name] = mesh.point_data[name][mask]
        return projected

    def filter_and_project_to_plane_x(self, mesh, x_plane=0.0, tolerance=0.015):
        mask = np.abs(mesh.points[:, 0] - x_plane) <= tolerance
        if not np.any(mask):
            return None
        points = mesh.points[mask].copy()
        points[:, 0] = x_plane  # Proyecta todos al plano X exacto

        projected = pv.PolyData(points)
        for name in mesh.point_data:
            projected.point_data[name] = mesh.point_data[name][mask]
        return projected

    def visualize_density(self):
        if self.current_density is None:
            print("No hay datos de densidad para visualizar.")
            return

        dens = self.current_density
        self.field_viewer.clear()
        self.field_viewer.set_background("white")
        self.field_viewer.add_axes(color="black")

        mode = self.view_mode_combo.currentText()
        if mode == "3D":
            self.field_viewer.set_background("white")
            self.field_viewer.add_axes(color="black")
            self.field_viewer.add_mesh(
                dens["density"],
                scalars="n0_log",
                cmap="plasma",
                clim=[dens["log_min"], dens["log_max"]],
                point_size=2,
                render_points_as_spheres=True,
                scalar_bar_args={
                    'title': "ne [m⁻³] (log₁₀)\n",
                    'color': 'black',
                    'fmt': "%.1f",
                }
            )
        elif mode == "2D Slice ZY":
            # slice_mesh = self.get_slice_at_z(dens["density"])
            # slice_mesh = self.project_to_plane(dens["density"], z_plane=self.current_z_value)
            slice_mesh = self.filter_and_project_to_plane_x(dens["density"], x_plane=self.current_z_value)
            if slice_mesh is not None and slice_mesh.n_points > 0:
                self.field_viewer.set_background("white")
                self.field_viewer.add_axes(color="black")

                self.field_viewer.add_mesh(
                    slice_mesh,
                    scalars="n0_log",
                    cmap="plasma",
                    clim=[dens["log_min"], dens["log_max"]],
                    point_size=2,
                    render_points_as_spheres=True,
                    scalar_bar_args={
                        'title': "ne [m⁻³] (log₁₀)\n",
                        'color': 'black',
                        'fmt': "%.1f",
                    }
                )
                self.field_viewer.view_zy()
                self.field_viewer.add_text("Distribución de Densidad Electrónica", position='upper_edge', font_size=12, color='black')

            else:
                print("No hay puntos en el plano Z={} para la densidad.".format(self.current_z_value))
                # Opcional: Puedes mostrar un mensaje en el viewer o limpiar la vista
                self.field_viewer.clear()
                self.field_viewer.add_text(f"Sin datos en Z={self.current_z_value:.2f}", color="black", font_size=16)
        self.field_viewer.reset_camera()

    def update_view_mode(self, mode):
        if mode == "2D Slice ZY":
            self.z_value_edit.setEnabled(True)
        else:
            self.z_value_edit.setEnabled(False)
        self.update_view()

    def update_z_value(self):
        # Lee el valor directamente del QLineEdit
        try:
            z = float(self.z_value_edit.text())
        except Exception:
            z = 0.0  # Valor por defecto si hay error
        self.current_z_value = z
        self.update_view()

    def switch_dataset(self, view_name):
        self.update_view()

    def get_slice_at_z(self, mesh, tol=1e-6):
        z = self.current_z_value
        # Busca el valor Z más cercano si hay valores únicos
        try:
            zs = np.unique(mesh.points[:, 2])
            closest = zs[np.abs(zs - z).argmin()]
            if abs(closest - z) > tol:
                print(f"Aviso: el Z más cercano encontrado es {closest:.6f} (input={z:.6f})")
            z = closest
        except Exception:
            pass

        try:
            slice_mesh = mesh.slice(normal='x', origin=(0, 0, z))
            return slice_mesh
        except Exception as e:
            print(f"Error generando corte ZY en z={z}: {e}")
            return None

    def switch_dataset(self, view_name):
        if view_name == "Electric Field":
            self.visualize_field()
        elif view_name == "Electron Density":
            self.visualize_density()

    def _load_initial_field_if_exists(self):
        path = data_file("E_Field_Laplace.npy")
        if os.path.exists(path):
            worker = LoaderWorker(
                mode="field",
                params={"validate_density": self.charge_density_check.isChecked()},
                solver=self.solver_instance
            )
            self.main_window.launch_worker(worker, self.on_field_loaded)

    def _load_initial_density_if_exists(self):
        path = data_file("density_n0.npy")
        if os.path.exists(path):
            worker = LoaderWorker(mode="density")
            self.main_window.launch_worker(worker, self.on_density_loaded)

    def run_process_and_reload(self, process_script, loader_mode, finished_callback):
        args = ['python3', worker(process_script)]
        self.process = subprocess.Popen(args)
        self.process_start_time = time.perf_counter()
        self.process_finished = False

        def check_output():
            if self.process is None:
                self.timer.stop()
                return
            if self.process.poll() is not None:
                self.timer.stop()
                self.process_finished = True
                elapsed = time.perf_counter() - self.process_start_time

                stdout, stderr = self.process.communicate()
                exit_code = self.process.returncode
                self.process = None

                self.progress_bar.finish()
                self.update_btn.setEnabled(True)

                if exit_code != 0:
                    msg = QMessageBox(self)
                    msg.setIcon(QMessageBox.Critical)
                    msg.setWindowTitle("Error en el subproceso")
                    msg.setText(f"El proceso finalizó con error (código {exit_code}) después de {elapsed:.2f} s.")
                    msg.setDetailedText(stderr if stderr else "No se recibió salida de error.")
                    msg.exec()
                    self.update_btn.setEnabled(True)
                    self.progress_bar.finish()
                    print(f"[ERROR] Subproceso falló: {stderr}")
                    self.simulation_state.prev_params_field = [None] * len(self.simulation_state.prev_params_field)
                    self.simulation_state.save_to_json(model("simulation_state.json"))
                else:
                    print(f"[INFO] Proceso terminado exitosamente en {elapsed:.2f} s")
                    msg = QMessageBox(self)
                    msg.setIcon(QMessageBox.Information)
                    msg.setWindowTitle("Proceso completado (Campo electrico)")
                    msg.setText("✅ El proceso se completó correctamente.\nApp is ready.")
                    msg.exec()

                    loader = LoaderWorker(
                        mode=loader_mode,
                        params={"validate_density": self.charge_density_check.isChecked()}
                    )
                    self.main_window.launch_worker(loader, finished_callback)

        self.timer = QTimer()
        self.timer.timeout.connect(check_output)
        self.timer.start(300)
