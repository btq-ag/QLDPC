"""
Interactive 3D Quantum LDPC Tanner Graph Visualizer

Dark-themed tkinter GUI with embedded matplotlib 3D panels for:
  - Force-directed, layered, and spherical graph layouts
  - Syndrome propagation animation
  - Multiple code construction comparisons (surface, hypergraph, Tanner)
  - Auto-rotation with manual override

Usage:
    qldpc-tanner             # via console entry point
    python -m qldpc.tanner.graph_3d
"""

import matplotlib
matplotlib.use("TkAgg")

import tkinter as tk
from tkinter import ttk
import numpy as np
import random
import os
import networkx as nx
import seaborn as sns

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from qldpc.theme import (
    DARK_BG, DARK_PANEL, DARK_AXES, DARK_TEXT, DARK_SUBTITLE,
    DARK_ACCENT, DARK_ACCENT_ALT, DARK_GRID, DARK_EDGE,
    DARK_INPUT,
    COLOR_SUCCESS, COLOR_ERROR,
    COLOR_DATA_QUBIT, COLOR_X_CHECK, COLOR_Z_CHECK, COLOR_ANCILLA,
    apply_dark_theme, configure_dark_3d_axes,
)

# ---------------------------------------------------------------------------
# Colormaps
# ---------------------------------------------------------------------------
seqCmap = sns.color_palette("mako", as_cmap=True)
divCmap = sns.cubehelix_palette(start=0.5, rot=-0.5, as_cmap=True)

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_N_QUBITS = 25
DEFAULT_N_CHECKS = 15
DEFAULT_SYNDROME_SPREAD = 3
ANIMATION_INTERVAL = 100  # ms


# =========================================================================
# Model
# =========================================================================

class QuantumLDPCTannerGraph:
    """3D Tanner graph model for quantum LDPC codes."""

    CODE_NAMES = ["Surface-like Code", "Hypergraph Product", "Quantum Tanner (Expander)"]
    LAYOUT_NAMES = ["Force-Directed", "Layered (Bipartite)", "Spherical"]

    def __init__(self, n_qubits=DEFAULT_N_QUBITS, n_checks=DEFAULT_N_CHECKS):
        self.n_qubits = n_qubits
        self.n_checks = n_checks
        self.syndrome_spread = DEFAULT_SYNDROME_SPREAD
        self.graph_type = 0
        self.layout_style = 0

        self.graph = None
        self.qubit_positions = None
        self.check_positions = None
        self.active_syndrome = None
        self.syndrome_time = 0

        self.node_colors = None
        self.edge_colors = None
        self.node_sizes = None

        self.initialize_graph()

    def initialize_graph(self):
        self.graph = nx.Graph()
        qubit_nodes = [f"q_{i}" for i in range(self.n_qubits)]
        check_nodes = [f"c_{i}" for i in range(self.n_checks)]
        self.graph.add_nodes_from(qubit_nodes, node_type="qubit")
        self.graph.add_nodes_from(check_nodes, node_type="check")
        self._add_edges_by_type()
        self._generate_3d_layout()
        self._init_visual_properties()

    def _add_edges_by_type(self):
        qubits = [n for n in self.graph.nodes() if n.startswith("q_")]
        checks = [n for n in self.graph.nodes() if n.startswith("c_")]
        degrees = [4, 6, 8]
        degree = degrees[self.graph_type]
        for q in qubits:
            targets = random.sample(checks, min(degree, len(checks)))
            for c in targets:
                self.graph.add_edge(q, c)

    def _generate_3d_layout(self):
        if self.layout_style == 0:
            pos = nx.spring_layout(self.graph, k=6, iterations=150)
            self.qubit_positions = np.array([
                [pos[n][0] * 8, pos[n][1] * 8, random.uniform(-4, 4)]
                for n in self.graph.nodes() if n.startswith("q_")
            ])
            self.check_positions = np.array([
                [pos[n][0] * 8, pos[n][1] * 8, random.uniform(-4, 4)]
                for n in self.graph.nodes() if n.startswith("c_")
            ])
        elif self.layout_style == 1:
            angles_q = np.linspace(0, 2 * np.pi, self.n_qubits, endpoint=False)
            self.qubit_positions = np.array([
                [12 * np.cos(a), 12 * np.sin(a), -5.0] for a in angles_q
            ])
            angles_c = np.linspace(0, 2 * np.pi, self.n_checks, endpoint=False)
            self.check_positions = np.array([
                [8 * np.cos(a), 8 * np.sin(a), 5.0] for a in angles_c
            ])
        else:
            self.qubit_positions = self._sphere_layout(self.n_qubits, 12.0)
            self.check_positions = self._sphere_layout(self.n_checks, 8.0)

    @staticmethod
    def _sphere_layout(n, radius=1.0):
        golden = (1 + 5 ** 0.5) / 2
        pts = []
        for i in range(n):
            theta = 2 * np.pi * i / golden
            phi = np.arccos(1 - 2 * (i + 0.5) / n)
            pts.append([
                radius * np.sin(phi) * np.cos(theta),
                radius * np.sin(phi) * np.sin(theta),
                radius * np.cos(phi),
            ])
        return np.array(pts)

    def _init_visual_properties(self):
        self.node_colors = (
            [seqCmap(0.3)] * self.n_qubits + [divCmap(0.7)] * self.n_checks
        )
        self.node_sizes = [100] * self.n_qubits + [150] * self.n_checks

    def trigger_syndrome(self, node_index=None):
        if node_index is None:
            node_index = random.randint(0, self.n_qubits - 1)
        self.active_syndrome = node_index
        self.syndrome_time = 0

    def update_syndrome_visualization(self):
        if self.active_syndrome is None:
            return
        self._init_visual_properties()
        origin = f"q_{self.active_syndrome}"
        for node in self.graph.nodes():
            try:
                d = nx.shortest_path_length(self.graph, origin, node)
            except nx.NetworkXNoPath:
                continue
            if d <= self.syndrome_spread:
                intensity = 1.0 - d / self.syndrome_spread
                if node.startswith("q_"):
                    idx = int(node.split("_")[1])
                    self.node_colors[idx] = seqCmap(0.8 * intensity + 0.2)
                    self.node_sizes[idx] = int(120 + 80 * intensity)
                else:
                    idx = int(node.split("_")[1]) + self.n_qubits
                    self.node_colors[idx] = divCmap(0.8 * intensity + 0.2)
                    self.node_sizes[idx] = int(170 + 80 * intensity)
        self.syndrome_time += 1
        if self.syndrome_time > 20:
            self.active_syndrome = None

    def get_edge_positions(self):
        edges = []
        for n1, n2 in self.graph.edges():
            p1 = (self.qubit_positions[int(n1.split("_")[1])]
                   if n1.startswith("q_")
                   else self.check_positions[int(n1.split("_")[1])])
            p2 = (self.qubit_positions[int(n2.split("_")[1])]
                   if n2.startswith("q_")
                   else self.check_positions[int(n2.split("_")[1])])
            edges.append((p1, p2))
        return edges


# =========================================================================
# GUI
# =========================================================================

class TannerGraph3DGUI:
    """Tkinter dark-mode GUI with embedded 3D matplotlib Tanner graph."""

    TITLE = "3D Quantum LDPC Tanner Graph Visualizer"

    def __init__(self, model=None):
        self.model = model or QuantumLDPCTannerGraph()
        self.azimuth = 45.0
        self.elevation = 30.0
        self.auto_rotate = True
        self.show_edges = True
        self.show_labels = False

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

        ttk.Label(ctrl, text="Tanner Graph 3D", style="Title.TLabel").pack(
            anchor=tk.W, pady=(0, 8)
        )

        # --- Graph parameters ----------------------------------------------
        gp = ttk.LabelFrame(ctrl, text="Graph", style="Dark.TLabelframe")
        gp.pack(fill=tk.X, pady=4)

        ttk.Label(gp, text="Qubits", style="Dark.TLabel").pack(anchor=tk.W, padx=4)
        self.qubits_var = tk.IntVar(value=DEFAULT_N_QUBITS)
        ttk.Scale(
            gp, from_=10, to=50, variable=self.qubits_var,
            orient=tk.HORIZONTAL, style="Dark.Horizontal.TScale",
            command=lambda v: self._rebuild_graph(),
        ).pack(fill=tk.X, padx=4, pady=2)

        ttk.Label(gp, text="Checks", style="Dark.TLabel").pack(anchor=tk.W, padx=4)
        self.checks_var = tk.IntVar(value=DEFAULT_N_CHECKS)
        ttk.Scale(
            gp, from_=5, to=30, variable=self.checks_var,
            orient=tk.HORIZONTAL, style="Dark.Horizontal.TScale",
            command=lambda v: self._rebuild_graph(),
        ).pack(fill=tk.X, padx=4, pady=2)

        ttk.Label(gp, text="Syndrome Spread", style="Dark.TLabel").pack(anchor=tk.W, padx=4)
        self.spread_var = tk.IntVar(value=DEFAULT_SYNDROME_SPREAD)
        ttk.Scale(
            gp, from_=1, to=5, variable=self.spread_var,
            orient=tk.HORIZONTAL, style="Dark.Horizontal.TScale",
            command=lambda v: setattr(self.model, "syndrome_spread", int(float(v))),
        ).pack(fill=tk.X, padx=4, pady=(2, 4))

        # --- Code type & layout --------------------------------------------
        cl = ttk.LabelFrame(ctrl, text="Construction", style="Dark.TLabelframe")
        cl.pack(fill=tk.X, pady=4)

        ttk.Button(cl, text="Cycle Code Type", style="Dark.TButton",
                   command=self._cycle_code).pack(fill=tk.X, padx=4, pady=2)
        self.code_label = ttk.Label(cl, text=self.model.CODE_NAMES[0], style="Accent.TLabel")
        self.code_label.pack(anchor=tk.W, padx=4)

        ttk.Button(cl, text="Cycle Layout", style="Dark.TButton",
                   command=self._cycle_layout).pack(fill=tk.X, padx=4, pady=2)
        self.layout_label = ttk.Label(cl, text=self.model.LAYOUT_NAMES[0], style="Dark.TLabel")
        self.layout_label.pack(anchor=tk.W, padx=4, pady=(0, 4))

        # --- Actions -------------------------------------------------------
        act = ttk.LabelFrame(ctrl, text="Actions", style="Dark.TLabelframe")
        act.pack(fill=tk.X, pady=4)

        ttk.Button(act, text="Trigger Syndrome", style="Accent.TButton",
                   command=lambda: self.model.trigger_syndrome()).pack(fill=tk.X, padx=4, pady=2)

        # --- Display -------------------------------------------------------
        disp = ttk.LabelFrame(ctrl, text="Display", style="Dark.TLabelframe")
        disp.pack(fill=tk.X, pady=4)

        self.edges_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(disp, text="Show Edges", variable=self.edges_var,
                        style="Dark.TCheckbutton").pack(anchor=tk.W, padx=4)

        self.labels_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(disp, text="Show Labels", variable=self.labels_var,
                        style="Dark.TCheckbutton").pack(anchor=tk.W, padx=4)

        self.rotate_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(disp, text="Auto Rotate", variable=self.rotate_var,
                        style="Dark.TCheckbutton").pack(anchor=tk.W, padx=4, pady=(0, 4))

        # --- Stats ---------------------------------------------------------
        stats = ttk.LabelFrame(ctrl, text="Statistics", style="Dark.TLabelframe")
        stats.pack(fill=tk.X, pady=4, expand=True)

        self.stats_text = tk.Text(
            stats, height=6, wrap=tk.WORD,
            bg=DARK_INPUT, fg=DARK_ACCENT, insertbackground=DARK_ACCENT,
            font=("Consolas", 9), relief=tk.FLAT, bd=0,
        )
        self.stats_text.pack(fill=tk.BOTH, padx=4, pady=4, expand=True)
        self._refresh_stats()

        # --- Instructions --------------------------------------------------
        ttk.Label(
            ctrl,
            text="Click Trigger Syndrome to see\nerror propagation on graph",
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

        # Mouse interaction
        self.canvas.mpl_connect("button_press_event", self._on_click)
        self.canvas.mpl_connect("scroll_event", self._on_scroll)

    # -- callbacks ----------------------------------------------------------

    def _rebuild_graph(self):
        self.model.n_qubits = int(self.qubits_var.get())
        self.model.n_checks = int(self.checks_var.get())
        self.model.initialize_graph()
        self._refresh_stats()

    def _cycle_code(self):
        self.model.graph_type = (self.model.graph_type + 1) % 3
        self.model.initialize_graph()
        self.code_label.configure(text=self.model.CODE_NAMES[self.model.graph_type])
        self._refresh_stats()

    def _cycle_layout(self):
        self.model.layout_style = (self.model.layout_style + 1) % 3
        self.model.initialize_graph()
        self.layout_label.configure(text=self.model.LAYOUT_NAMES[self.model.layout_style])

    def _on_click(self, event):
        if event.inaxes == self.ax and event.button == 1:
            self.model.trigger_syndrome()

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

    def _refresh_stats(self):
        ne = self.model.graph.number_of_edges()
        nn = self.model.graph.number_of_nodes()
        avg = 2 * ne / nn if nn else 0
        self.stats_text.configure(state=tk.NORMAL)
        self.stats_text.delete("1.0", tk.END)
        self.stats_text.insert(
            tk.END,
            f"Qubits:    {self.model.n_qubits}\n"
            f"Checks:    {self.model.n_checks}\n"
            f"Edges:     {ne}\n"
            f"Avg Deg:   {avg:.1f}\n"
            f"Code:      {self.model.CODE_NAMES[self.model.graph_type]}\n"
            f"Layout:    {self.model.LAYOUT_NAMES[self.model.layout_style]}",
        )
        self.stats_text.configure(state=tk.DISABLED)

    # -- drawing ------------------------------------------------------------

    def _draw(self):
        ax = self.ax
        ax.clear()
        ax.set_facecolor(DARK_AXES)

        self.model.update_syndrome_visualization()

        # Edges
        if self.edges_var.get():
            for p1, p2 in self.model.get_edge_positions():
                ax.plot3D(*zip(p1, p2), color=DARK_EDGE, alpha=0.35, linewidth=0.7)

        # Qubit nodes
        qp = self.model.qubit_positions
        if len(qp) > 0:
            ax.scatter(
                qp[:, 0], qp[:, 1], qp[:, 2],
                c=self.model.node_colors[: self.model.n_qubits],
                s=self.model.node_sizes[: self.model.n_qubits],
                alpha=0.85, marker="o", edgecolors=DARK_EDGE, linewidth=0.5,
                label="Data Qubits",
            )

        # Check nodes
        cp = self.model.check_positions
        if len(cp) > 0:
            ax.scatter(
                cp[:, 0], cp[:, 1], cp[:, 2],
                c=self.model.node_colors[self.model.n_qubits:],
                s=self.model.node_sizes[self.model.n_qubits:],
                alpha=0.85, marker="s", edgecolors=DARK_EDGE, linewidth=0.5,
                label="Check Nodes",
            )

        # Labels
        if self.labels_var.get():
            for i, p in enumerate(qp):
                ax.text(p[0], p[1], p[2], f"q{i}", fontsize=7, color=DARK_SUBTITLE)
            for i, p in enumerate(cp):
                ax.text(p[0], p[1], p[2], f"c{i}", fontsize=7, color=DARK_SUBTITLE)

        code_name = self.model.CODE_NAMES[self.model.graph_type]
        layout_name = self.model.LAYOUT_NAMES[self.model.layout_style]
        ax.set_title(
            f"3D Tanner Graph: {code_name}\nLayout: {layout_name}",
            color=DARK_TEXT, fontweight="bold", fontsize=13,
        )
        ax.set_xlabel("X", color=DARK_SUBTITLE)
        ax.set_ylabel("Y", color=DARK_SUBTITLE)
        ax.set_zlabel("Z", color=DARK_SUBTITLE)
        ax.tick_params(colors=DARK_SUBTITLE)
        for pane in (ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane):
            pane.set_facecolor(DARK_BG)
            pane.set_edgecolor(DARK_EDGE)
        ax.grid(color=DARK_GRID, alpha=0.25)
        ax.legend(loc="upper left", fontsize=8,
                  facecolor=DARK_PANEL, edgecolor=DARK_EDGE, labelcolor=DARK_TEXT)

        rng = 20.0
        ax.set_xlim([-rng, rng])
        ax.set_ylim([-rng, rng])
        ax.set_zlim([-rng, rng])

    # -- animation ----------------------------------------------------------

    def _animate(self):
        if self.rotate_var.get():
            self.azimuth += 0.5
            self.ax.view_init(elev=self.elevation, azim=self.azimuth)

        self._draw()
        self.canvas.draw_idle()
        self.root.after(ANIMATION_INTERVAL, self._animate)

    # -- public API ---------------------------------------------------------

    def run(self):
        self.root.mainloop()

    def save_screenshot(self, path=None):
        if path is None:
            plots_dir = os.path.join(os.path.dirname(__file__), "..", "..", "Plots")
            os.makedirs(plots_dir, exist_ok=True)
            path = os.path.join(plots_dir, "tanner_graph_3d.png")
        self.fig.savefig(path, dpi=150, facecolor=DARK_BG, edgecolor="none")


# =========================================================================
# Entry point
# =========================================================================

def main():
    """Entry point for the 3D Tanner graph visualizer."""
    print("Starting 3D Quantum LDPC Tanner Graph Visualizer")
    print("Click to trigger syndrome | Scroll to zoom | Drag to rotate")
    model = QuantumLDPCTannerGraph()
    gui = TannerGraph3DGUI(model)
    gui.run()


if __name__ == "__main__":
    main()
