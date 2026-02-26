import subprocess
import sys
import time
import os
import logging
import numpy as np
import pyvista as pv
import meshio

from PySide6.QtCore import QThread, Signal, QObject, Slot

from electric_field_solver import ElectricFieldSolver
from magnetic_field_solver_cpu import B_Field
from simulation_engine_viewer import Simulation
from project_paths import data_file

# Configure logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


class LoaderWorker(QObject):
    """
    Worker class responsible for loading and processing data for visualization in different modes:
    mesh, electric field, magnetic field, charge density, and particle simulation.

    Signals:
        finished (Signal[object]): Emitted when processing completes, passing the result.
        started (Signal): Emitted when processing starts.
        progress (Signal[int]): Emitted to indicate progress percentage (0-100).

    Args:
        mode (str): Operation mode ('mesh', 'field', 'magnetic', 'density', 'simulation').
        params (dict, optional): Additional parameters required by some modes.
        plotter (Simulation, optional): Visualization instance used in 'simulation' mode.
        solver (ElectricFieldSolver, optional): External solver if needed.
    """

    finished = Signal(object)
    started = Signal()
    progress = Signal(int)

    def __init__(self, mode="mesh", params=None, plotter=None, solver=None):
        super().__init__()
        self.mode = mode
        self.params = params or {}
        self.plotter = plotter
        self.solver = solver
        self._is_running = True

    @Slot()
    def run(self):
        """
        Executes processing according to the specified mode.
        This method can load geometry, electric or magnetic fields, charge densities,
        or run particle simulations.
        """
        self.started.emit()
        logger.debug(f"LoaderWorker started with mode: {self.mode}")

        def fail(message: str):
            logger.error(message)
            self.finished.emit(None)

        if self.mode == "mesh":
            # Load mesh geometry from .msh file and convert to PyVista PolyData
            try:
                msh = meshio.read(data_file("SimulationZone.msh"))
                cells = msh.cells_dict.get("triangle")
                if cells is None:
                    fail("Mesh file does not contain 'triangle' cells.")
                    return
                faces = np.hstack([np.full((cells.shape[0], 1), 3), cells]).astype(np.int32).flatten()
                mesh = pv.PolyData(msh.points, faces)
                logger.debug("Mesh loaded successfully.")
                self.finished.emit(mesh)
            except Exception as e:
                fail(f"Error loading mesh: {e}")

        elif self.mode == "field":
            # Load electric field data from .npy file (Laplace or Poisson solution)
            self.progress.emit(0)
            validate_density = self.params.get("validate_density", False)

            laplace_path = data_file("E_Field_Laplace.npy")
            poisson_path = data_file("E_Field_Poisson.npy")
            field_path = poisson_path if validate_density else laplace_path

            if not os.path.exists(field_path):
                fail(f"Electric field file not found: {field_path}")
                return

            try:
                data = np.load(field_path)
                if data.shape[1] < 6:
                    fail("Electric field data format is invalid: less than 6 columns.")
                    return

                points = data[:, :3]
                vectors = data[:, 3:]
                magnitudes = np.linalg.norm(vectors, axis=1)
                log_magnitudes = np.log10(magnitudes + 1e-3)
                log_magnitudes[log_magnitudes < 0] = 0

                mesh = pv.PolyData(points)
                mesh["E_field"] = vectors
                mesh["magnitude"] = log_magnitudes

                self.progress.emit(100)
                logger.debug("Electric field loaded and processed successfully.")
                self.finished.emit(mesh)
            except Exception as e:
                fail(f"Error loading electric field data: {e}")

        elif self.mode == "magnetic":
            # Load magnetic field data and generate glyphs for visualization
            logger.debug("Loading magnetic field data...")
            file_path = data_file("Magnetic_Field_np.npy")
            if not os.path.exists(file_path):
                fail(f"Magnetic field file not found: {file_path}")
                return

            try:
                data = np.load(file_path)
                if data.shape[1] < 6:
                    fail("Magnetic field data format is invalid: less than 6 columns.")
                    return

                points = data[:, :3]
                vectors = data[:, 3:]
                magnitudes = np.linalg.norm(vectors, axis=1)

                mesh = pv.PolyData(points)
                mesh["vectors"] = vectors
                mesh["magnitude"] = magnitudes
                glyphs = mesh.glyph(orient="vectors", scale=False, factor=0.01)

                logger.debug("Magnetic field loaded and glyphs created successfully.")
                self.finished.emit(glyphs)
            except Exception as e:
                fail(f"Error loading magnetic field data: {e}")

        elif self.mode == "density":
            # Load electron density distribution and return as PolyData
            try:
                E_np = np.load(data_file("E_Field_Laplace.npy"))
                points = E_np[:, :3]
                n0 = np.load(data_file("density_n0.npy"))
                n0_log = np.log10(n0)

                mesh = pv.PolyData(points)
                max_value = np.max(n0_log[n0_log != np.log10(1e-100)])
                log_min = max_value - 3.0
                log_max = max_value

                mesh["n0_log"] = n0_log

                logger.debug("Density data loaded successfully.")
                self.finished.emit({
                    "density": mesh,
                    "log_min": log_min,
                    "log_max": log_max
                })
            except Exception as e:
                fail(f"Error loading density data: {e}")

        elif self.mode == "simulation":
            # Run particle simulation (requires a plotter instance)
            logger.debug("Starting particle simulation...")
            if self.plotter is None:
                fail("Simulation instance (plotter) not provided.")
                return
            try:
                self.plotter.Animation(neutral_visible=self.params.get("neutral_visible", False))
                logger.debug("Simulation completed successfully.")
                self.finished.emit("Simulation completed")
            except Exception as e:
                fail(f"Error during simulation: {e}")

        else:
            fail(f"Unknown mode: {self.mode}")
