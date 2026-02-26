import json

class SimulationState:
    """
    Class representing the complete state of a physical simulation
    in a space propulsion environment (HET or other).

    Attributes:
        Geometry:
            - H: Domain height [m]
            - R_big: Outer radius [m]
            - R_small: Inner radius [m]
            - r0: Mean radius (coil center) [m]

        Mesh:
            - refinement_level: Refinement level (str)
            - max_elements: Maximum number of elements (optional)
            - min_physics_scale: Minimum physical resolution scale (optional)
            - chunk_size: Chunk size for processing (optional)

        Field:
            - voltage: Anode voltage [V]
            - voltage_cathode: Cathode voltage [V]
            - N_turns: Number of coil turns
            - I: Current [A]

        Simulation:
            - nSteps: Number of time steps
            - N_particles: Number of particles
            - frames: Number of frames to save (for animation)

        Dynamics:
            - alpha: Collision coefficient (optional)
            - sigma_ion: Ionization cross-section (optional)
            - dt: Time step (optional)

        Configuration:
            - GPU_ACTIVE: Whether GPU is enabled
            - gas: Type of gas
            - field_outdated: Indicates if the electric field is outdated
            - magnetic_outdated: Indicates if the magnetic field is outdated

        Previous Parameters (for change tracking):
            - prev_params_mesh: Last mesh parameters
            - prev_params_field: Last electric field parameters
            - prev_params_magnetic: Last magnetic field parameters
            - prev_params_simulation: Last simulation parameters
    """

    def __init__(self):
        # Geometry
        self.H = 0.02
        self.R_big = 0.050
        self.R_small = 0.028
        self.r0 = (self.R_big + self.R_small) / 2

        # Mesh
        self.refinement_level = "test"
        self.max_elements = None
        self.min_physics_scale = None
        self.chunk_size = None

        # Electric and magnetic fields
        self.voltage = 300
        self.voltage_cathode = 16
        self.N_turns = 200
        self.I = 4.5

        # Simulation
        self.nSteps = 5000
        self.N_particles = 1000
        self.frames = 500

        # Particle dynamics
        self.alpha = None
        self.sigma_ion = None
        self.dt = None

        # General configuration
        self.GPU_ACTIVE = False
        self.gas = "Xenon"
        self.field_outdated = False
        self.magnetic_outdated = False

        self.impulso_especifico = None
        self.time_simulation = None

        # Previous parameters
        self.prev_params_mesh = (
            self.H, self.R_big, self.R_small, self.refinement_level, self.max_elements
        )
        self.prev_params_field = (
            self.voltage, self.voltage_cathode
        )
        self.prev_params_magnetic = (
            self.N_turns, self.I, self.r0
        )
        self.prev_params_simulation = (
            self.nSteps, self.N_particles
        )

    def print_state(self):
        """
        Prints the current simulation state in an organized manner.
        """
        print("=" * 40)
        print(" Simulation State Overview ".center(40, "="))
        print("-" * 40)
        print("[Geometry and Physical Parameters]")
        print(f"  H                : {self.H}")
        print(f"  R_big            : {self.R_big}")
        print(f"  R_small          : {self.R_small}")
        print(f"  r0 (center)      : {self.r0}")
        print()
        print("[Mesh and Refinement]")
        print(f"  refinement_level : {self.refinement_level}")
        print(f"  max_elements     : {self.max_elements}")
        print(f"  min_physics_scale: {self.min_physics_scale}")
        print(f"  chunk_size       : {self.chunk_size}")
        print()
        print("[Electric/Magnetic Field]")
        print(f"  voltage          : {self.voltage}")
        print(f"  voltage_cathode  : {self.voltage_cathode}")
        print(f"  N_turns (coil)   : {self.N_turns}")
        print(f"  I (current)      : {self.I}")
        print()
        print("[Simulation Parameters]")
        print(f"  nSteps           : {self.nSteps}")
        print(f"  N_particles      : {self.N_particles}")
        print(f"  frames           : {self.frames}")
        print()
        print("[Dynamics and Additional Physics]")
        print(f"  alpha            : {self.alpha}")
        print(f"  sigma_ion        : {self.sigma_ion}")
        print(f"  dt               : {self.dt}")
        print()
        print("[Additional Configuration]")
        print(f"  GPU_ACTIVE       : {self.GPU_ACTIVE}")
        print(f"  gas              : {self.gas}")
        print(f"  field_outdated   : {self.field_outdated}")
        print(f"  magnetic_outdated: {self.magnetic_outdated}")
        print()
        print("[Previous Parameters]")
        print(f"  prev_params_mesh      : {self.prev_params_mesh}")
        print(f"  prev_params_field     : {self.prev_params_field}")
        print(f"  prev_params_magnetic  : {self.prev_params_magnetic}")
        print(f"  prev_params_simulation: {self.prev_params_simulation}")
        print("=" * 40)

    def to_dict(self):
        """
        Returns the current state as a dictionary.
        Useful for JSON serialization.
        """
        return self.__dict__

    def save_to_json(self, path):
        """
        Saves the current state to a JSON file.

        Args:
            path (str): Full destination file path.
        """
        print(f"[DEBUG] Saving JSON to: {path}")
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=4)

    @classmethod
    def load_from_json(cls, path):
        """
        Loads a simulation state from a JSON file.

        Args:
            path (str): Path to the JSON file.

        Returns:
            SimulationState: Reconstructed object from loaded data.
        """
        with open(path, "r") as f:
            data = json.load(f)
        obj = cls()
        obj.__dict__.update(data)
        return obj
