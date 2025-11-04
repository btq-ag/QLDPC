"""
Real-Time 2D Water Simulation using Stable Fluids

This script implements a real-time 2D fluid simulation based on the "Stable
Fluids" algorithm by Jos Stam. It features an interactive window where users
can add fluid density by clicking and dragging the mouse.

The animation displays the fluid's density field and provides a real-time
Frames Per Second (FPS) counter to benchmark performance.
"""

import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import os
import seaborn as sns

# --- Simulation Parameters ---
GRID_SIZE = 128       # Resolution of the simulation grid
DT = 0.1              # Time step
DIFFUSION = 0.0       # Diffusion rate (not used in this simple version)
VISCOSITY = 0.000001  # Fluid viscosity
FORCE_AMOUNT = 5.0    # Force added by mouse
DENSITY_AMOUNT = 100.0 # Density added by mouse
ANIMATION_INTERVAL = 1 # Milliseconds between frames

# --- Visualization Parameters ---
PLOT_DIR = 'Plots'
OUTPUT_FILENAME_GIF = os.path.join(PLOT_DIR, 'realtime_simulation.gif')
SEQUENTIAL_CMAP = sns.color_palette("mako", as_cmap=True)


class RealTimeFluidSolver:
    """
    A real-time fluid dynamics solver using the Stable Fluids method.
    """
    def __init__(self, size):
        self.size = size
        self.dt = DT
        self.diff = DIFFUSION
        self.visc = VISCOSITY

        # Velocity fields
        self.u = np.zeros((size, size))
        self.v = np.zeros((size, size))
        self.u_prev = np.zeros((size, size))
        self.v_prev = np.zeros((size, size))

        # Density field
        self.density = np.zeros((size, size))
        self.density_prev = np.zeros((size, size))

    def add_source(self, x, s, dt):
        x += dt * s

    def set_boundaries(self, b, x):
        """Enforce boundary conditions."""
        if b == 1: # Reflective for u
            x[0, :] = -x[1, :]
            x[-1, :] = -x[-2, :]
            x[:, 0] = x[:, 1]
            x[:, -1] = x[:, -2]
        elif b == 2: # Reflective for v
            x[0, :] = x[1, :]
            x[-1, :] = x[-2, :]
            x[:, 0] = -x[:, 1]
            x[:, -1] = -x[:, -2]
        else: # b == 0, for density
            x[0, :] = x[1, :]
            x[-1, :] = x[-2, :]
            x[:, 0] = x[:, 1]
            x[:, -1] = x[:, -2]
        
        # Corners
        x[0, 0] = 0.5 * (x[1, 0] + x[0, 1])
        x[0, -1] = 0.5 * (x[1, -1] + x[0, -2])
        x[-1, 0] = 0.5 * (x[-2, 0] + x[-1, 1])
        x[-1, -1] = 0.5 * (x[-2, -1] + x[-1, -2])

    def linear_solve(self, b, x, x0, a, c, iters=20):
        """Jacobi iteration for diffusion/viscosity."""
        c_recip = 1.0 / c
        for _ in range(iters):
            x[1:-1, 1:-1] = (x0[1:-1, 1:-1] + a * (x[:-2, 1:-1] + x[2:, 1:-1] + x[1:-1, :-2] + x[1:-1, 2:])) * c_recip
            self.set_boundaries(b, x)

    def diffuse(self, b, x, x0, rate, dt):
        a = dt * rate * (self.size - 2)**2
        self.linear_solve(b, x, x0, a, 1 + 4 * a)

    def advect(self, b, d, d0, u, v, dt):
        """Advection using bilinear interpolation."""
        dt0 = dt * (self.size - 2)
        
        # Grid indices
        i, j = np.meshgrid(np.arange(self.size), np.arange(self.size))

        # Backtrace coordinates
        x = np.clip(i - dt0 * u, 0.5, self.size - 1.5)
        y = np.clip(j - dt0 * v, 0.5, self.size - 1.5)
        
        # Get integer and fractional parts of coordinates
        i0, j0 = np.floor(x).astype(int), np.floor(y).astype(int)
        i1, j1 = i0 + 1, j0 + 1
        
        s1, t1 = x - i0, y - j0
        s0, t0 = 1 - s1, 1 - t1
        
        d[1:-1, 1:-1] = (s0[1:-1, 1:-1] * (t0[1:-1, 1:-1] * d0[j0[1:-1, 1:-1], i0[1:-1, 1:-1]] + t1[1:-1, 1:-1] * d0[j1[1:-1, 1:-1], i0[1:-1, 1:-1]]) +
                         s1[1:-1, 1:-1] * (t0[1:-1, 1:-1] * d0[j0[1:-1, 1:-1], i1[1:-1, 1:-1]] + t1[1:-1, 1:-1] * d0[j1[1:-1, 1:-1], i1[1:-1, 1:-1]]))
        self.set_boundaries(b, d)

    def project(self, u, v, p, div):
        """Hodge decomposition to make the velocity field mass-conserving."""
        h = 1.0 / (self.size - 2)
        div[1:-1, 1:-1] = -0.5 * h * (u[1:-1, 2:] - u[1:-1, :-2] + v[2:, 1:-1] - v[:-2, 1:-1])
        p.fill(0)
        self.set_boundaries(0, div)
        self.set_boundaries(0, p)
        self.linear_solve(0, p, div, 1, 4)
        
        u[1:-1, 1:-1] -= 0.5 * (p[1:-1, 2:] - p[1:-1, :-2]) / h
        v[1:-1, 1:-1] -= 0.5 * (p[2:, 1:-1] - p[:-2, 1:-1]) / h
        self.set_boundaries(1, u)
        self.set_boundaries(2, v)
    
    def velocity_step(self):
        self.add_source(self.u, self.u_prev, self.dt)
        self.add_source(self.v, self.v_prev, self.dt)
        
        self.u_prev, self.u = self.u, self.u_prev
        self.v_prev, self.v = self.v, self.v_prev
        
        self.diffuse(1, self.u, self.u_prev, self.visc, self.dt)
        self.diffuse(2, self.v, self.v_prev, self.visc, self.dt)
        
        self.project(self.u, self.v, self.u_prev, self.v_prev)
        
        self.u_prev, self.u = self.u, self.u_prev
        self.v_prev, self.v = self.v, self.v_prev
        
        self.advect(1, self.u, self.u_prev, self.u_prev, self.v_prev, self.dt)
        self.advect(2, self.v, self.v_prev, self.u_prev, self.v_prev, self.dt)
        
        self.project(self.u, self.v, self.u_prev, self.v_prev)
    
    def density_step(self):
        self.add_source(self.density, self.density_prev, self.dt)
        self.density_prev, self.density = self.density, self.density_prev
        self.diffuse(0, self.density, self.density_prev, self.diff, self.dt)
        self.density_prev, self.density = self.density, self.density_prev
        self.advect(0, self.density, self.density_prev, self.u, self.v, self.dt)

    def step(self):
        """Perform a full simulation step."""
        self.velocity_step()
        self.density_step()
        self.u_prev.fill(0)
        self.v_prev.fill(0)
        self.density_prev.fill(0)


# --- User Interaction and Animation ---
class FluidAnimation:
    def __init__(self, solver):
        self.solver = solver
        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.im = self.ax.imshow(self.solver.density, cmap=SEQUENTIAL_CMAP, origin='lower', vmin=0, vmax=1)
        
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_title("Real-Time Fluid Simulation (Click and Drag to Add Density)")

        # Performance tracking
        self.frame_count = 0
        self.start_time = time.time()
        self.fps_text = self.ax.text(0.02, 0.95, '', color='white', transform=self.ax.transAxes)

        # Mouse interaction state
        self.is_mouse_down = False
        self.prev_mouse_pos = None

        # Connect mouse events
        self.fig.canvas.mpl_connect('button_press_event', self.on_mouse_down)
        self.fig.canvas.mpl_connect('button_release_event', self.on_mouse_up)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

    def on_mouse_down(self, event):
        if event.inaxes == self.ax:
            self.is_mouse_down = True
            self.prev_mouse_pos = (int(event.xdata), int(event.ydata))

    def on_mouse_up(self, event):
        self.is_mouse_down = False
        self.prev_mouse_pos = None

    def on_mouse_move(self, event):
        if self.is_mouse_down and event.inaxes == self.ax:
            x, y = int(event.xdata), int(event.ydata)
            if self.prev_mouse_pos is not None:
                px, py = self.prev_mouse_pos
                dx, dy = x - px, y - py
                
                # Add density and force
                radius = 3
                yy, xx = np.ogrid[-radius:radius+1, -radius:radius+1]
                mask = xx**2 + yy**2 <= radius**2
                
                # Clamp coordinates to be within bounds
                x_min, x_max = max(0, x-radius), min(self.solver.size, x+radius+1)
                y_min, y_max = max(0, y-radius), min(self.solver.size, y+radius+1)
                
                mask_x_min = max(0, radius - x)
                mask_x_max = min(mask.shape[1], radius - x + self.solver.size)
                mask_y_min = max(0, radius - y)
                mask_y_max = min(mask.shape[0], radius - y + self.solver.size)

                self.solver.density_prev[y_min:y_max, x_min:x_max] += DENSITY_AMOUNT * mask[mask_y_min:mask_y_max, mask_x_min:mask_x_max]
                self.solver.u_prev[y_min:y_max, x_min:x_max] += FORCE_AMOUNT * dx * mask[mask_y_min:mask_y_max, mask_x_min:mask_x_max]
                self.solver.v_prev[y_min:y_max, x_min:x_max] += FORCE_AMOUNT * dy * mask[mask_y_min:mask_y_max, mask_x_min:mask_x_max]

            self.prev_mouse_pos = (x, y)

    def update(self, frame):
        self.solver.step()
        self.im.set_data(self.solver.density)
        self.im.set_clim(0, np.maximum(1.0, np.max(self.solver.density))) # Adjust color limit

        # Update FPS counter
        self.frame_count += 1
        elapsed_time = time.time() - self.start_time
        if elapsed_time > 1.0:
            fps = self.frame_count / elapsed_time
            self.fps_text.set_text(f'FPS: {fps:.2f}')
            self.start_time = time.time()
            self.frame_count = 0
            
        return [self.im, self.fps_text]

    def run(self):
        ani = animation.FuncAnimation(self.fig, self.update, blit=True, interval=ANIMATION_INTERVAL)
        plt.show()


if __name__ == "__main__":
    print("--- Starting Real-Time Fluid Simulation ---")
    print("Instructions: Click and drag your mouse to add fluid density and apply forces.")
    
    fluid_solver = RealTimeFluidSolver(GRID_SIZE)
    app = FluidAnimation(fluid_solver)
    app.run()
    
    print("--- Simulation window closed. ---") 