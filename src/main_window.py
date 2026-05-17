# ──────────────────────────────────────────────
# Importación de librerías estándar
import os                      # Manejo de rutas y operaciones con archivos
import numpy as np             # Biblioteca para cálculos numéricos y álgebra matricial

# ──────────────────────────────────────────────
# Importación de módulos de PySide6 para la interfaz gráfica
import PySide6.QtWidgets as QtW  # Importación general de widgets Qt para construcción de la GUI
from PySide6 import QtCore        # Elementos centrales de Qt, incluyendo señales y soporte para hilos
from PySide6.QtWidgets import (  # Widgets específicos para la interfaz gráfica principal
    QWidget, QLabel, QLineEdit, QPushButton,
    QHBoxLayout, QVBoxLayout, QFormLayout, QGroupBox
)
from PySide6.QtWidgets import QMessageBox  # Diálogos emergentes para mostrar mensajes al usuario
from PySide6.QtCore import QThread, Signal, QObject, QTimer  # Clases para multitarea, señales y temporizadores

# ──────────────────────────────────────────────
# Módulos para visualización 3D y manejo de mallas
import pyvista as pv                 # Biblioteca para visualización y procesamiento 3D
from pyvistaqt import QtInteractor  # Integración de PyVista con Qt para interacción visual
import meshio                       # Herramienta para lectura y escritura de formatos de malla
import gmsh                         # Generación y refinamiento de mallas geométricas

# ──────────────────────────────────────────────
# Importación de módulos propios del proyecto
from electric_field_solver import ElectricFieldSolver           # Solucionador de campos eléctricos
from mesh_generator import HallThrusterMesh                     # Generador de malla para propulsor Hall
from project_paths import model                                  # Gestión de rutas dentro del proyecto
from widgets.panels.simulation_options import SimulationOptionsPanel  # Panel para opciones de simulación
from widgets.panels.magnetic_field.magnetic_options import MagneticOptionsPanel  # Panel de opciones para campo magnético
from widgets.panels.field_options import FieldOptionsPanel       # Panel de opciones para campo eléctrico
from gui_styles.stylesheets import *                             # Estilos CSS para personalización de la interfaz
from gui_styles.stylesheets import messagebox_style
from widgets.parameter_views import ParameterPanel               # Panel para visualización y edición de parámetros
from widgets.options_panel import OptionsPanel                   # Panel general para opciones diversas
from widgets.view_panel import ViewPanel                         # Panel principal para visualización 3D
from utils.loader_thread import LoaderWorker                     # Worker para tareas en segundo plano con hilos
from models.simulation_state import SimulationState              # Modelo que representa el estado actual de la simulación
from widgets.panels.home_options import HomeOptionsPanel         # Panel de opciones en la pantalla inicial
from PySide6.QtWidgets import QProgressDialog                    # Diálogo para mostrar progreso de tareas largas
from PySide6.QtCore import QThread, Signal, QObject, Qt         # Clases centrales para multitarea y gestión de eventos Qt
from PySide6.QtGui import QGuiApplication                        # Funciones para interacción con la pantalla y GUI

class MainWindow(QtW.QMainWindow):
    def __init__(self):
        super().__init__()
        self._active_threads = []

        # Definición del título principal de la ventana
        self.setWindowTitle("HET simulator")

        # Obtener dimensiones disponibles de la pantalla principal para dimensionar la ventana
        screen_size = QGuiApplication.primaryScreen().availableGeometry().size()
        width, height = screen_size.width(), screen_size.height()

        # Establecer tamaño mínimo y tamaño inicial basado en proporciones de la pantalla
        self.setMinimumSize(int(width * 0.8), int(height * 0.8))
        self.resize(int(width * 0.95), int(height * 0.8))

        # Definición de la ruta para el archivo JSON que contiene el estado de la simulación
        state_file = model("simulation_state.json")

        # Cargar estado de simulación si existe; si no, crear estado inicial y guardarlo
        if os.path.exists(state_file):
            print("[INFO] Estado de simulación cargado desde archivo JSON.")
            self.simulation_state = SimulationState.load_from_json(state_file)
            self.simulation_state.print_state()
        else:
            print("[INFO] Archivo de estado no encontrado. Se crea estado por defecto.")
            self.simulation_state = SimulationState()
            self.simulation_state.save_to_json(state_file)  # Guardar archivo inicial

        # Instanciación de los paneles principales que componen la interfaz de usuario
        self.home_panel = HomeOptionsPanel(self)
        self.field_panel = FieldOptionsPanel(self)
        self.magnetic_panel = MagneticOptionsPanel(self)
        self.simulation_panel = SimulationOptionsPanel(self)

        # Configuración general de la interfaz gráfica
        self._setup_ui()

        # Aplicar estilos personalizados definidos en el proyecto
        self.setStyleSheet(self_Style())

        # Añadir el visor del campo magnético al panel principal de visualización
        self.View_Part.add_viewer("magnetic", self.magnetic_panel.magnetic_viewer)

        # Initial banner / button state based on the persisted simulation state.
        self.refresh_dependency_state()

    def _setup_ui(self):
        # Configuración del widget central y distribución principal de la ventana

        central_widget = QtW.QWidget()  # Widget contenedor principal
        self.frame = QtW.QHBoxLayout()  # Layout horizontal para distribuir columnas
        self.frame.setSpacing(0)
        self.frame.setContentsMargins(0, 0, 0, 0)

        # Creación de las tres columnas principales: opciones, parámetros y vista principal
        self.Parameters = ParameterPanel(self)  # Panel para parámetros
        self.Options = OptionsPanel(self, self.Parameters.parameters_view)  # Panel para opciones con acceso a parámetros
        self.View_Part = ViewPanel(self)        # Panel principal para visualización 3D
        self.parameters_view = self.Parameters.parameters_view
        self.set_active_button(self.Options.tab_buttons[0])  # Seleccionar botón activo inicial

        # Añadir widgets al layout principal con distribución proporcional del espacio
        self.frame.addWidget(self.Options, stretch=0.3)
        self.frame.addWidget(self.Parameters, stretch=1)
        self.frame.addWidget(self.View_Part.view_stack, stretch=4)

        # Asignar layout al widget central y establecerlo como contenido principal de la ventana
        central_widget.setLayout(self.frame)
        self.setCentralWidget(central_widget)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Ajustar tamaño mínimo del contenido interno si existe el atributo 'frame_content'
        if hasattr(self, 'frame_content'):
            self.frame_content.setMinimumSize(self.width(), self.height())

    @property
    def current_viewer(self):
        # Retorna el widget de visualización actualmente activo
        return self.View_Part.view_stack.currentWidget()

    def on_dynamic_tab_clicked(self, index, btn):
        # Gestión del cambio de pestañas: actualizar vista de parámetros y panel de visualización

        self.parameters_view.setCurrentIndex(index)
        self.set_active_button(btn)

        view_keys = {0: "mesh", 1: "field", 2: "magnetic", 3: "simulation"}
        if index in view_keys:
            self.View_Part.switch_view(view_keys[index])

        # Silent state refresh: enables/disables action buttons and refreshes inline banners.
        # No modal alerts on tab switch — prerequisite warnings are surfaced either as inline
        # banners inside each panel or only when the user clicks an action button.
        self.refresh_dependency_state()

    def set_active_button(self, active_btn):
        # Actualizar estilos visuales para resaltar el botón actualmente activo
        for btn in self.Options.tab_buttons:
            if btn == active_btn:
                btn.setStyleSheet(button_activate_style())
            else:
                btn.setStyleSheet(button_options_style())
        if hasattr(self.Options, "refresh_icons"):
            self.Options.refresh_icons(active_btn)

    def launch_worker(self, worker, finished_callback):
        # Crear y lanzar un hilo para ejecutar una tarea en segundo plano mediante un worker

        thread = QThread()
        self._active_threads.append(thread)
        worker.moveToThread(thread)

        print(f"[INFO] Iniciando worker con modo: {worker.mode}")

        # Conectar señales para gestión de ejecución y limpieza
        thread.started.connect(worker.run)
        worker.finished.connect(finished_callback)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)

        def cleanup():
            print(f"[INFO] Liberando recursos del hilo asociado al worker: {worker.mode}")
            if thread in self._active_threads:
                self._active_threads.remove(thread)
            thread.deleteLater()

        thread.finished.connect(cleanup)

        # Iniciar ejecución del hilo
        thread.start()

    def refresh_dependency_state(self):
        """
        Refresh action-button enablement and inline alert banners across panels
        based on the current outdated flags.

        Silent: never shows a modal popup.
        """
        if hasattr(self.simulation_panel, "update_simulate_button_state"):
            self.simulation_panel.update_simulate_button_state()
        if hasattr(self.magnetic_panel, "update_magnetic_button_state"):
            self.magnetic_panel.update_magnetic_button_state()
        if hasattr(self.magnetic_panel, "refresh_banner"):
            self.magnetic_panel.refresh_banner()
        if hasattr(self.simulation_panel, "refresh_banner"):
            self.simulation_panel.refresh_banner()

    # Backwards-compatible alias kept for any caller still using the old name.
    def alert_if_field_or_magnetic_outdated(self):
        self.refresh_dependency_state()

    def show_prerequisite_alert(self, title: str, message: str):
        """Modal warning card shown right before running an action that lacks prerequisites."""
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(message)
        box.setIcon(QMessageBox.Warning)
        box.setStyleSheet(messagebox_style())
        box.exec()
