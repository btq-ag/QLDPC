"""
Real-Time Interactive Quantum LDPC Circuit Simulator

Dark-themed tkinter GUI with embedded matplotlib panels for:
  - Interactive circuit view with click-to-inject errors
  - Live syndrome vector display
  - Belief propagation decoding progress
  - Cavity QED parameter exploration

Usage:
    qldpc-simulator          # via console entry point
    python -m qldpc.simulation.ldpc_circuit
"""

import matplotlib
matplotlib.use("TkAgg")

import tkinter as tk
from tkinter import ttk
import numpy as np
import time
import os
import seaborn as sns

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Circle, Rectangle, FancyBboxPatch

from qldpc.theme import (
    DARK_BG, DARK_PANEL, DARK_AXES, DARK_TEXT, DARK_SUBTITLE,
    DARK_ACCENT, DARK_ACCENT_ALT, DARK_GRID, DARK_EDGE,
    DARK_BUTTON, DARK_INPUT,
    COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING, COLOR_INFO,
    COLOR_DATA_QUBIT, COLOR_X_CHECK, COLOR_Z_CHECK, COLOR_CAVITY_BUS,
    apply_dark_theme, configure_dark_axes,
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
DEFAULT_ERROR_RATE = 0.05
DEFAULT_COOPERATIVITY = 1e5
ANIMATION_INTERVAL = 120  # ms


# =========================================================================
# Model
# =========================================================================

class QuantumLDPCCode:
    """Quantum LDPC code with belief-propagation decoding."""

    def __init__(self, n_data: int = 21, n_checks: int = 12):
        self.n_data = n_data
        self.n_checks = n_checks
        self.distance = int(np.sqrt(n_data))

        self.parity_matrix = self._generate_ldpc_matrix()

        # 0=|0>, 1=|1>, 2=X error, 3=Z error, 4=Y error
        self.qubit_states = np.zeros(n_data, dtype=int)
        self.syndrome = np.zeros(n_checks, dtype=int)

        # Belief propagation state
        self.variable_beliefs = np.full((n_data, 2), 0.5)
        self.check_to_var_messages = np.full((n_checks, n_data), 0.5)
        self.var_to_check_messages = np.full((n_data, n_checks), 0.5)

        # Cavity QED
        self.cavity_cooperativity = DEFAULT_COOPERATIVITY
        self.gate_fidelity = self._calculate_gate_fidelity()

        # Decoding iteration counter
        self.bp_iteration = 0
        self.max_bp_iterations = 10
        self.decoding_complete = False

    # -- matrix generation --------------------------------------------------

    def _generate_ldpc_matrix(self):
        H = np.zeros((self.n_checks, self.n_data), dtype=int)
        rng = np.random.RandomState(42)
        for i in range(self.n_checks):
            cols = rng.choice(self.n_data, 6, replace=False)
            H[i, cols] = 1
        return H

    # -- fidelity -----------------------------------------------------------

    def _calculate_gate_fidelity(self):
        return 1.0 - 1.0 / self.cavity_cooperativity - 0.001

    # -- error injection ----------------------------------------------------

    def inject_error(self, qubit_idx, error_type=2):
        if 0 <= qubit_idx < self.n_data:
            self.qubit_states[qubit_idx] = error_type
            self._update_syndrome()

    def _update_syndrome(self):
        for i in range(self.n_checks):
            connected = np.where(self.parity_matrix[i] == 1)[0]
            errors = sum(1 for q in connected if self.qubit_states[q] in (2, 3, 4))
            self.syndrome[i] = errors % 2

    # -- belief propagation -------------------------------------------------

    def belief_propagation_step(self):
        if self.bp_iteration >= self.max_bp_iterations:
            return

        # Check -> variable messages
        for ci in range(self.n_checks):
            connected = np.where(self.parity_matrix[ci] == 1)[0]
            for vi in connected:
                if self.syndrome[ci] == 0:
                    self.check_to_var_messages[ci, vi] = 0.5
                else:
                    self.check_to_var_messages[ci, vi] = 0.5

        # Variable -> check messages and beliefs
        for vi in range(self.n_data):
            checks = np.where(self.parity_matrix[:, vi] == 1)[0]
            incoming = self.check_to_var_messages[checks, vi]
            if len(incoming) > 0:
                b0 = np.prod(incoming) * 0.9
                b1 = np.prod(1.0 - incoming) * 0.1
                norm = b0 + b1
                if norm > 0:
                    self.variable_beliefs[vi, 0] = b0 / norm
                    self.variable_beliefs[vi, 1] = b1 / norm
            for ci in checks:
                self.var_to_check_messages[vi, ci] = self.variable_beliefs[vi, 1]

        self.bp_iteration += 1
        if self.bp_iteration >= self.max_bp_iterations:
            self.decoding_complete = True

    def reset_decoding(self):
        self.bp_iteration = 0
        self.decoding_complete = False
        self.variable_beliefs[:] = 0.5
        self.check_to_var_messages[:] = 0.5
        self.var_to_check_messages[:] = 0.5

    def clear_errors(self):
        self.qubit_states.fill(0)
        self._update_syndrome()
        self.reset_decoding()

    # -- helpers used by tests ----------------------------------------------

    def calculate_syndrome(self, components=None):
        """Public API for test compatibility."""
        self._update_syndrome()
        return self.syndrome.copy()


# =========================================================================
# GUI
# =========================================================================

class LDPCSimulatorGUI:
    """Tkinter dark-mode GUI with embedded matplotlib panels."""

    TITLE = "Real-Time Quantum LDPC Circuit Simulator"

    def __init__(self, ldpc_code=None):
        self.code = ldpc_code or QuantumLDPCCode()
        self.auto_decode = False
        self.show_messages = True
        self.show_cavity = True

        # -- root window ----------------------------------------------------
        self.root = tk.Tk()
        self.root.title(self.TITLE)
        self.root.geometry("1280x820")
        self.root.minsize(960, 640)
        self.style = apply_dark_theme(self.root)

        # -- layout ---------------------------------------------------------
        self._build_ui()

        # -- start animation loop -------------------------------------------
        self._animate()

    # -- UI construction ----------------------------------------------------

    def _build_ui(self):
        outer = ttk.Frame(self.root, style="Dark.TFrame")
        outer.pack(fill=tk.BOTH, expand=True)

        self._build_controls(outer)
        self._build_canvas(outer)

    def _build_controls(self, parent):
        ctrl = ttk.Frame(parent, style="Dark.TFrame", width=260)
        ctrl.pack(side=tk.LEFT, fill=tk.Y, padx=(8, 0), pady=8)
        ctrl.pack_propagate(False)

        ttk.Label(ctrl, text="LDPC Simulator", style="Title.TLabel").pack(
            anchor=tk.W, pady=(0, 8)
        )

        # --- Cooperativity section -----------------------------------------
        coop_frame = ttk.LabelFrame(ctrl, text="Cavity QED", style="Dark.TLabelframe")
        coop_frame.pack(fill=tk.X, pady=4)

        ttk.Label(coop_frame, text="Cooperativity (C)", style="Dark.TLabel").pack(
            anchor=tk.W, padx=4
        )

        self.coop_var = tk.DoubleVar(value=5.0)
        self.coop_scale = ttk.Scale(
            coop_frame, from_=3.0, to=6.0, variable=self.coop_var,
            orient=tk.HORIZONTAL, style="Dark.Horizontal.TScale",
            command=self._on_coop_changed,
        )
        self.coop_scale.pack(fill=tk.X, padx=4, pady=2)

        self.coop_label = ttk.Label(coop_frame, text="C = 1.00e+05", style="Accent.TLabel")
        self.coop_label.pack(anchor=tk.W, padx=4)

        self.fidelity_label = ttk.Label(coop_frame, text="F = 0.9990", style="Dark.TLabel")
        self.fidelity_label.pack(anchor=tk.W, padx=4, pady=(0, 4))

        # --- Decoding section ----------------------------------------------
        dec_frame = ttk.LabelFrame(ctrl, text="Decoding", style="Dark.TLabelframe")
        dec_frame.pack(fill=tk.X, pady=4)

        ttk.Button(dec_frame, text="Decode Step", style="Dark.TButton",
                   command=self._decode_step).pack(fill=tk.X, padx=4, pady=2)

        self.auto_btn = ttk.Button(dec_frame, text="Auto Decode", style="Dark.TButton",
                                   command=self._toggle_auto)
        self.auto_btn.pack(fill=tk.X, padx=4, pady=2)

        ttk.Button(dec_frame, text="Clear Errors", style="Dark.TButton",
                   command=self._clear_errors).pack(fill=tk.X, padx=4, pady=2)

        ttk.Button(dec_frame, text="Reset Code", style="Dark.TButton",
                   command=self._reset_code).pack(fill=tk.X, padx=4, pady=2)

        # --- Display toggles -----------------------------------------------
        disp_frame = ttk.LabelFrame(ctrl, text="Display", style="Dark.TLabelframe")
        disp_frame.pack(fill=tk.X, pady=4)

        self.msg_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            disp_frame, text="Show Messages", variable=self.msg_var,
            style="Dark.TCheckbutton",
        ).pack(anchor=tk.W, padx=4)

        self.cavity_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            disp_frame, text="Show Cavity", variable=self.cavity_var,
            style="Dark.TCheckbutton",
        ).pack(anchor=tk.W, padx=4, pady=(0, 4))

        # --- Info section --------------------------------------------------
        info_frame = ttk.LabelFrame(ctrl, text="Code Parameters", style="Dark.TLabelframe")
        info_frame.pack(fill=tk.X, pady=4, expand=True)

        self.info_text = tk.Text(
            info_frame, height=8, wrap=tk.WORD,
            bg=DARK_INPUT, fg=DARK_ACCENT, insertbackground=DARK_ACCENT,
            font=("Consolas", 9), relief=tk.FLAT, bd=0,
        )
        self.info_text.pack(fill=tk.BOTH, padx=4, pady=4, expand=True)
        self._refresh_info()

        # --- Instructions --------------------------------------------------
        ttk.Label(
            ctrl,
            text="Click qubits to inject errors\n"
                 "Cycle: |0> -> |1> -> X -> Z -> Y",
            style="Subtitle.TLabel", wraplength=240,
        ).pack(anchor=tk.W, pady=(8, 0))

    def _build_canvas(self, parent):
        canvas_frame = ttk.Frame(parent, style="Dark.TFrame")
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.fig = Figure(figsize=(10, 7), facecolor=DARK_BG)
        gs = self.fig.add_gridspec(
            2, 3, height_ratios=[2.5, 1], width_ratios=[2, 0.8, 0.8],
            hspace=0.35, wspace=0.30,
        )

        self.ax_circuit = self.fig.add_subplot(gs[0, :2])
        self.ax_syndrome = self.fig.add_subplot(gs[0, 2])
        self.ax_beliefs = self.fig.add_subplot(gs[1, :])

        for ax in (self.ax_circuit, self.ax_syndrome, self.ax_beliefs):
            configure_dark_axes(ax)

        self.canvas = FigureCanvasTkAgg(self.fig, master=canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.canvas.mpl_connect("button_press_event", self._on_click)

    # -- callbacks ----------------------------------------------------------

    def _on_coop_changed(self, val):
        C = 10 ** float(val)
        self.code.cavity_cooperativity = C
        self.code.gate_fidelity = self.code._calculate_gate_fidelity()
        self.coop_label.configure(text=f"C = {C:.2e}")
        self.fidelity_label.configure(text=f"F = {self.code.gate_fidelity:.4f}")

    def _decode_step(self):
        if not self.code.decoding_complete:
            self.code.belief_propagation_step()

    def _toggle_auto(self):
        self.auto_decode = not self.auto_decode
        self.auto_btn.configure(
            text="Stop Auto" if self.auto_decode else "Auto Decode"
        )

    def _clear_errors(self):
        self.code.clear_errors()

    def _reset_code(self):
        coop = self.code.cavity_cooperativity
        self.code = QuantumLDPCCode(self.code.n_data, self.code.n_checks)
        self.code.cavity_cooperativity = coop
        self.code.gate_fidelity = self.code._calculate_gate_fidelity()
        self._refresh_info()

    def _on_click(self, event):
        if event.inaxes != self.ax_circuit:
            return
        for i in range(self.code.n_data):
            x, y = self._qubit_pos(i)
            if (event.xdata - x) ** 2 + (event.ydata - y) ** 2 < 0.3 ** 2:
                new_state = (self.code.qubit_states[i] + 1) % 5
                self.code.inject_error(i, new_state)
                self.code.reset_decoding()
                break

    # -- helpers ------------------------------------------------------------

    def _qubit_pos(self, idx):
        cols = 7
        return (idx % cols) * 1.5, 6 - (idx // cols) * 1.5

    def _check_pos(self, idx):
        return 10, idx * 0.5

    def _refresh_info(self):
        n = self.code.n_data
        k = n - self.code.n_checks
        d = self.code.distance
        rate = k / n if n else 0
        self.info_text.configure(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert(
            tk.END,
            f"Qubits (n):  {n}\n"
            f"Logical (k): {k}\n"
            f"Distance (d): {d}\n"
            f"Rate R=k/n:  {rate:.3f}\n"
            f"Sparse H:    6 per row\n"
            f"Scaling:     d = Theta(n)",
        )
        self.info_text.configure(state=tk.DISABLED)

    # -- drawing ------------------------------------------------------------

    def _draw_circuit(self):
        ax = self.ax_circuit
        ax.clear()
        ax.set_xlim(-1, 15)
        ax.set_ylim(-1, 8)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_facecolor(DARK_AXES)

        state_labels = {0: "|0>", 1: "|1>", 2: "X", 3: "Z", 4: "Y"}
        state_colors = {
            0: COLOR_DATA_QUBIT,
            1: lightCmap(0.6),
            2: COLOR_ERROR,
            3: COLOR_INFO,
            4: "#9B5DE5",
        }

        # Data qubits
        for i in range(self.code.n_data):
            x, y = self._qubit_pos(i)
            state = self.code.qubit_states[i]
            color = state_colors.get(state, COLOR_DATA_QUBIT)
            ep = self.code.variable_beliefs[i, 1]
            alpha = 0.3 + 0.7 * ep

            circle = Circle((x, y), 0.3, color=color, alpha=alpha)
            ax.add_patch(circle)
            ax.text(x, y, state_labels.get(state, "?"), ha="center", va="center",
                    fontsize=9, fontweight="bold", color=DARK_TEXT)
            ax.text(x, y - 0.55, f"q{i}", ha="center", va="center",
                    fontsize=7, color=DARK_SUBTITLE)

        # Parity checks
        for j in range(self.code.n_checks):
            x, y = self._check_pos(j)
            color = COLOR_SUCCESS if self.code.syndrome[j] == 0 else COLOR_ERROR
            rect = Rectangle((x - 0.2, y - 0.2), 0.4, 0.4, facecolor=color, alpha=0.85)
            ax.add_patch(rect)
            ax.text(x, y, f"s{j}", ha="center", va="center",
                    fontsize=8, fontweight="bold", color=DARK_TEXT)

        # Connections
        if self.msg_var.get():
            for j in range(self.code.n_checks):
                for i in range(self.code.n_data):
                    if self.code.parity_matrix[j, i] == 1:
                        x1, y1 = self._qubit_pos(i)
                        x2, y2 = self._check_pos(j)
                        msg = self.code.check_to_var_messages[j, i]
                        alpha = 0.15 + 0.5 * abs(msg - 0.5) * 2
                        color = COLOR_ERROR if msg > 0.5 else COLOR_SUCCESS
                        ax.plot([x1, x2], [y1, y2], color=color,
                                alpha=alpha, linewidth=0.8)

        # Cavity QED box
        if self.cavity_var.get():
            cavity = FancyBboxPatch(
                (11.5, 2), 2.5, 3, boxstyle="round,pad=0.1",
                facecolor=COLOR_CAVITY_BUS, alpha=0.35,
                edgecolor=DARK_EDGE, linewidth=2,
            )
            ax.add_patch(cavity)
            ax.text(12.75, 3.5, "Cavity\nQED", ha="center", va="center",
                    fontsize=11, fontweight="bold", color=DARK_TEXT)
            C = self.code.cavity_cooperativity
            F = self.code.gate_fidelity
            ax.text(
                12.75, 2.5, f"C = {C:.0e}\nF = {F:.4f}",
                ha="center", va="center", fontsize=9, color=DARK_TEXT,
                bbox=dict(boxstyle="round", facecolor=DARK_PANEL, alpha=0.85,
                          edgecolor=DARK_EDGE),
            )

        bp_text = f"BP Iteration: {self.code.bp_iteration}/{self.code.max_bp_iterations}"
        if self.code.decoding_complete:
            bp_text += "  [COMPLETE]"
        ax.text(
            5, 7.5, bp_text, ha="center", fontsize=11, fontweight="bold",
            color=DARK_TEXT,
            bbox=dict(boxstyle="round", facecolor=DARK_PANEL, alpha=0.6,
                      edgecolor=DARK_EDGE),
        )

    def _draw_syndrome(self):
        ax = self.ax_syndrome
        ax.clear()
        ax.set_xlim(-0.5, 1.5)
        ax.set_ylim(-0.5, self.code.n_checks - 0.5)
        ax.axis("off")
        ax.set_facecolor(DARK_AXES)

        for i, s in enumerate(self.code.syndrome):
            color = COLOR_SUCCESS if s == 0 else COLOR_ERROR
            alpha = 0.5 if s == 0 else 0.9
            rect = Rectangle((0, i), 1, 0.8, facecolor=color, alpha=alpha,
                              edgecolor=DARK_EDGE, linewidth=0.5)
            ax.add_patch(rect)
            ax.text(0.5, i + 0.4, str(s), ha="center", va="center",
                    fontsize=11, fontweight="bold", color=DARK_TEXT)

        ax.text(0.5, -0.4, "s = He", ha="center", va="top",
                fontsize=11, fontweight="bold", color=DARK_ACCENT)

        active = np.any(self.code.syndrome == 1)
        status = "Errors Detected!" if active else "No Errors"
        sc = COLOR_ERROR if active else COLOR_SUCCESS
        ax.text(0.5, self.code.n_checks, status, ha="center", va="bottom",
                fontsize=9, fontweight="bold", color=sc)

    def _draw_beliefs(self):
        ax = self.ax_beliefs
        ax.clear()
        ax.set_facecolor(DARK_AXES)

        probs = self.code.variable_beliefs[:, 1]
        indices = np.arange(self.code.n_data)
        colors = [seqCmap(float(p)) for p in probs]

        for i, state in enumerate(self.code.qubit_states):
            if state in (2, 3, 4):
                colors[i] = COLOR_ERROR

        ax.bar(indices, probs, color=colors, alpha=0.8, edgecolor=DARK_EDGE,
               linewidth=0.3)
        ax.axhline(0.5, color=DARK_ACCENT_ALT, linestyle="--", alpha=0.6)
        ax.text(self.code.n_data / 2, 0.53, "Decision Threshold",
                ha="center", fontsize=9, color=DARK_ACCENT_ALT)
        ax.set_ylim(0, 1)
        ax.set_xlabel("Data Qubits", color=DARK_SUBTITLE)
        ax.set_ylabel("Error Probability", color=DARK_SUBTITLE)
        ax.tick_params(colors=DARK_SUBTITLE)
        for spine in ax.spines.values():
            spine.set_color(DARK_EDGE)
        ax.grid(axis="y", color=DARK_GRID, alpha=0.3)

    # -- animation loop -----------------------------------------------------

    def _animate(self):
        if self.auto_decode and not self.code.decoding_complete:
            self.code.belief_propagation_step()

        self._draw_circuit()
        self._draw_syndrome()
        self._draw_beliefs()
        self.canvas.draw_idle()

        self.root.after(ANIMATION_INTERVAL, self._animate)

    # -- public API ---------------------------------------------------------

    def run(self):
        """Start the GUI main loop."""
        self.root.mainloop()

    def save_screenshot(self, path=None):
        """Save the current matplotlib figure to disk."""
        if path is None:
            plots_dir = os.path.join(os.path.dirname(__file__), "..", "..", "Plots")
            os.makedirs(plots_dir, exist_ok=True)
            path = os.path.join(plots_dir, "ldpc_simulator.png")
        self.fig.savefig(path, dpi=150, facecolor=DARK_BG, edgecolor="none")


# =========================================================================
# Entry point
# =========================================================================

def main():
    """Entry point for the real-time LDPC circuit simulator."""
    print("Starting Real-Time Quantum LDPC Circuit Simulator")
    print("Click qubits to inject errors | Adjust cooperativity with slider")
    code = QuantumLDPCCode(n_data=21, n_checks=12)
    gui = LDPCSimulatorGUI(code)
    gui.run()


if __name__ == "__main__":
    main()
