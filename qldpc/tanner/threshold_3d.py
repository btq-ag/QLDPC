"""
Real-Time 3D Quantum LDPC Threshold Landscape Visualizer

Dark-themed tkinter GUI with embedded matplotlib 3D surface for:
  - Error threshold surfaces across code families
  - Distance scaling analysis
  - Code rate / code length trade-offs
  - Real-time parameter adjustment and auto-rotation

Usage:
    qldpc-threshold          # via console entry point
    python -m qldpc.tanner.threshold_3d
"""

import matplotlib
matplotlib.use("TkAgg")

import tkinter as tk
from tkinter import ttk
import numpy as np
import os
import seaborn as sns

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from qldpc.theme import (
    DARK_BG, DARK_PANEL, DARK_AXES, DARK_TEXT, DARK_SUBTITLE,
    DARK_ACCENT, DARK_ACCENT_ALT, DARK_GRID, DARK_EDGE,
    DARK_INPUT,
    COLOR_SUCCESS, COLOR_ERROR,
    apply_dark_theme, configure_dark_3d_axes,
)

# ---------------------------------------------------------------------------
# Colormaps
# ---------------------------------------------------------------------------
seqCmap = sns.color_palette("mako", as_cmap=True)
divCmap = sns.cubehelix_palette(start=0.5, rot=-0.5, as_cmap=True)
lightCmap = sns.cubehelix_palette(
    start=2, rot=0, dark=0, light=0.95, reverse=True, as_cmap=True
)

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_COOPERATIVITY = 1e5
SURFACE_RESOLUTION = 50
ANIMATION_INTERVAL = 80  # ms


# =========================================================================
# Model
# =========================================================================

class QuantumLDPCThresholdModel:
    """Model for quantum LDPC threshold behaviour and scaling analysis."""

    FAMILY_NAMES = [
        "Surface Codes",
        "Hypergraph Product",
        "Quantum Tanner (Breakthrough)",
    ]
    MODE_NAMES = ["Error Threshold Landscape", "Distance Scaling Analysis"]

    def __init__(self):
        self.cooperativity = DEFAULT_COOPERATIVITY
        self.code_family = 0
        self.visualization_mode = 0

    def calculate_threshold_surface(self):
        p = np.linspace(0.001, 0.1, SURFACE_RESOLUTION)
        d = np.linspace(10, 100, SURFACE_RESOLUTION)
        P, D = np.meshgrid(p, d)

        thresholds = [0.005, 0.01, 0.03]
        th = thresholds[self.code_family]

        if self.code_family == 0:
            exp = (D + 1) / 2
        elif self.code_family == 1:
            exp = (D * np.log(D + 1) + 1) / 2
        else:
            exp = D

        Z = np.where(
            P < th,
            np.exp(-exp * (th - P) / th),
            (P / th) ** 0.5,
        )
        cavity = max(0.1, 1 - 1 / self.cooperativity)
        Z = Z * cavity * 10 + 0.01
        return P, D, Z

    def calculate_scaling_surface(self):
        n = np.linspace(100, 1000, SURFACE_RESOLUTION)
        r = np.linspace(0.1, 0.9, SURFACE_RESOLUTION)
        N, R = np.meshgrid(n, r)

        if self.code_family == 0:
            Z = np.sqrt(N) * (1.1 - R) * 0.5
        elif self.code_family == 1:
            Z = np.sqrt(N * np.log(N + 1)) * (1.1 - R) * 0.3
        else:
            Z = N * 0.15 * (1.2 - R)

        Z = np.maximum(Z, 5.0)
        return N, R, Z


# =========================================================================
# GUI
# =========================================================================

class ThresholdLandscape3DGUI:
    """Tkinter dark-mode GUI with embedded 3D threshold landscape."""

    TITLE = "3D Quantum LDPC Threshold Landscape"

    def __init__(self, model=None):
        self.model = model or QuantumLDPCThresholdModel()
        self.azimuth = 45.0
        self.elevation = 30.0
        self.auto_rotate = True
        self.rotation_speed = 1.0
        self.show_wireframe = False
        self.show_grid = True
        self._needs_redraw = True
        self._colorbar = None

        self.root = tk.Tk()
        self.root.title(self.TITLE)
        self.root.geometry("1320x860")
        self.root.minsize(960, 640)
        self.style = apply_dark_theme(self.root)

        self._build_ui()
        self._animate()

    # -- UI -----------------------------------------------------------------

    def _build_ui(self):
        outer = ttk.Frame(self.root, style="Dark.TFrame")
        outer.pack(fill=tk.BOTH, expand=True)
        self._build_controls(outer)
        self._build_canvas(outer)

    def _build_controls(self, parent):
        ctrl = ttk.Frame(parent, style="Dark.TFrame", width=260)
        ctrl.pack(side=tk.LEFT, fill=tk.Y, padx=(8, 0), pady=8)
        ctrl.pack_propagate(False)

        ttk.Label(ctrl, text="Threshold 3D", style="Title.TLabel").pack(
            anchor=tk.W, pady=(0, 8)
        )

        # --- Cavity QED ----------------------------------------------------
        cav = ttk.LabelFrame(ctrl, text="Cavity QED", style="Dark.TLabelframe")
        cav.pack(fill=tk.X, pady=4)

        ttk.Label(cav, text="Cooperativity (C)", style="Dark.TLabel").pack(
            anchor=tk.W, padx=4
        )
        self.coop_var = tk.DoubleVar(value=5.0)
        ttk.Scale(
            cav, from_=3.0, to=6.0, variable=self.coop_var,
            orient=tk.HORIZONTAL, style="Dark.Horizontal.TScale",
            command=self._on_coop,
        ).pack(fill=tk.X, padx=4, pady=2)
        self.coop_label = ttk.Label(cav, text="C = 1.00e+05", style="Accent.TLabel")
        self.coop_label.pack(anchor=tk.W, padx=4, pady=(0, 4))

        # --- Code family ---------------------------------------------------
        fam = ttk.LabelFrame(ctrl, text="Code Family", style="Dark.TLabelframe")
        fam.pack(fill=tk.X, pady=4)

        self.family_var = tk.IntVar(value=0)
        for i, name in enumerate(self.model.FAMILY_NAMES):
            ttk.Radiobutton(
                fam, text=name, variable=self.family_var, value=i,
                style="Dark.TRadiobutton", command=self._on_family,
            ).pack(anchor=tk.W, padx=4)
        self.family_insight = ttk.Label(fam, text="d ~ sqrt(n), R ~ 1/n", style="Subtitle.TLabel")
        self.family_insight.pack(anchor=tk.W, padx=4, pady=(2, 4))

        # --- View mode -----------------------------------------------------
        vm = ttk.LabelFrame(ctrl, text="View Mode", style="Dark.TLabelframe")
        vm.pack(fill=tk.X, pady=4)

        self.mode_var = tk.IntVar(value=0)
        for i, name in enumerate(self.model.MODE_NAMES):
            ttk.Radiobutton(
                vm, text=name, variable=self.mode_var, value=i,
                style="Dark.TRadiobutton", command=self._on_mode,
            ).pack(anchor=tk.W, padx=4)

        # --- Display -------------------------------------------------------
        disp = ttk.LabelFrame(ctrl, text="Display", style="Dark.TLabelframe")
        disp.pack(fill=tk.X, pady=4)

        self.wire_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(disp, text="Wireframe", variable=self.wire_var,
                        style="Dark.TCheckbutton",
                        command=self._mark_redraw).pack(anchor=tk.W, padx=4)

        self.grid_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(disp, text="Grid", variable=self.grid_var,
                        style="Dark.TCheckbutton",
                        command=self._mark_redraw).pack(anchor=tk.W, padx=4)

        self.rotate_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(disp, text="Auto Rotate", variable=self.rotate_var,
                        style="Dark.TCheckbutton").pack(anchor=tk.W, padx=4)

        ttk.Label(disp, text="Rotation Speed", style="Dark.TLabel").pack(anchor=tk.W, padx=4)
        self.speed_var = tk.DoubleVar(value=1.0)
        ttk.Scale(
            disp, from_=0.0, to=5.0, variable=self.speed_var,
            orient=tk.HORIZONTAL, style="Dark.Horizontal.TScale",
        ).pack(fill=tk.X, padx=4, pady=(2, 4))

        # --- Info ----------------------------------------------------------
        info = ttk.LabelFrame(ctrl, text="Insight", style="Dark.TLabelframe")
        info.pack(fill=tk.X, pady=4, expand=True)

        self.info_text = tk.Text(
            info, height=5, wrap=tk.WORD,
            bg=DARK_INPUT, fg=DARK_ACCENT, insertbackground=DARK_ACCENT,
            font=("Consolas", 9), relief=tk.FLAT, bd=0,
        )
        self.info_text.pack(fill=tk.BOTH, padx=4, pady=4, expand=True)
        self._refresh_insight()

        ttk.Label(
            ctrl, text="Drag to rotate | Scroll to zoom",
            style="Subtitle.TLabel", wraplength=240,
        ).pack(anchor=tk.W, pady=(8, 0))

    def _build_canvas(self, parent):
        frame = ttk.Frame(parent, style="Dark.TFrame")
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.fig = Figure(figsize=(10, 8), facecolor=DARK_BG)
        self.ax = self.fig.add_subplot(111, projection="3d")
        configure_dark_3d_axes(self.ax)

        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.canvas.mpl_connect("scroll_event", self._on_scroll)
        self.canvas.mpl_connect("button_press_event", self._on_click)

    # -- callbacks ----------------------------------------------------------

    def _on_coop(self, val):
        C = 10 ** float(val)
        self.model.cooperativity = C
        self.coop_label.configure(text=f"C = {C:.2e}")
        self._mark_redraw()

    def _on_family(self):
        self.model.code_family = self.family_var.get()
        self._refresh_insight()
        self._mark_redraw()

    def _on_mode(self):
        self.model.visualization_mode = self.mode_var.get()
        self._mark_redraw()

    def _mark_redraw(self):
        self._needs_redraw = True

    def _on_scroll(self, event):
        if event.inaxes == self.ax:
            factor = 0.9 if event.step > 0 else 1.1
            for getter, setter in [
                (self.ax.get_xlim, self.ax.set_xlim),
                (self.ax.get_ylim, self.ax.set_ylim),
                (self.ax.get_zlim, self.ax.set_zlim),
            ]:
                lo, hi = getter()
                c = (lo + hi) / 2
                r = (hi - lo) * factor / 2
                setter([c - r, c + r])

    def _on_click(self, event):
        if event.inaxes == self.ax:
            self.rotate_var.set(False)

    def _refresh_insight(self):
        insights = [
            "Surface codes:\n  d ~ sqrt(n)\n  R ~ 1/n\n  Threshold ~ 0.5%\n  Traditional approach",
            "Hypergraph product:\n  d ~ sqrt(n log n)\n  R = const\n  Threshold ~ 1%\n  Improved scaling",
            "Quantum Tanner:\n  d ~ n (LINEAR!)\n  R = const\n  Threshold ~ 3%\n  2022 breakthrough!",
        ]
        self.info_text.configure(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert(tk.END, insights[self.model.code_family])
        self.info_text.configure(state=tk.DISABLED)

        scaling_labels = ["d ~ sqrt(n), R ~ 1/n", "d ~ sqrt(n log n), R = const", "d ~ n, R = const  (BREAKTHROUGH)"]
        self.family_insight.configure(text=scaling_labels[self.model.code_family])

    # -- drawing ------------------------------------------------------------

    def _draw_surface(self):
        stored_elev = self.ax.elev if hasattr(self.ax, "elev") else self.elevation
        stored_azim = self.ax.azim if hasattr(self.ax, "azim") else self.azimuth

        self.ax.clear()
        self.ax.set_facecolor(DARK_AXES)

        if self.model.visualization_mode == 0:
            X, Y, Z = self.model.calculate_threshold_surface()
            xl, yl, zl = "Physical Error Rate", "Code Distance", "Logical Error Rate"
        else:
            X, Y, Z = self.model.calculate_scaling_surface()
            xl, yl, zl = "Code Length (n)", "Code Rate (k/n)", "Distance (d)"

        cmaps = [lightCmap, divCmap, seqCmap]
        cmap = cmaps[self.model.code_family]

        if self.wire_var.get():
            self.ax.plot_wireframe(X, Y, Z, color=DARK_ACCENT, alpha=0.6, linewidth=0.7)
        else:
            surf = self.ax.plot_surface(
                X, Y, Z, cmap=cmap, alpha=0.85,
                linewidth=0, antialiased=True, shade=True,
            )
            # Colorbar
            if self._colorbar is not None:
                try:
                    self._colorbar.remove()
                except Exception:
                    pass
            try:
                self._colorbar = self.fig.colorbar(surf, ax=self.ax, shrink=0.45, aspect=25, pad=0.08)
                self._colorbar.set_label(zl, fontsize=10, color=DARK_TEXT)
                self._colorbar.ax.tick_params(colors=DARK_SUBTITLE)
            except Exception:
                self._colorbar = None

        self.ax.set_xlabel(xl, color=DARK_SUBTITLE, fontsize=10, labelpad=8)
        self.ax.set_ylabel(yl, color=DARK_SUBTITLE, fontsize=10, labelpad=8)
        self.ax.set_zlabel(zl, color=DARK_SUBTITLE, fontsize=10, labelpad=8)
        self.ax.tick_params(colors=DARK_SUBTITLE)

        family = self.model.FAMILY_NAMES[self.model.code_family]
        mode = self.model.MODE_NAMES[self.model.visualization_mode]
        self.ax.set_title(
            f"{mode}\n{family}",
            color=DARK_TEXT, fontweight="bold", fontsize=13,
        )

        for pane in (self.ax.xaxis.pane, self.ax.yaxis.pane, self.ax.zaxis.pane):
            pane.set_facecolor(DARK_BG)
            pane.set_edgecolor(DARK_EDGE)

        self.ax.grid(self.grid_var.get(), color=DARK_GRID, alpha=0.25)
        self.ax.set_box_aspect([1, 1, 0.8])

        pad = 0.1
        for arr, setter in [(X, self.ax.set_xlim), (Y, self.ax.set_ylim), (Z, self.ax.set_zlim)]:
            lo, hi = np.min(arr), np.max(arr)
            p = (hi - lo) * pad
            setter([lo - p, hi + p])

        self.ax.view_init(elev=stored_elev, azim=stored_azim)
        self._needs_redraw = False

    # -- animation ----------------------------------------------------------

    def _animate(self):
        if self._needs_redraw:
            self._draw_surface()

        if self.rotate_var.get():
            self.azimuth += self.speed_var.get()
            self.ax.view_init(elev=self.elevation, azim=self.azimuth)

        self.canvas.draw_idle()
        self.root.after(ANIMATION_INTERVAL, self._animate)

    # -- public API ---------------------------------------------------------

    def run(self):
        self.root.mainloop()

    def save_screenshot(self, path=None):
        if path is None:
            plots_dir = os.path.join(os.path.dirname(__file__), "..", "..", "Plots")
            os.makedirs(plots_dir, exist_ok=True)
            path = os.path.join(plots_dir, "threshold_landscape_3d.png")
        self.fig.savefig(path, dpi=150, facecolor=DARK_BG, edgecolor="none")


# =========================================================================
# Entry point
# =========================================================================

def main():
    """Entry point for the 3D threshold landscape visualizer."""
    print("Starting 3D Quantum LDPC Threshold Landscape")
    print("Drag to rotate | Scroll to zoom | Radio buttons to switch")
    model = QuantumLDPCThresholdModel()
    gui = ThresholdLandscape3DGUI(model)
    gui.run()


if __name__ == "__main__":
    main()
