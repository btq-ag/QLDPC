"""
Generate all static plots for the QLDPC repository.

Runs each simulation module's main() function to regenerate plots
in the Plots/ directory. All plots use a consistent dark theme.

Usage:
    python generate_all_plots.py
"""

import os
import sys
import matplotlib.pyplot as plt


def set_dark_theme():
    """Configure matplotlib for consistent dark theme plots."""
    plt.style.use("dark_background")
    plt.rcParams.update({
        "figure.facecolor": "#1e1e1e",
        "axes.facecolor": "#2b2b2b",
        "axes.edgecolor": "#555555",
        "axes.labelcolor": "#cccccc",
        "text.color": "#cccccc",
        "xtick.color": "#aaaaaa",
        "ytick.color": "#aaaaaa",
        "grid.color": "#444444",
        "legend.facecolor": "#2b2b2b",
        "legend.edgecolor": "#555555",
        "savefig.facecolor": "#1e1e1e",
        "savefig.edgecolor": "#1e1e1e",
    })


def main():
    """Generate all static plots."""
    set_dark_theme()

    plots_dir = os.path.join(os.path.dirname(__file__), "Plots")
    os.makedirs(plots_dir, exist_ok=True)

    print("=== Generating all QLDPC plots ===\n")

    modules = [
        ("Cavity cooperativity analysis", "qldpc.simulation.cavity_gates"),
        ("GHZ fidelity analysis", "qldpc.simulation.ghz"),
        ("Syndrome extraction", "qldpc.simulation.syndrome"),
        ("Quantum circuits", "qldpc.simulation.quantum_circuits"),
        ("LDPC process animations", "qldpc.simulation.animations"),
    ]

    for label, module_name in modules:
        print(f"  [{label}] ...", end=" ", flush=True)
        try:
            mod = __import__(module_name, fromlist=["main"])
            if hasattr(mod, "main"):
                mod.main()
                print("done")
            else:
                print("skipped (no main())")
        except Exception as e:
            print(f"FAILED: {e}")

    print(f"\nPlots saved to {plots_dir}")


if __name__ == "__main__":
    main()
