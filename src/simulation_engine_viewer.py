import numpy as np
import pyvista as pv
import time
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pyvistaqt import QtInteractor

import os

from project_paths import data_file


class Simulation():
    def __init__(self, plotter=None, L=0.02, Rin=0.028, Rex=0.05):
        self.particle_path = data_file("particle_simulation.npy")
        self.L = L
        self.Rin = Rin
        self.Rex = Rex

        # Variables de control de estado
        self.current_frame = 0
        self.window_closed = False
        self.pause = {"valor": False}

        # 1) Carga inicial de datos y conteo de frames/partículas
        self.reload_data()
        # Ahora reload_data ya dejó en self.all_positions y en
        # self.num_frames, self.num_particles, y reinició current_frame=0.
        self.prev_num_particles = self.num_particles

        # 2) Si no se recibe plotter, se crea uno de PyVista
        if plotter is None:
            plotter = pv.Plotter(window_size=[1280, 800])
        self.plotter = plotter

        # 3) Crear geometría fija del propulsor y configurar la cámara
        self.Geometries_creation()
        self.Plot_Configuration()

        # 4) Crear los actores iniciales de partículas usando el primer frame
        # Solo necesitas llamar a _create_particle_actors(),
        # no es necesario tener un refresh_particles() separado aquí.
        self._create_particle_actors()

    def _create_particle_actors(self):
        # 1) Si existieran actores anteriores, los elimino
        if hasattr(self, 'ion_actor') and self.ion_actor is not None:
            try:
                self.plotter.remove_actor(self.ion_actor)
            except Exception:
                pass
            self.ion_actor = None

        if hasattr(self, 'neutral_actor') and self.neutral_actor is not None:
            try:
                self.plotter.remove_actor(self.neutral_actor)
            except Exception:
                pass
            self.neutral_actor = None

        # 2) Tomo los puntos del frame 0
        frame0 = self.all_positions[0]
        mask_ions = frame0[:, 3] == 1
        mask_neutral = frame0[:, 3] == 0
        ions0 = frame0[mask_ions, :3]
        neut0 = frame0[mask_neutral, :3]

        # 3) Creo nuevos PolyData
        self.ions = pv.PolyData(ions0)
        self.neutrals = pv.PolyData(neut0)

        # 4) Calculo point_size según self.num_particles
        if self.num_particles <= 4000:
            ps = 3.0
        elif self.num_particles <= 10000:
            ps = 2.5
        elif self.num_particles <= 100000:
            ps = 1.5
        else:
            ps = 1.0

        # 5) Agrego los actores nuevos
        if self.ions.n_points > 0:
            self.ion_actor = self.plotter.add_mesh(
                self.ions,
                color='deepskyblue',
                point_size=ps,
                render_points_as_spheres=True,
                lighting=True,
                specular=0.9,
                diffuse=1,
                ambient=0.3
            )
        else:
            self.ion_actor = None

        if self.neutrals.n_points > 0:
            self.neutral_actor = self.plotter.add_mesh(
                self.neutrals,
                color='red',
                point_size=ps,
                render_points_as_spheres=True,
                lighting=True,
                specular=0.9,
                diffuse=1,
                ambient=0.3
            )
        else:
            self.neutral_actor = None

        # 6) Forzar una actualización de la vista
        self.plotter.update()

        # 7) Actualizo el valor previo de num_particles
        self.prev_num_particles = self.num_particles



    def reload_data(self):
        """
        Vuelve a cargar el archivo .npy desde disco y actualiza:
            - self.all_positions
            - self.num_frames
            - self.num_particles
        Úselo siempre que el archivo en disco haya cambiado (por ejemplo,
        después de terminar el subproceso que genera el .npy).
        """
        self.all_positions = np.load(self.particle_path, mmap_mode="r")
        self.num_frames, self.num_particles, _ = self.all_positions.shape
        # Reiniciar el frame actual a 0 para que la animación empiece desde el inicio
        self.current_frame = 0


    def refresh_particles(self):
        """
        Elimina los actores previos de iones y neutros (si existen) y vuelve
        a crear dos actores nuevos usando la información del primer frame
        actualizada en self.all_positions.
        """
        # --- 1) Remover actores antiguos (si ya existían) ---
        if hasattr(self, 'ion_actor') and self.ion_actor is not None:
            try:
                self.plotter.remove_actor(self.ion_actor)
            except Exception:
                pass
            self.ion_actor = None

        if hasattr(self, 'neutral_actor') and self.neutral_actor is not None:
            try:
                self.plotter.remove_actor(self.neutral_actor)
            except Exception:
                pass
            self.neutral_actor = None

        # --- 2) Extraer los puntos del primer frame (frame 0) para iones y neutros ---
        frame_data = self.all_positions[0]
        mask_ions = frame_data[:, 3] == 1
        mask_neutrals = frame_data[:, 3] == 0

        ions_points = frame_data[mask_ions, :3]
        neutrals_points = frame_data[mask_neutrals, :3]

        # --- 3) Crear nuevos objetos PolyData (self.ions, self.neutrals) ---
        self.ions = pv.PolyData(ions_points)
        self.neutrals = pv.PolyData(neutrals_points)

        # --- 4) Determinar tamaño de partícula (punto 3) según total de partículas ---
        if self.num_particles <= 4000:
            particle_size = 3.0
        elif self.num_particles <= 10000:
            particle_size = 2.5
        elif self.num_particles <= 100000:
            particle_size = 1.5
        else:
            particle_size = 1.0

        # --- 5) Crear los actores nuevos en el plotter ---
        if self.ions.n_points > 0:
            self.ion_actor = self.plotter.add_mesh(
                self.ions,
                color='deepskyblue',
                point_size=particle_size,
                render_points_as_spheres=True,
                lighting=True,
                specular=0.9,
                diffuse=1,
                ambient=0.3
            )
        else:
            self.ion_actor = None

        if self.neutrals.n_points > 0:
            self.neutral_actor = self.plotter.add_mesh(
                self.neutrals,
                color='red',
                point_size=particle_size,
                render_points_as_spheres=True,
                lighting=True,
                specular=0.9,
                diffuse=1,
                ambient=0.3
            )
        else:
            self.neutral_actor = None

        # --- 6) Forzar actualización de la escena (para que se vea al instante) ---
        self.plotter.update()


    def step_frame(self, neutral_visible=False):
        """
        Avanza un frame en la animación. Aquí simplemente actualizo los
        puntos de los actores existentes para el frame self.current_frame.
        """
        if self.current_frame >= self.num_frames:
            return False

        frame_data = self.all_positions[self.current_frame]
        if np.isnan(frame_data).any() or np.isinf(frame_data).any():
            print("[ERROR] Datos inválidos (NaN o Inf) en frame", self.current_frame)
            return False

        mask_ions = frame_data[:, 3] == 1
        ions_points = frame_data[mask_ions, :3]
        mask_neutrals = frame_data[:, 3] == 0
        neutrals_points = frame_data[mask_neutrals, :3]

        # Actualiza los puntos del PolyData de iones
        if self.ion_actor is not None:
            if ions_points.shape[0] > 0:
                self.ions.points = ions_points
                self.ion_actor.mapper.dataset.points = ions_points
                self.ion_actor.SetVisibility(True)
            else:
                self.ion_actor.SetVisibility(False)

        # Actualiza los puntos del PolyData de neutros
        if self.neutral_actor is not None and neutral_visible:
            if neutrals_points.shape[0] > 0:
                self.neutrals.points = neutrals_points
                self.neutral_actor.mapper.dataset.points = neutrals_points
                self.neutral_actor.SetVisibility(True)
            else:
                self.neutral_actor.SetVisibility(False)
        elif self.neutral_actor is not None:
            self.neutral_actor.SetVisibility(False)

        self.plotter.update()
        self.current_frame += 1
        return True


    def reset_animation(self):
        self.current_frame = 0


    def on_close(self):
        self.window_closed = True


    def pause_simulation(self):
        self.pause["valor"] = not self.pause["valor"]
        estado = "Pausada" if self.pause["valor"] else "Reanudada"
        print(f"\n⏸️  Simulación: {estado}")


    def Geometries_creation(self):
        """
        Crea la carcasa del propulsor (cilindros, tapas, ejes, etc.) y la
        añade al plotter. Esto permanece inmutable entre corridas.
        """
        Rsol_ext = self.Rin / 2
        ancho_plano = (self.Rex * 2) + self.Rin
        espesor_plano = 0.001

        helping_value_Rin = 0.01 * self.Rin
        helping_value_L = 0.01 * self.L

        centro = (0, 0, (self.L) / 2)
        centro_solenoid = self.Rex
        direccion = (0, 0, 1)

        cilindro_ext = pv.Cylinder(center=centro, direction=direccion,
                                  radius=self.Rex, height=self.L, resolution=200).triangulate()
        cilindro_int = pv.Cylinder(center=centro, direction=direccion,
                                  radius=self.Rin, height=self.L, resolution=200).triangulate()

        cilindro_hueco = cilindro_ext.boolean_difference(cilindro_int).clean()
        cilindro = cilindro_hueco.clip(
            normal="z", origin=(centro[0], centro[1], self.L - 1e-6), invert=True
        )

        cilindro_tapa = pv.Cylinder(
            center=centro,
            direction=direccion,
            radius=self.Rin - helping_value_Rin,
            height=self.L + helping_value_L,
            resolution=200
        ).triangulate()

        plano_solid = pv.Cube(
            center=(0, 0, 0),
            x_length=ancho_plano,
            y_length=ancho_plano,
            z_length=espesor_plano
        ).triangulate()

        plano_hueco_aux = pv.Cube(
            center=(0, 0, self.L),
            x_length=ancho_plano,
            y_length=ancho_plano,
            z_length=espesor_plano
        ).triangulate()
        cilindro_corte = pv.Cylinder(
            center=(0, 0, self.L),
            direction=direccion,
            radius=self.Rex,
            height=10,
            resolution=100
        ).triangulate()
        plano_hueco = plano_hueco_aux.boolean_difference(cilindro_corte)

        cilindro_1 = pv.Cylinder(
            center=(centro_solenoid, centro_solenoid, (self.L) / 2),
            direction=(0, 0, 1),
            radius=Rsol_ext,
            height=self.L,
            resolution=50
        )
        cilindro_2 = pv.Cylinder(
            center=(centro_solenoid, -centro_solenoid, (self.L) / 2),
            direction=(0, 0, 1),
            radius=Rsol_ext,
            height=self.L,
            resolution=50
        )
        cilindro_3 = pv.Cylinder(
            center=(-centro_solenoid, centro_solenoid, (self.L) / 2),
            direction=(0, 0, 1),
            radius=Rsol_ext,
            height=self.L,
            resolution=50
        )
        cilindro_4 = pv.Cylinder(
            center=(-centro_solenoid, -centro_solenoid, (self.L) / 2),
            direction=(0, 0, 1),
            radius=Rsol_ext,
            height=self.L,
            resolution=50
        )

        self.plotter.set_background("white")
        self.plotter.add_mesh(
            cilindro,
            color="#656565",
            opacity=1,
            show_edges=False,
            specular=1.0,
            specular_power=30,
            diffuse=0.8,
            ambient=0.2
        )
        self.plotter.add_mesh(
            plano_solid,
            color="gray",
            opacity=1,
            specular=1.0,
            specular_power=30,
            diffuse=0.8,
            ambient=0.3
        )
        self.plotter.add_mesh(
            plano_hueco,
            color="gray",
            opacity=1,
            specular=1.0,
            specular_power=30,
            diffuse=0.8,
            ambient=0.3
        )
        self.plotter.add_mesh(
            cilindro_tapa,
            color="gray",
            opacity=1,
            specular=1.0,
            specular_power=30,
            diffuse=0.8,
            ambient=0.3
        )
        self.plotter.add_mesh(
            cilindro_1,
            color="#CD7F32",
            opacity=1,
            specular=1.0,
            specular_power=30,
            diffuse=0.8,
            ambient=0.3
        )
        self.plotter.add_mesh(
            cilindro_2,
            color="#CD7F32",
            opacity=1,
            specular=1.0,
            specular_power=30,
            diffuse=0.8,
            ambient=0.3
        )
        self.plotter.add_mesh(
            cilindro_3,
            color="#CD7F32",
            opacity=1,
            specular=1.0,
            specular_power=30,
            diffuse=0.8,
            ambient=0.3
        )
        self.plotter.add_mesh(
            cilindro_4,
            color="#CD7F32",
            opacity=1,
            specular=1.0,
            specular_power=30,
            diffuse=0.8,
            ambient=0.3
        )


    def Plot_Configuration(self):
        """
        Configura cámara, luces, texto y ejes fijos. Esto solo se llama
        al inicio o si realmente necesita reconfigurar la cámara (p. ej.
        cambios de geometría muy grandes).
        """
        self.plotter.camera_position = [
            (-5 * self.Rex, 2.5 * self.Rex, 5 * self.Rex),
            (0, 0, 0),
            (0, 1, 0)
        ]
        self.plotter.camera.view_angle = 60

        light = pv.Light(
            position=(-5 * self.Rex, -5 * self.Rex, -7 * self.Rex),
            focal_point=(0, 0, 0),
            intensity=1.5
        )
        self.plotter.add_light(light)

        # Texto y ejes fijos (no se recrea cada frame)
        self.plotter.add_text("Simulación", position="upper_edge", color='Black', font_size=6)

        self.plotter.iren.add_observer("ExitEvent", lambda *_: self.on_close())

        x_line = pv.Line(pointa=(-100, 0, 0), pointb=(100, 0, 0))
        y_line = pv.Line(pointa=(0, -100, 0), pointb=(0, 100, 0))
        z_line = pv.Line(pointa=(0, 0, -100), pointb=(0, 0, 100))

        self.plotter.add_mesh(x_line, color='red', line_width=3)
        self.plotter.add_mesh(y_line, color='green', line_width=3)
        self.plotter.add_mesh(z_line, color='blue', line_width=3)


    def Animation(self, neutral_visible=False):
        """
        Ejecuta el bucle de animación y actualiza los PolyData de iones y neutros.
        Cada vez que cambia el número de partículas, recrea actores y recrea los buffers
        para que su forma siempre coincida con el nuevo tamaño.
        """
        if isinstance(self.plotter, pv.Plotter) and not isinstance(self.plotter, QtInteractor):
            self.plotter.show(auto_close=False, interactive_update=True)

        self.plotter.add_key_event("space", self.pause_simulation)
        self.plotter.add_key_event("Return", lambda: self._restart_animation())

        # Partimos con la cantidad inicial de partículas
        max_particles = self.num_particles

        if neutral_visible == False:
            self.neutral_actor.SetVisibility(False)


        while (not self.window_closed) and (self.current_frame < self.num_frames):
            # 1) Si terminamos todos los frames, solo hacemos pausa
            if self.current_frame >= self.num_frames:
                self.pause["valor"] = True
                self.current_frame = self.num_frames - 1

            # 2) Si está en pausa, solo actualizamos la escena
            while self.pause["valor"] and not self.window_closed:
                self.plotter.update()
                time.sleep(0.001)

            # 3) Chequeo si cambió la cantidad de partículas: si sí, recreo actores
            if self.num_particles != self.prev_num_particles:
                self._create_particle_actors()
                max_particles = self.num_particles
                # IMPORTANTE: reinicializo prev_num_particles para que no vuelva a pasar
                # hasta que cambie otra vez
                self.prev_num_particles = self.num_particles

            # 4) Ahora sí obtengo los datos del frame actual
            frame = self.current_frame
            frame_data = self.all_positions[frame]

            mask_ions = frame_data[:, 3] == 1
            ions_points = frame_data[mask_ions, :3]
            num_ions = len(ions_points)

            # 5) Creo buffers nuevos de longitud max_particles
            #    Esto evita el broadcast si num_ions > buffer antiguo
            buffer_ions = np.full((max_particles, 3), np.nan, dtype=np.float32)

            if self.ion_actor is not None:
                if num_ions > 0:
                    # Copio únicamente los primeros num_ions puntos
                    buffer_ions[:num_ions] = ions_points[:num_ions]
                    self.ions.points = buffer_ions
                    # Con mapper.update() solicitamos al actor que recargue el PolyData
                    self.ion_actor.mapper.update()
                    self.ion_actor.SetVisibility(True)
                else:
                    self.ion_actor.SetVisibility(False)

            # 6) Lo mismo para neutros (solo si neutral_visible=True)
            if neutral_visible and self.neutral_actor is not None:
                mask_neutrals = frame_data[:, 3] == 0
                neutrals_points = frame_data[mask_neutrals, :3]
                num_neutrals = len(neutrals_points)

                buffer_neutrals = np.full((max_particles, 3), np.nan, dtype=np.float32)
                if num_neutrals > 0:
                    buffer_neutrals[:num_neutrals] = neutrals_points[:num_neutrals]
                    self.neutrals.points = buffer_neutrals
                    self.neutral_actor.mapper.update()
                    self.neutral_actor.SetVisibility(True)
                else:
                    self.neutral_actor.SetVisibility(False)
            else:
                num_neutrals = self.num_particles - num_ions
                self.neutral_actor.SetVisibility(False)

            # 7) Refrescar la escena e incrementar frame
            self.plotter.update()
            time.sleep(1/60)
            print(f"\rFrame: {frame + 1}/{self.num_frames} | Iones: {num_ions} | Neutros: {num_neutrals}", end='', flush=True)

            self.current_frame += 1
        self.reload_data()
        self.refresh_particles()
        print("\n")


    def _restart_animation(self):
        """
        Handler para cuando el usuario presiona "Return" en la ventana PyVista.
        Reinicia la animación desde el frame 0.
        """
        print("[DEBUG] Reiniciando animación desde tecla Enter.")
        self.current_frame = 0
        self.pause["valor"] = False


    def is_finished(self):
        return self.current_frame >= self.num_frames - 1


# --- Fin de la clase Simulation ---
