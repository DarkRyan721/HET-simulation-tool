import subprocess
import os
import sys
import time
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6.QtCore import Slot

import hashlib
import json
from PySide6.QtWidgets import QMessageBox
from magnetic_field_solver_cpu import B_Field
from utils.loader_thread import LoaderWorker
from widgets.panels.collapse import CollapsibleBox
from widgets.panels.magnetic_field.field_lines_control_panel import FieldLinesControlPanel
from widgets.panels.magnetic_field.heatmap_points_control import HeatmapControlPanel
from widgets.panels.magnetic_field.solenoid_points_control import SolenoidPointsControlPanel

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, QLineEdit, QLabel,
    QHBoxLayout, QPushButton, QCheckBox, QSlider, QComboBox
)

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, QPushButton
)
from PySide6.QtCore import QThread, Signal, QObject, QTimer

from PySide6.QtCore import Qt
import PySide6.QtWidgets as QtW

from utils.ui_helpers import _input_with_unit
from gui_styles.stylesheets import *
from gui_styles.stylesheets import messagebox_style, viewer_frame_style
from widgets.alert_banner import AlertBanner
# TODO: Importar el solver y el loader apropiados para el campo magnético
# from E_field_solver import MagneticFieldSolver
# from utils.magnetic_loader import MagneticLoaderWorker
from project_paths import data_file, model, worker

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, QPushButton, QComboBox
)
from utils.loading_bar import ProgressBarWidget
from PySide6.QtWidgets import QStyle
from PySide6.QtWidgets import QVBoxLayout, QPushButton, QWidget, QLabel, QFrame
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel

class MagneticOptionsPanel(QWidget):
    plot_result_ready = Signal(object)
    def __init__(self, main_window):
        super().__init__()
        self._active_plot_threads = []
        self.main_window = main_window
        self.simulation_state = self.main_window.simulation_state
        self.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.thread = QThread()

        self.dependency_banner = AlertBanner(
            title="Prerequisites required",
            message="Update the electric field first.",
            level="warning",
        )
        self.dependency_banner.hide()
        layout.addWidget(self.dependency_banner)
        self.plot_result_ready.connect(self._on_plot_result_ready)

        # Parámetros magnéticos
        self.input_nSteps_container, self.input_nSteps = _input_with_unit(str(self.simulation_state.nSteps), "[N_turns]")
        self.input_N_turns_container, self.input_N = _input_with_unit(str(self.simulation_state.N_turns), "[N_turns]")
        self.input_i_container, self.input_i = _input_with_unit(str(self.simulation_state.I), "[A]")


        # --- Layout para visualizaciones ---
        self.visualization_layout = QVBoxLayout()
        layout.addLayout(self.visualization_layout)

        # --- Diccionario de widgets de visualización ---
        self.visualization_widgets = {}

        # --- Viewer 3D ---
        self.magnetic_viewer = self._create_viewer()
        self.visualization_widgets["3D Magnetic Field"] = self.magnetic_viewer

        # --- Canvas Matplotlib (Heatmap) ---
        self.mpl_canvas = None  # Se crea bajo demanda


        mag_box = QGroupBox("Magnetic field parameters")
        mag_box.setStyleSheet(box_render_style())
        mag_box.setSizePolicy(QtW.QSizePolicy.Policy.Expanding, QtW.QSizePolicy.Policy.Fixed)
        form = QFormLayout()
        form.addRow("Integration steps (nSteps):", self.input_nSteps_container)
        form.addRow("Number of turns (N_turns):", self.input_N_turns_container)
        form.addRow("Current (I):", self.input_i_container)
        mag_box.setLayout(form)
        layout.addWidget(mag_box)


        self.update_btn = QPushButton("Update field")
        self.update_btn.setStyleSheet(button_parameters_style())
        self.update_btn.setToolTip("Run the magnetic field computation with the current parameters.")
        self.update_btn.clicked.connect(self.on_update_clicked_Magnetic_field)
        layout.addWidget(self.update_btn)

        self.solenoid_controls = SolenoidPointsControlPanel()
        self.solenoid_controls.btn_update.clicked.connect(self._show_solenoid_points_viewer)

        self.field_lines_controls = FieldLinesControlPanel()
        self.field_lines_controls.btn_update.clicked.connect(self._show_field_lines_viewer)

        self.heatmap_controls = HeatmapControlPanel()
        self.heatmap_controls.btn_update.clicked.connect(self._show_heatmap_viewer)

        layout.addWidget(self.solenoid_controls)
        layout.addWidget(self.field_lines_controls)
        layout.addWidget(self.heatmap_controls)

        self.progress_bar = ProgressBarWidget("Loading mesh...")
        layout.addWidget(self.progress_bar)
        self.progress_bar.hide()
        # self.progress_bar = QtW.QProgressBar()
        # self.progress_bar.setRange(0, 0)  # Indeterminado (marquee)
        # self.progress_bar.setVisible(False)
        # layout.addWidget(self.progress_bar)

        # Estira para ocupar espacio
        layout.addStretch()

        # Carga inicial si existe
        self._load_initial_magnetic_if_exists()

    def update_magnetic_button_state(self):
        """Keep buttons enabled — pre-action validation handles missing prerequisites."""
        self.set_buttons_enabled(True)

    def _missing_prerequisites_message(self) -> str | None:
        if self.simulation_state.field_outdated:
            return "The electric field must be updated before computing the magnetic field."
        return None

    def refresh_banner(self):
        msg = self._missing_prerequisites_message()
        if msg:
            self.dependency_banner.set_content(
                title="Prerequisites required",
                message=msg,
                level="warning",
            )
            self.dependency_banner.show()
        else:
            self.dependency_banner.hide()

    def set_buttons_enabled(self, enabled: bool):
        # Aquí agrega todos los botones que deseas deshabilitar/habilitar
        self.heatmap_controls.btn_update.setEnabled(enabled)
        self.field_lines_controls.btn_update.setEnabled(enabled)
        self.solenoid_controls.btn_update.setEnabled(enabled)
        self.update_btn.setEnabled(enabled)

    def on_update_clicked_Magnetic_field(self):
        prereq_msg = self._missing_prerequisites_message()
        if prereq_msg:
            self.main_window.show_prerequisite_alert("Update fields", prereq_msg)
            return

        # Recolecta campos obligatorios y avanzados
        campos = {
            "nSteps": self.input_nSteps.text(),
            "N_turns": self.input_N.text(),
            "I": self.input_i.text(),
        }

        try:
            valores = self.validar_numeros(campos)
        except ValueError as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Validation error", str(e))
            return

        nSteps = int(valores["nSteps"])
        N_turns = int(valores["N_turns"])
        I = valores["I"]
        self.simulation_state.nSteps = nSteps
        self.simulation_state.N_turns = N_turns
        self.simulation_state.I = I

        self.progress_bar.start("Computing magnetic field...")
        self.set_buttons_enabled(False)
        new_params = [nSteps, N_turns, I]
        if new_params != self.simulation_state.prev_params_magnetic or self.simulation_state.magnetic_outdated:
            self.progress_bar.start()
            print("Magnetic parameters changed:", new_params)
            self.simulation_state.prev_params_magnetic = new_params
            self.simulation_state.save_to_json(model("simulation_state.json"))
            self.run_process_and_reload(
                process_script="magnetic_field_process.py",
                loader_mode="magnetic",
                finished_callback= self.on_magnetic_loaded_file
            )
        else:
            from PySide6.QtWidgets import QMessageBox
            print("No changes detected in magnetic parameters.")
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("No changes detected")
            msg.setText("You must change the parameters to run a new magnetic field simulation.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setStyleSheet(messagebox_style())
            msg.exec()
            self.main_window.launch_worker(LoaderWorker(mode="magnetic"), self.on_magnetic_loaded)
        self.simulation_state.print_state()

    def validar_numeros(self, campos, opcionales=None):
        """
        Valida que los valores de entrada sean numéricos y no vacíos,
        excepto los opcionales, que pueden ser vacíos o 'None' y se asignan como None.
        """
        if opcionales is None:
            opcionales = set()
        else:
            opcionales = set(opcionales)

        resultados = {}
        for nombre, texto in campos.items():
            texto = str(texto).strip()
            if not texto or texto.lower() == "none":
                if nombre in opcionales:
                    resultados[nombre] = None
                    continue
                else:
                    raise ValueError(f"El campo '{nombre}' es obligatorio y está vacío.")
            try:
                valor = float(texto)
            except ValueError:
                raise ValueError(f"El campo '{nombre}' debe ser un número válido. Valor recibido: '{texto}'")
            resultados[nombre] = valor
        return resultados

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
                print(f"[DEBUG] Proceso terminado en {elapsed:.2f} s")
                stdout, stderr = self.process.communicate()
                exit_code = self.process.returncode

                self.process = None

                if exit_code != 0:
                    msg = QMessageBox(self)
                    msg.setIcon(QMessageBox.Critical)
                    msg.setWindowTitle("Subprocess error")
                    msg.setText(f"The process failed with exit code {exit_code} after {elapsed:.2f} s.")
                    msg.setDetailedText(stderr if stderr else "No error output was received.")
                    msg.setStyleSheet(messagebox_style())
                    msg.exec()
                    self.process_finished = True
                    self.set_buttons_enabled(True)
                    self.progress_bar.finish()
                    self.simulation_state.prev_params_magnetic = [None] * len(self.simulation_state.prev_params_magnetic)
                    self.simulation_state.save_to_json(model("simulation_state.json"))
                    print(f"[ERROR] Subprocess failed: {stderr}")
                else:
                    print(f"[INFO] Process finished successfully in {elapsed:.2f} s")
                    msg = QMessageBox(self)
                    msg.setIcon(QMessageBox.Information)
                    msg.setWindowTitle("Magnetic field computed")
                    msg.setText("The process finished successfully.\nApp is ready.")
                    msg.setStyleSheet(messagebox_style())
                    msg.exec()

                    loader = LoaderWorker(mode=loader_mode)
                    self.main_window.launch_worker(loader, finished_callback)

        self.timer = QTimer()
        self.timer.timeout.connect(check_output)
        self.timer.start(300)

    def on_magnetic_loaded(self, data):
            self.current_magnetic = data
            self.main_window.View_Part.current_data = data  # asegúrate de sincronizar ViewPanel
            self.visualize_magnetic(data)
            self.progress_bar.finish()
            self.set_buttons_enabled(True)

    def on_magnetic_loaded_file(self, data):
            self.current_magnetic = data
            self.simulation_state.magnetic_outdated = False
            self.main_window.View_Part.current_data = data
            self.simulation_state.save_to_json(model("simulation_state.json"))
            self.main_window.refresh_dependency_state()
            self.visualize_magnetic(data)
            self.progress_bar.finish()
            self.set_buttons_enabled(True)

    def visualize_magnetic(self, glyphs):
        self.magnetic_viewer.clear()
        self.magnetic_viewer.update()
        self.magnetic_viewer.add_mesh(
            glyphs, scalars="magnitude", cmap="magma", scalar_bar_args={"title": "|B| [T]"}
        )
        self.magnetic_viewer.add_text("Magnetic field", position='upper_edge', font_size=6, color='black')
        self.magnetic_viewer.reset_camera()
        self.magnetic_viewer.view_yx()

    def _create_viewer(self):
        viewer = QtInteractor()
        viewer.set_background("white")
        viewer.setStyleSheet(viewer_frame_style())
        viewer.add_axes(interactive=False)
        viewer.setSizePolicy(QtW.QSizePolicy.Expanding, QtW.QSizePolicy.Expanding)
        viewer.view_zx()
        try:
            viewer.enable_shadows(False)
        except Exception:
            pass
        try:
            viewer.enable_anti_aliasing(False)
        except Exception:
            pass
        return viewer

    def _load_initial_magnetic_if_exists(self):
        path = data_file("Magnetic_Field_np.npy")
        params = (
            self.simulation_state.nSteps,
            self.simulation_state.N_turns,
            self.simulation_state.I
        )

        if os.path.exists(path):
            worker = LoaderWorker(
                mode="magnetic",
                params=params,
            )
            self.main_window.launch_worker(worker, self.on_magnetic_loaded)

    def show_viewer3d(self):
        # Limpia el canvas matplotlib si está presente
        if hasattr(self, "mpl_canvas") and self.mpl_canvas is not None:
            for name in list(self.main_window.View_Part.viewers.keys()):
                if isinstance(self.main_window.View_Part.viewers[name], FigureCanvas):
                    self.main_window.View_Part.view_stack.removeWidget(self.mpl_canvas)
                    del self.main_window.View_Part.viewers[name]
            self.mpl_canvas.deleteLater()
            self.mpl_canvas = None
        # Ahora asegúrate de volver a agregar el viewer 3D si no está
        if "magnetic" not in self.main_window.View_Part.viewers:
            self.main_window.View_Part.add_viewer("magnetic", self.magnetic_viewer)
        self.main_window.View_Part.switch_view("magnetic")

    def show_matplotlib_figure(self, fig, name):
        # Elimina el canvas anterior (si existe)
        if hasattr(self, "mpl_canvas") and self.mpl_canvas is not None:
            if name in self.main_window.View_Part.viewers:
                self.main_window.View_Part.view_stack.removeWidget(self.mpl_canvas)
                del self.main_window.View_Part.viewers[name]
            self.mpl_canvas.deleteLater()
            self.mpl_canvas = None

        self.mpl_canvas = FigureCanvas(fig)
        self.main_window.View_Part.add_viewer(name, self.mpl_canvas)
        self.main_window.View_Part.switch_view(name)

    def _start_plot_thread(self, plot_func, finished_callback):
        self.progress_bar.start("Loading data...")
        self.set_buttons_enabled(False)
        thread = QThread()
        worker = PlotWorker(plot_func)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(finished_callback)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)

        def cleanup():
            self.progress_bar.finish()
            self.set_buttons_enabled(True)
            print("🧹 Limpiando thread del PlotWorker")
            self._active_plot_threads.append((thread, worker))
            thread.deleteLater()

        thread.finished.connect(cleanup)
        self._active_plot_threads.append((thread, worker))
        thread.start()
        print("[DEBUG] Hilo de plot iniciado")

    def on_heatmap_finished(self, result):
        self.plot_result_ready.emit(('Heatmap', result))
    def on_fieldlines_finished(self, result):
        self.plot_result_ready.emit(('Field Lines', result))
    def on_solenoidpoints_finished(self, result):
        self.plot_result_ready.emit(('Solenoid Points', result))

    def _on_plot_result_ready(self, data):
        tipo, result = data
        fig, ax = result
        # Aquí puedes mapear tipo a nombre de viewer si quieres
        if tipo == "Heatmap":
            name = "magnetic_heatmap"
        elif tipo == "Field Lines":
            name = "magnetic_fieldlines"
        elif tipo == "Solenoid Points":
            name = "solenoid_points"
        else:
            name = "unknown_plot"
        self.show_matplotlib_figure(fig, name)

    def _show_solenoid_points_viewer(self):
        self.progress_bar.start("Loading data...")
        self.set_buttons_enabled(False)
        print("[DEBUG] Mostrando Solenoid Points Viewer")
        print("[DEBUG] Viewers antes:", self.main_window.View_Part.viewers.keys())
        # Limpia el viewer 3D de PyVista
        self.magnetic_viewer.clear()
        # Re-agrega el viewer si no está registrado
        if "magnetic" not in self.main_window.View_Part.viewers:
            self.main_window.View_Part.add_viewer("magnetic", self.magnetic_viewer)
        # SWITCH explícito al viewer 3D:
        self.main_window.View_Part.switch_view("magnetic")
        print("[DEBUG] Switch a viewer 3D realizado")
        # Obtén los parámetros de los checkboxes o controles
        params = self.solenoid_controls.get_params()
        # Instancia el campo magnético según parámetros actuales
        bfield = B_Field(
            nSteps=self.simulation_state.nSteps,
            N=self.simulation_state.N_turns,
            I=self.simulation_state.I
        )
        # Llama al método PyVista, pasando el QtInteractor embebido
        bfield.Solenoid_points_plot_pyvista(**params, plotter=self.magnetic_viewer)
        self.magnetic_viewer.reset_camera()
        self.magnetic_viewer.view_isometric()
        self.progress_bar.finish()
        self.set_buttons_enabled(True)
        print("[DEBUG] Viewers después:", self.main_window.View_Part.viewers.keys())
        print("[DEBUG] Widget activo después:", self.main_window.View_Part.view_stack.currentWidget())

    def generate_heatmap_threaded(self):
        print("[DEBUG] Generando Heatmap en un hilo separado")
        self.progress_bar.start("Loading data...")
        self.set_buttons_enabled(False)
        params = self.heatmap_controls.get_params()
        bfield = B_Field(
            nSteps=self.simulation_state.nSteps,
            N=self.simulation_state.N_turns,
            I=self.simulation_state.I
        )
        print("[DEBUG] Params enviados a heatmap:", params)
        plot_func = lambda: bfield.B_Field_Heatmap(**params)
        self._start_plot_thread(plot_func, self.on_heatmap_finished)

    def generate_fieldlines_threaded(self):
        print("[DEBUG] Generando Field Lines en un hilo separado")
        params = self.field_lines_controls.get_params()
        bfield = B_Field(
            nSteps=self.simulation_state.nSteps,
            N=self.simulation_state.N_turns,
            I=self.simulation_state.I
        )
        print("[DEBUG] Params enviados a field lines:", params)
        plot_func = lambda: bfield.B_Field_Lines(**params)
        self._start_plot_thread(plot_func, self.on_fieldlines_finished)

    def generate_solenoidpoints_threaded(self):
        print("[DEBUG] Generando Solenoid Points en un hilo separado")
        params = self.solenoid_controls.get_params()
        bfield = B_Field(
            nSteps=self.simulation_state.nSteps,
            N=self.simulation_state.N_turns,
            I=self.simulation_state.I
        )
        print("[DEBUG] Params enviados a solenoid points:", params)
        plot_func = lambda: bfield.Solenoid_points_plot(**params)
        self._start_plot_thread(plot_func, self.on_solenoidpoints_finished)


    def params_hash(self, mode, nSteps, N_turns, I, kwargs):
        string = f"{mode}_{nSteps}_{N_turns}_{I}_{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(string.encode()).hexdigest()

    def generate_magnetic_image(self, mode, nSteps, N_turns, I, kwargs, output_path):
        self.simulation_state.mode_magnetic = mode
        self.simulation_state.nSteps = nSteps
        self.simulation_state.N_turns = N_turns
        self.simulation_state.I = I
        self.simulation_state.output_file = output_path
        self.simulation_state.kwargs = kwargs
        self.simulation_state.save_to_json(model("simulation_state.json"))
        args = [
            sys.executable,
            worker("magnetic_graphic_process.py"),
        ]
        result = subprocess.run(args, capture_output=True, text=True)
        if result.returncode != 0:
            print("ERROR en generación gráfica:", result.stderr)
            return False
        print("OK: Imagen generada:", output_path)
        return True

    def _show_heatmap_viewer(self):
        print("[DEBUG] Mostrando Heatmap Viewer")
        params = self.heatmap_controls.get_params()
        nSteps = self.simulation_state.nSteps
        N_turns = self.simulation_state.N_turns
        I = self.simulation_state.I
        mode = "heatmap"
        hashname = self.params_hash(mode, nSteps, N_turns, I, params)
        output_path = os.path.join(data_file(""), f"heatmap_{hashname}.png")

        # Antes de lanzar generate_magnetic_image(...)
        self.simulation_state.output_file = output_path
        self.simulation_state.mode_magnetic = mode  # ("fieldlines", "heatmap", etc.)
        self.simulation_state.kwargs = params  # si params son los kwargs específicos del modo
        self.simulation_state.save_to_json(model("simulation_state.json"))

        if not os.path.exists(output_path):
            # Lanza el proceso, preferiblemente en un QThread (ejemplo aquí sin QThread)
            self.progress_bar.start("Loading data...")
            self.set_buttons_enabled(False)
            ok = self.generate_magnetic_image(mode, nSteps, N_turns, I, params, output_path)
            self.progress_bar.finish()
            self.set_buttons_enabled(True)
            if not ok:
                return
        # Ahora muestra la imagen
        self._show_image_in_panel(output_path, "magnetic_heatmap")

    def _show_field_lines_viewer(self):
        print("[DEBUG] Mostrando Field Lines Viewer")
        params = self.field_lines_controls.get_params()
        nSteps = self.simulation_state.nSteps
        N_turns = self.simulation_state.N_turns
        I = self.simulation_state.I
        mode = "fieldlines"
        hashname = self.params_hash(mode, nSteps, N_turns, I, params)
        output_path = os.path.join(data_file(""), f"fieldlines_{hashname}.png")

        # Antes de lanzar generate_magnetic_image(...)
        self.simulation_state.output_file = output_path
        self.simulation_state.mode_magnetic = mode  # ("fieldlines", "heatmap", etc.)
        self.simulation_state.kwargs = params  # si params son los kwargs específicos del modo
        self.simulation_state.save_to_json(model("simulation_state.json"))

        if not os.path.exists(output_path):
            # Lanza el proceso bloqueante (puedes migrar a QThread luego)
            self.progress_bar.start("Loading data...")
            self.set_buttons_enabled(False)
            ok = self.generate_magnetic_image(mode, nSteps, N_turns, I, params, output_path)
            self.progress_bar.finish()
            self.set_buttons_enabled(True)
            if not ok:
                return
        # Mostrar la imagen en el panel
        self._show_image_in_panel(output_path, "magnetic_fieldlines")


    def _show_image_in_panel(self, image_path, name):
        # Borra canvas anterior
        if hasattr(self, "mpl_canvas") and self.mpl_canvas is not None:
            if name in self.main_window.View_Part.viewers:
                self.main_window.View_Part.view_stack.removeWidget(self.mpl_canvas)
                del self.main_window.View_Part.viewers[name]
            self.mpl_canvas.deleteLater()
            self.mpl_canvas = None

        # Carga la imagen en QLabel/QPixmap
        label = QLabel()
        pixmap = QPixmap(image_path)
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignCenter)
        label.setScaledContents(True)  # Si quieres que se adapte al tamaño
        self.main_window.View_Part.add_viewer(name, label)
        self.main_window.View_Part.switch_view(name)


class PlotWorker(QObject):
    finished = Signal(object)  # Emite el resultado (fig, ax) o solo fig

    def __init__(self, plot_func, *args, **kwargs):
        super().__init__()
        self.plot_func = plot_func
        self.args = args
        self.kwargs = kwargs

    @Slot()
    def run(self):
        print("[DEBUG] INICIO de plot_func en hilo secundario...")
        start = time.perf_counter()
        result = self.plot_func(*self.args, **self.kwargs)
        print(f"[DEBUG] FIN de plot_func, duró {time.perf_counter()-start:.2f} s")
        self.finished.emit(result)
        print("[DEBUG] Ejecutando worker de plot...")
