import os
import sys
import numpy as np
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from models.simulation_state import SimulationState
from magnetic_field_solver_cpu import B_Field
from project_paths import data_file, model


print("[DEBUG] Process started", flush=True)

# Load electric field data and spatial coordinates
E_File = np.load(data_file("E_Field_Poisson.npy"))
spatial_coords = E_File[:, :3]

# Load simulation state parameters
state = SimulationState.load_from_json(model("simulation_state.json"))

nSteps = state.nSteps
N_turns = state.N_turns
I = state.I

# Instantiate B_Field object with parameters from state
bfield = B_Field(
    nSteps=nSteps,
    N=N_turns,
    I=I,
    L_canal=state.H,
    L_bobina=state.H,
    Rin=state.R_small,
    Rext=state.R_big
)

# Calculate total magnetic field at given spatial coordinates
B_value = bfield.Total_Magnetic_Field(S=spatial_coords)

# === Original magnitude histogram visualization (debug comment) ===
magnitudes = np.linalg.norm(B_value, axis=1)

# === Automatic filtering based on percentiles (debug comment) ===
lower_percentile = 0.1   # lower percentile threshold
upper_percentile = 99.9  # upper percentile threshold
min_physical = np.percentile(magnitudes, lower_percentile)
max_physical = np.percentile(magnitudes, upper_percentile)

print(f"Filtering magnitudes outside the range [{min_physical:.2e}, {max_physical:.2e}] T")
outliers = ~((magnitudes >= min_physical) & (magnitudes <= max_physical))
print(f"Points outside range: {np.count_nonzero(outliers)} of {len(magnitudes)}")

# === Modify outlier values without removing any rows ===
B_value_filtered = B_value.copy()
B_value_filtered[outliers] = 0.0  # Alternative: scale by min_physical * B_value[outliers] / magnitudes[outliers]

# Save filtered magnetic field data in the same format as original files
np.save(data_file("Magnetic_Field_np.npy"), np.column_stack((spatial_coords, B_value_filtered)))

print("[DEBUG] Magnetic field calculated and saved (outliers set to zero)")
