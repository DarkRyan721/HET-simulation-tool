# Librerías estándar
import h5py

# Librerías de terceros
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import numpy as np
import pyvista as pv
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from mpl_toolkits import mplot3d
from scipy.interpolate import griddata
from tqdm import tqdm

# Módulos internos del proyecto
from project_paths import data_file

class B_Field:
    def __init__(self, nSteps=5000, L_canal=0.02, L_bobina=0.03,
                 Rin=0.028, Rext=0.05, N=200, I=4.5):
        """
        Inicializa los parámetros del sistema y genera los solenoides.

        Parámetros:
        - nSteps: Resolución del solenoide (número de segmentos).
        - L_canal: Longitud del canal principal (m).
        - L_bobina: Longitud de la bobina (m).
        - Rin: Radio interno del solenoide (m).
        - Rext: Radio externo del solenoide (m).
        - N: Número de vueltas del solenoide.
        - I: Corriente que circula por cada bobina (A).
        """
        self.nSteps = nSteps
        self.L_canal = L_canal
        self.L_bobina = L_bobina
        self.Rin = Rin
        self.Rext = Rext
        self.N = N
        self.I = I
        self.muo = 4e-7 * np.pi  # Constante de permeabilidad del vacío [T·m/A]
        self.Rout = 0.5 * Rin    # Radio de los solenoides externos

        print(f"Inicializando: L = {L_canal} m, Rin = {Rin} m, Rext = {Rext} m, "
              f"N = {N} vueltas, I = {I} A")

        self.Solenoid_Create()

    def Solenoid_Create(self):
        """
        Genera las coordenadas de los solenoides (1 central y 4 periféricos) en el espacio.
        """

        phi = np.linspace(0, 2*np.pi, self.nSteps)
        self.Rout = 0.5*self.Rin #[m] -> Radio de los solenoides externos
        Rout_center = self.Rext

        def xParametrique_inner( phi ) : return self.Rin*np.cos(self.N*phi)
        def yParametrique_inner( phi ) : return self.Rin*np.sin(self.N*phi)
        def zParametrique_inner( phi ) : return self.L_canal*phi/(2*np.pi)

        def xParametrique_outer( phi ) : return self.Rout*np.cos(self.N*phi)
        def yParametrique_outer( phi ) : return self.Rout*np.sin(self.N*phi)
        def zParametrique_outer( phi ) : return self.L_canal*phi/(2*np.pi)

        X_inner = xParametrique_inner(phi)
        Y_inner = yParametrique_inner(phi)
        Z_inner = zParametrique_inner(phi)
        self.S_Inner = np.column_stack((X_inner,Y_inner,Z_inner))

        X1 = xParametrique_outer(phi) + Rout_center
        Y1 = yParametrique_outer(phi) + Rout_center
        Z1 = zParametrique_outer(phi)
        self.S1 = np.column_stack((X1,Y1,Z1))

        X2 = xParametrique_outer(phi) - Rout_center
        Y2 = yParametrique_outer(phi) + Rout_center
        Z2 = zParametrique_outer(phi)
        self.S2 = np.column_stack((X2,Y2,Z2))

        X3 = xParametrique_outer(phi) - Rout_center
        Y3 = yParametrique_outer(phi) - Rout_center
        Z3 = zParametrique_outer(phi)
        self.S3 = np.column_stack((X3,Y3,Z3))

        X4 = xParametrique_outer(phi) + Rout_center
        Y4 = yParametrique_outer(phi) - Rout_center
        Z4 = zParametrique_outer(phi)
        self.S4 = np.column_stack((X4,Y4,Z4))

    def Magnetic_Field(self, S: np.ndarray, S_solenoid: np.ndarray,
                       current: float = 4.5, chunk_size: int = 100) -> np.ndarray:
        """
        Calcula el campo magnético en una malla de puntos S debido a un solenoide S_solenoid.

        Parámetros:
        - S: Puntos del espacio donde calcular el campo magnético (Nx3).
        - S_solenoid: Coordenadas del hilo conductor del solenoide (Mx3).
        - current: Corriente en el solenoide (A).
        - chunk_size: Tamaño de los bloques para procesamiento vectorizado.

        Retorna:
        - Array Nx3 con los componentes del campo magnético [Bx, By, Bz].
        """
        mu0 = self.muo

        # Coordenadas de los puntos de evaluación
        xg, yg, zg = S.T
        Xs, Ys, Zs = S_solenoid.T

        # Inicialización del campo
        Bx, By, Bz = np.zeros_like(xg), np.zeros_like(yg), np.zeros_like(zg)

        # Diferenciales de línea dl para cada segmento del solenoide
        dlx = np.diff(Xs)
        dly = np.diff(Ys)
        dlz = np.diff(Zs)

        # Iteración por bloques
        for start in tqdm(range(0, len(dlx), chunk_size),
                          desc="Campo magnético (NumPy)", unit="chunk"):
            end = min(start + chunk_size, len(dlx))

            dlx_chunk = dlx[start:end]
            dly_chunk = dly[start:end]
            dlz_chunk = dlz[start:end]

            X_chunk = Xs[start:end]
            Y_chunk = Ys[start:end]
            Z_chunk = Zs[start:end]

            for k in range(len(dlx_chunk)):
                # Vector posición desde el elemento de corriente hacia el punto de evaluación
                rx = xg - X_chunk[k]
                ry = yg - Y_chunk[k]
                rz = zg - Z_chunk[k]

                rnorm = np.sqrt(rx**2 + ry**2 + rz**2)
                rnorm = np.maximum(rnorm, 1e-14)  # Evitar división por cero

                # Ley de Biot-Savart
                dBx = (dly_chunk[k] * rz - dlz_chunk[k] * ry) / rnorm**3
                dBy = (dlz_chunk[k] * rx - dlx_chunk[k] * rz) / rnorm**3
                dBz = (dlx_chunk[k] * ry - dly_chunk[k] * rx) / rnorm**3

                Bx += dBx
                By += dBy
                Bz += dBz

        # Escalar por la constante física
        factor = (mu0 * current) / (4.0 * np.pi)
        Bx *= factor
        By *= factor
        Bz *= factor

        return np.column_stack((Bx, By, Bz))

        #_______________________________

    def Total_Magnetic_Field(self, S, chunk_size=100):
        """
        Calcula el campo magnético total en los puntos especificados.

        El campo total se obtiene como la diferencia entre el campo del solenoide interno
        y la suma de los campos de los otros cuatro solenoides.

        Parámetros:
            S (np.ndarray): Puntos en los que se evalúa el campo magnético.
            chunk_size (int): Tamaño de bloques para el cálculo en paralelo o por partes.

        Retorna:
            np.ndarray: Campo magnético total en cada punto de S.
        """
        B_inner = self.Magnetic_Field(S=S, S_solenoid=self.S_Inner, current=self.I, chunk_size=chunk_size)
        B1 = self.Magnetic_Field(S=S, S_solenoid=self.S1, current=self.I, chunk_size=chunk_size)
        B2 = self.Magnetic_Field(S=S, S_solenoid=self.S2, current=self.I, chunk_size=chunk_size)
        B3 = self.Magnetic_Field(S=S, S_solenoid=self.S3, current=self.I, chunk_size=chunk_size)
        B4 = self.Magnetic_Field(S=S, S_solenoid=self.S4, current=self.I, chunk_size=chunk_size)

        B_total = B_inner - (B1 + B2 + B3 + B4)
        return B_total
        #_______________________________

    def Solenoid_points_plot_pyvista(
        self,
        Solenoid_inner=True,
        Solenoid_1=True,
        Solenoid_2=True,
        Solenoid_3=True,
        Solenoid_4=True,
        Cylinder_ext=True,
        plotter=None
    ):
        """
        Visualiza los puntos de los solenoides y el cilindro externo utilizando PyVista.

        Si se proporciona un `plotter`, se usa ese (útil para integración con QtInteractor).
        En caso contrario, se crea uno temporal y se muestra de inmediato.

        Parámetros:
            Solenoid_inner (bool): Mostrar solenoide interno.
            Solenoid_1 (bool): Mostrar solenoide 1.
            Solenoid_2 (bool): Mostrar solenoide 2.
            Solenoid_3 (bool): Mostrar solenoide 3.
            Solenoid_4 (bool): Mostrar solenoide 4.
            Cylinder_ext (bool): Mostrar el cilindro exterior.
            plotter (pv.Plotter): Instancia de PyVista Plotter o QtInteractor.

        Retorna:
            pv.Plotter | None: Retorna el plotter solo si fue creado localmente.
        """
        created_local_plotter = plotter is None
        if created_local_plotter:
            plotter = pv.Plotter()

        # Agregar puntos de cada solenoide
        if Solenoid_inner:
            plotter.add_points(self.S_Inner, color='black', point_size=8, render_points_as_spheres=True, label="Inner")
        if Solenoid_1:
            plotter.add_points(self.S1, color='red', point_size=8, render_points_as_spheres=True, label="S1")
        if Solenoid_2:
            plotter.add_points(self.S2, color='blue', point_size=8, render_points_as_spheres=True, label="S2")
        if Solenoid_3:
            plotter.add_points(self.S3, color='green', point_size=8, render_points_as_spheres=True, label="S3")
        if Solenoid_4:
            plotter.add_points(self.S4, color='orange', point_size=8, render_points_as_spheres=True, label="S4")
# Después de añadir los ejes y la grilla

        # Agregar cilindro exterior
        if Cylinder_ext:
            cylinder = pv.Cylinder(
                center=(0, 0, self.L_canal / 2),
                direction=(0, 0, 1),
                radius=self.Rext,
                height=self.L_canal,
                resolution=100
            )
            plotter.add_mesh(cylinder, color='gray', opacity=0.4, style='surface', label="Cilindro exterior")

        # Configuración del plotter
        plotter.set_background('white')
        plotter.add_axes(line_width=2, color='black')

        plotter.show_grid()

        if created_local_plotter:
            plotter.show(title="Solenoid Points 3D (PyVista)", auto_close=True)
            return plotter

    def B_Field_Heatmap(self, Solenoid_Center=False, All_Solenoids=False, XY=False, ZX=False, Plane_Value=0.0, resolution=100):
        """
        Genera un mapa de calor de la magnitud del campo magnético en un plano dado (XY o ZX).

        Parámetros:
        -----------
        Solenoid_Center : bool
            Si True, evalúa el campo magnético del solenoide interno.
        All_Solenoids : bool
            Si True, evalúa el campo magnético total de todos los solenoides.
        XY : bool
            Si True, genera el mapa en el plano XY a Z=Plane_Value.
        ZX : bool
            Si True, genera el mapa en el plano ZX a Y=Plane_Value.
        Plane_Value : float
            Valor constante de Z (si XY=True) o Y (si ZX=True) donde se genera el plano.
        resolution : int
            Número de puntos por eje en la malla estructurada para evaluación.

        Retorna:
        --------
        fig : matplotlib.figure.Figure
            Figura del mapa de calor generado.
        ax : matplotlib.axes._subplots.AxesSubplot
            Ejes del gráfico generado.
        """

        print("[DEBUG] Entrando a B_Field_Heatmap con", XY, ZX, Solenoid_Center, All_Solenoids)

        # Crear malla estructurada en XY o ZX
        if XY:
            xi = np.linspace(-1.5 * self.Rext, 1.5 * self.Rext, resolution)
            yi = np.linspace(-1.5 * self.Rext, 1.5 * self.Rext, resolution)
            Xi, Yi = np.meshgrid(xi, yi)
            S_eval = np.column_stack((Xi.ravel(), Yi.ravel(), np.full(Xi.size, Plane_Value)))
        elif ZX:
            xi = np.linspace(0.0, 1.5 * self.L_canal, resolution)  # Z
            yi = np.linspace(-1.5 * self.Rext, 1.5 * self.Rext, resolution)  # X
            Xi, Yi = np.meshgrid(xi, yi)
            S_eval = np.column_stack((Yi.ravel(), np.full(Xi.size, Plane_Value), Xi.ravel()))
        else:
            print("Error: Debes seleccionar un plano de visualización (XY o ZX).")
            return

        # Evaluar campo magnético
        if Solenoid_Center:
            B_eval = self.Magnetic_Field(S=S_eval, S_solenoid=self.S_Inner)
        elif All_Solenoids:
            B_eval = self.Total_Magnetic_Field(S=S_eval)
        else:
            print("Error: Debes especificar qué solenoides visualizar.")
            return

        # Extraer componentes y calcular magnitud
        if XY:
            Bx = B_eval[:, 0].reshape(Xi.shape)
            By = B_eval[:, 1].reshape(Yi.shape)
            Bmag = np.sqrt(Bx**2 + By**2)
            R = np.sqrt(Xi**2 + Yi**2)
            Bmag[R > self.Rext] = Bmag[Bmag > 1e-8].min()
        elif ZX:
            Bx = B_eval[:, 2].reshape(Xi.shape)  # Bz
            By = B_eval[:, 0].reshape(Yi.shape)  # Bx
            Bmag = np.sqrt(Bx**2 + By**2)

        # Preparar escala logarítmica
        vmin = Bmag[Bmag > 1e-8].min()
        vmax = Bmag.max()
        levels = np.logspace(np.log10(vmin), np.log10(vmax), 300)
        cmap = plt.get_cmap('inferno').copy()
        cmap.set_under('black')

        # Crear gráfico
        fig, ax = plt.subplots(figsize=(10, 8))
        heatmap = ax.contourf(Xi, Yi, Bmag, levels=levels, cmap=cmap, norm=colors.LogNorm(vmin=vmin, vmax=vmax))
        cbar = plt.colorbar(heatmap, ax=ax, ticks=np.linspace(vmin, vmax, 5))
        cbar.ax.yaxis.set_major_formatter('{:.2e}'.format)
        cbar.set_label("Magnitud del Campo Magnético [T]")

        # Etiquetas y geometría del canal
        if XY:
            ax.set_xlabel("X [m]")
            ax.set_ylabel("Y [m]")
            ax.set_title("Mapa de Calor del Campo Magnético - Plano XY")
            ax.set_xlim(-1.5 * self.Rext, 1.5 * self.Rext)
            ax.set_ylim(-1.5 * self.Rext, 1.5 * self.Rext)
            ax.add_patch(plt.Circle((0, 0), self.Rin, fill=True, linewidth=2, facecolor='gray'))
            ax.add_patch(plt.Circle((0, 0), self.Rext, fill=False, linewidth=4, edgecolor='gray'))
        elif ZX:
            ax.set_xlabel("Z [m]")
            ax.set_ylabel("X [m]")
            ax.set_title("Mapa de Calor del Campo Magnético - Plano ZX")
            ax.set_xlim(0.0, 1.5 * self.L_canal)
            ax.set_ylim(-1.5 * self.Rext, 1.5 * self.Rext)

            ax.add_patch(plt.Rectangle((0.0, self.Rext), self.L_canal, 0.5*self.Rext, facecolor='gray'))
            ax.add_patch(plt.Rectangle((0.0, -1.5*self.Rext), self.L_canal, 0.5*self.Rext, facecolor='gray'))
            ax.add_patch(plt.Rectangle((0.0, -self.Rin), self.L_canal, 2*self.Rin, facecolor='gray'))

        plt.tight_layout()
        return fig, ax

    def B_Field_Lines(self, Solenoid_Center=False, All_Solenoids=False, XY=False, ZX=False, Plane_Value=0.0, resolution=100, show=False):
        """
        Genera un gráfico de líneas de flujo del campo magnético en el plano XY o ZX.

        Parámetros:
        -----------
        Solenoid_Center : bool
            Si True, evalúa el campo del solenoide central.
        All_Solenoids : bool
            Si True, evalúa el campo total de todos los solenoides.
        XY : bool
            Si True, genera el gráfico en el plano XY.
        ZX : bool
            Si True, genera el gráfico en el plano ZX.
        Plane_Value : float
            Coordenada fija en Z (si XY=True) o Y (si ZX=True).
        resolution : int
            Resolución de la malla de evaluación.
        show : bool
            Si True, muestra la figura con plt.show().

        Retorna:
        --------
        fig : matplotlib.figure.Figure
            Figura del gráfico generado.
        ax : matplotlib.axes._subplots.AxesSubplot
            Ejes del gráfico generado.
        """

        fig, ax = plt.subplots(figsize=(10, 8))

        # Construir malla estructurada y puntos de evaluación
        if XY:
            xi = np.linspace(-1.5 * self.Rext, 1.5 * self.Rext, resolution)
            yi = np.linspace(-1.5 * self.Rext, 1.5 * self.Rext, resolution)
            Xi, Yi = np.meshgrid(xi, yi)
            S_eval = np.column_stack((Xi.ravel(), Yi.ravel(), np.full(Xi.size, Plane_Value)))
        elif ZX:
            xi = np.linspace(0.0, 1.5 * self.L_canal, resolution)
            yi = np.linspace(-1.5 * self.Rext, 1.5 * self.Rext, resolution)
            Xi, Yi = np.meshgrid(xi, yi)
            S_eval = np.column_stack((Yi.ravel(), np.full(Xi.size, Plane_Value), Xi.ravel()))
        else:
            print("Error: Debes seleccionar un plano de visualización (XY o ZX).")
            return

        # Evaluar campo magnético
        if Solenoid_Center:
            B_eval = self.Magnetic_Field(S=S_eval, S_solenoid=self.S_Inner)
        elif All_Solenoids:
            B_eval = self.Total_Magnetic_Field(S=S_eval)
        else:
            print("Error: Debes seleccionar el solenoide a visualizar.")
            return

        # Separar componentes
        if XY:
            Bx = B_eval[:, 0].reshape(Xi.shape)
            By = B_eval[:, 1].reshape(Yi.shape)
        elif ZX:
            Bx = B_eval[:, 2].reshape(Xi.shape)  # Bz
            By = B_eval[:, 0].reshape(Yi.shape)  # Bx

        Bmag = np.sqrt(Bx**2 + By**2)

        # Graficar fondo con magnitud del campo
        color_plot = ax.contourf(Xi, Yi, Bmag, levels=100, cmap='viridis')
        ax.streamplot(Xi, Yi, Bx, By, color='white', linewidth=0.7, density=1, arrowsize=0.7)

        cbar = plt.colorbar(color_plot, ax=ax)
        cbar.set_label("Magnitud del Campo Magnético [T]")

        # Configurar ejes y geometría
        if XY:
            ax.set_xlabel("X [m]")
            ax.set_ylabel("Y [m]")
            ax.set_title("Líneas del Campo Magnético - Plano XY")
            ax.set_xlim(-1.5 * self.Rext, 1.5 * self.Rext)
            ax.set_ylim(-1.5 * self.Rext, 1.5 * self.Rext)
            ax.add_patch(plt.Circle((0, 0), self.Rin, fill=True, linewidth=2, facecolor='black'))
            ax.add_patch(plt.Circle((0, 0), self.Rext, fill=False, linewidth=4, edgecolor='black'))
        elif ZX:
            ax.set_xlabel("Z [m]")
            ax.set_ylabel("X [m]")
            ax.set_title("Líneas del Campo Magnético - Plano ZX")
            ax.set_xlim(0.0, 1.5 * self.L_canal)
            ax.set_ylim(-1.5 * self.Rext, 1.5 * self.Rext)
            ax.add_patch(plt.Rectangle((0.0, self.Rext), self.L_canal, 0.5*self.Rext, facecolor='black'))
            ax.add_patch(plt.Rectangle((0.0, -1.5*self.Rext), self.L_canal, 0.5*self.Rext, facecolor='black'))
            ax.add_patch(plt.Rectangle((0.0, -self.Rin), self.L_canal, 2*self.Rin, facecolor='black'))

        plt.tight_layout()
        if show:
            plt.show()
        return fig, ax

    def save_magnetic_field(self, B: np.ndarray, S: np.ndarray) -> None:
        """
        Guarda el campo magnético evaluado en un archivo .npy junto con los puntos de evaluación.

        Parámetros:
            B (np.ndarray): Array de valores del campo magnético (N, 3).
            S (np.ndarray): Array de posiciones donde se evaluó el campo (N, 3).
        """
        if B.shape != S.shape or B.shape[1] != 3:
            raise ValueError("Las dimensiones de B y S no coinciden o no tienen 3 componentes.")

        data = np.column_stack((S, B))
        np.save(data_file("Magnetic_Field_np.npy"), data)
        print("Archivo 'Magnetic_Field_np.npy' guardado correctamente.")


    def plot_magnetic_field_simulation(self, resolution=300, plane_value=0.0):
        Rin = 0.028
        Rex = 0.05
        chamber_length = 0.02
        z_range = [0, 2 * self.L_canal]  # Ajusta según el tamaño de tu canal real
        x_range = [-1.2 * self.Rext, 1.2 * self.Rext]  # Hazlo apenas más grande que el canal

        # Cubre todo el rectángulo
        z_grid, x_grid = np.meshgrid(
            np.linspace(*z_range, resolution),
            np.linspace(*x_range, resolution)
        )
        S_eval = np.column_stack((x_grid.ravel(), np.full(x_grid.size, plane_value), z_grid.ravel()))
        B_eval = self.Total_Magnetic_Field(S=S_eval)
        Bx_grid = B_eval[:, 0].reshape(x_grid.shape)
        Bz_grid = B_eval[:, 2].reshape(z_grid.shape)
        Bmag_grid = np.sqrt(Bx_grid**2 + Bz_grid**2)

        # Máscaras geométricas
        mask_chamber = (z_grid <= self.L_canal) & ((np.abs(x_grid) < Rin) | (np.abs(x_grid) > Rex))

        mask_valid = np.isfinite(Bmag_grid) & (Bmag_grid > 0)
        if not np.any(mask_valid):
            raise ValueError("No hay datos válidos para graficar el campo magnético.")

        vmin = max(np.percentile(Bmag_grid[mask_valid], 1), 1e-7)
        vmax = np.percentile(Bmag_grid[mask_valid], 98)

        Bmag_grid_plot = np.copy(Bmag_grid)
        Bmag_grid_plot[~mask_valid] = np.nan
        # Bmag_grid_plot[~mask_valid] = vmin
        print("Cantidad de NaNs en Bmag_grid_plot:", np.isnan(Bmag_grid_plot).sum())
        print("Dimensiones:", Bmag_grid_plot.shape)
        from matplotlib.ticker import FuncFormatter
        fig, ax = plt.subplots(figsize=(8, 7))
        ax.set_facecolor('black')

        # Prepara el colormap para NaN
        cmap = plt.get_cmap('jet').copy()
        cmap.set_bad(color='green')  # O el color que prefieras

        # Contourf y colorbar formateada
        levels = np.logspace(np.log10(vmin), np.log10(vmax), 200)
        ctf = ax.contourf(z_grid, x_grid, Bmag_grid_plot, levels=levels, cmap=cmap,
                        norm=colors.LogNorm(vmin=vmin, vmax=vmax), alpha=0.85)

        ax.set_title('Campo Magnético en el Plano ZR', fontsize=16)
        ticks = np.logspace(np.log10(vmin), np.log10(vmax), 4)
        cb = plt.colorbar(ctf, ax=ax, label="|B| [T]", ticks=ticks)
        cb.formatter = FuncFormatter(lambda x, pos: f"{x:.2e}")
        cb.ax.tick_params(labelsize=12)
        cb.update_ticks()
        # Geometría y extras
        rect_central = plt.Rectangle(
            (0.0, -self.Rin), self.L_canal, 2*self.Rin,
            linewidth=0, edgecolor='black', facecolor='black', zorder=20, alpha = 0.45
        )
        ax.add_patch(rect_central)
        ax.streamplot(z_grid, x_grid, Bz_grid, Bx_grid,
                    color='blue', linewidth=1.1, density=2, arrowsize=1.1)
        ax.contourf(z_grid, x_grid, mask_chamber, levels=[0.5, 1], colors='black', alpha=0.45, zorder=10)
        ax.plot([0, self.L_canal, self.L_canal, 0, 0], [Rin, Rin, Rex, Rex, Rin], color='yellow', lw=2.5)
        ax.plot([0, self.L_canal, self.L_canal, 0, 0], [-Rin, -Rin, -Rex, -Rex, -Rin], color='yellow', lw=2.5)
        ax.plot([0, self.L_canal, self.L_canal, 0, 0], [Rex, Rex, -Rex, -Rex, Rex], color='yellow', lw=1.0, ls='--')

        ax.set_xlim(z_range)
        ax.set_ylim(x_range)
        ax.set_xlabel('z [m]', fontsize=13)
        ax.set_ylabel('r [m]', fontsize=13)
        plt.tight_layout()

               # --- Imprimir el valor del campo magnético en el centro del canal (z = centro, x = 0) ---
        z_centro = 0.5 * self.L_canal  # Mitad del canal
        x_centro = 0.0                 # Centro radial

        # Encuentra el índice más cercano en las mallas
        idx_z = (np.abs(z_grid[0, :] - z_centro)).argmin()
        idx_x = (np.abs(x_grid[:, 0] - x_centro)).argmin()

        B_centro = Bmag_grid[idx_x, idx_z]
        print(f"Valor de |B| en el centro del canal (z = {z_centro:.4f} m, x = {x_centro:.4f} m): {B_centro:.4e} T")

        plt.show()


if __name__ == "__main__":

    # Carga de datos espaciales desde archivo numpy
    E_Field_Data = np.load(data_file("E_Field_Poisson.npy"))
    spatial_coords = E_Field_Data[:, :3]

    # Inicialización del objeto B_Field con parámetros específicos
    B_field = B_Field(L_bobina=0.0075, nSteps=700, N=5000, I=5.5)

    # Cálculo del campo magnético en puntos espaciales dados
    B_magnetic = B_field.Magnetic_Field(S=spatial_coords, S_solenoid=B_field.S_Inner)

    # Cálculo del campo magnético total (incluye todas las contribuciones)
    B_total = B_field.Total_Magnetic_Field(S=spatial_coords)

    # Opciones para guardar o visualizar resultados (descomentar según necesidad):

    # Guardar matriz del campo magnético y posiciones en archivo .npy
    # B_field.Save_B_Field(B=B_total, S=spatial_coords)

    # Visualización de líneas de campo magnético en diferentes planos y configuraciones
    # B_field.B_Field_Lines(Solenoid_Center=False, All_Solenoids=True, XY=False, ZX=False,
    #                       Plane_Value=0.0, resolution=100, show=True)

    # Visualización del mapa de calor del campo magnético en plano XY
    # B_field.B_Field_Heatmap(XY=True, ZX=False, Plane_Value=0.01, Solenoid_Center=True, All_Solenoids=True)

    # Mapa de color personalizado para el campo magnético con contornos
    # B_field.color_map_B(S=spatial_coords, XY=True, Plane_Value=0.01, num_contorn=10,
    #                     resolution=400, Solenoid_Center=True)

    # Visualización de puntos correspondientes a solenoides (2D)
    # B_field.Solenoid_points_plot(Solenoid_1=True, Solenoid_2=True, Solenoid_3=True, Solenoid_4=True)

    # Visualización 3D de puntos de solenoides usando PyVista
    # B
