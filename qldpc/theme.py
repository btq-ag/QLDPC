"""
Shared dark theme constants and utilities for all QLDPC GUIs.

Provides a centralized dark theme matching the TQNN visual style, with
ttk styling and matplotlib figure configuration.
"""

import tkinter as tk
from tkinter import ttk

# ---------------------------------------------------------------------------
# Dark theme color constants
# ---------------------------------------------------------------------------

DARK_BG = "#1a1a1a"
DARK_PANEL = "#0a0a0a"
DARK_AXES = "#111111"
DARK_TEXT = "#ffffff"
DARK_SUBTITLE = "#aaaaaa"
DARK_ACCENT = "#00ff88"
DARK_ACCENT_ALT = "#e94560"
DARK_GRID = "#2d2d2d"
DARK_EDGE = "#444444"
DARK_BUTTON = "#2d2d2d"
DARK_BUTTON_HOVER = "#3d3d3d"
DARK_INPUT = "#1e1e1e"

# Semantic accent colors (used across all GUIs)
COLOR_SUCCESS = "#00cc66"
COLOR_ERROR = "#ff4444"
COLOR_WARNING = "#ff9f43"
COLOR_INFO = "#74b9ff"

# Qubit / code component colors (matching LDPC_COLORS palette)
COLOR_DATA_QUBIT = "#2EC4B6"
COLOR_X_CHECK = "#FF6B6B"
COLOR_Z_CHECK = "#FFD93D"
COLOR_ANCILLA = "#9B5DE5"
COLOR_CAVITY_BUS = "#3D5A80"


def apply_dark_theme(root: tk.Tk) -> ttk.Style:
    """Apply the shared dark theme to a tkinter root window.

    Parameters
    ----------
    root : tk.Tk
        The root window to style.

    Returns
    -------
    ttk.Style
        The configured ttk style instance.
    """
    root.configure(bg=DARK_BG)

    style = ttk.Style(root)
    style.theme_use("clam")

    # Frame
    style.configure("Dark.TFrame", background=DARK_BG)
    style.configure("Panel.TFrame", background=DARK_PANEL)

    # Label
    style.configure(
        "Dark.TLabel",
        background=DARK_BG,
        foreground=DARK_TEXT,
        font=("Segoe UI", 10),
    )
    style.configure(
        "Title.TLabel",
        background=DARK_BG,
        foreground=DARK_TEXT,
        font=("Segoe UI", 14, "bold"),
    )
    style.configure(
        "Accent.TLabel",
        background=DARK_BG,
        foreground=DARK_ACCENT,
        font=("Segoe UI", 10, "bold"),
    )
    style.configure(
        "Subtitle.TLabel",
        background=DARK_BG,
        foreground=DARK_SUBTITLE,
        font=("Segoe UI", 9),
    )

    # LabelFrame
    style.configure(
        "Dark.TLabelframe",
        background=DARK_BG,
        foreground=DARK_TEXT,
    )
    style.configure(
        "Dark.TLabelframe.Label",
        background=DARK_BG,
        foreground=DARK_ACCENT,
        font=("Segoe UI", 10, "bold"),
    )

    # Button
    style.configure(
        "Dark.TButton",
        background=DARK_BUTTON,
        foreground=DARK_TEXT,
        borderwidth=0,
        font=("Segoe UI", 9),
        padding=(8, 4),
    )
    style.map(
        "Dark.TButton",
        background=[("active", DARK_BUTTON_HOVER), ("disabled", DARK_BG)],
        foreground=[("disabled", DARK_EDGE)],
    )
    style.configure(
        "Accent.TButton",
        background=DARK_ACCENT,
        foreground=DARK_BG,
        borderwidth=0,
        font=("Segoe UI", 9, "bold"),
        padding=(8, 4),
    )
    style.map(
        "Accent.TButton",
        background=[("active", "#00cc70")],
    )

    # Checkbutton
    style.configure(
        "Dark.TCheckbutton",
        background=DARK_BG,
        foreground=DARK_TEXT,
        font=("Segoe UI", 9),
    )
    style.map(
        "Dark.TCheckbutton",
        background=[("active", DARK_BG)],
    )

    # Radiobutton
    style.configure(
        "Dark.TRadiobutton",
        background=DARK_BG,
        foreground=DARK_TEXT,
        font=("Segoe UI", 9),
    )
    style.map(
        "Dark.TRadiobutton",
        background=[("active", DARK_BG)],
    )

    # Scale (slider)
    style.configure(
        "Dark.Horizontal.TScale",
        background=DARK_BG,
        troughcolor=DARK_PANEL,
    )

    # Separator
    style.configure("Dark.TSeparator", background=DARK_EDGE)

    return style


def configure_dark_axes(ax, title: str = ""):
    """Apply dark theme to a matplotlib axes.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes to configure.
    title : str, optional
        Optional title to set.
    """
    ax.set_facecolor(DARK_AXES)
    ax.tick_params(colors=DARK_TEXT, which="both")
    ax.xaxis.label.set_color(DARK_TEXT)
    ax.yaxis.label.set_color(DARK_TEXT)
    for spine in ax.spines.values():
        spine.set_color(DARK_EDGE)
    if title:
        ax.set_title(title, color=DARK_TEXT, fontweight="bold")


def configure_dark_3d_axes(ax, title: str = ""):
    """Apply dark theme to a 3D matplotlib axes.

    Parameters
    ----------
    ax : mpl_toolkits.mplot3d.axes3d.Axes3D
        The 3D axes to configure.
    title : str, optional
        Optional title to set.
    """
    ax.set_facecolor(DARK_AXES)
    ax.tick_params(colors=DARK_TEXT, which="both")
    ax.xaxis.label.set_color(DARK_TEXT)
    ax.yaxis.label.set_color(DARK_TEXT)
    ax.zaxis.label.set_color(DARK_TEXT)
    ax.xaxis.pane.set_facecolor(DARK_BG)
    ax.yaxis.pane.set_facecolor(DARK_BG)
    ax.zaxis.pane.set_facecolor(DARK_BG)
    ax.xaxis.pane.set_edgecolor(DARK_EDGE)
    ax.yaxis.pane.set_edgecolor(DARK_EDGE)
    ax.zaxis.pane.set_edgecolor(DARK_EDGE)
    ax.grid(color=DARK_GRID, alpha=0.3)
    if title:
        ax.set_title(title, color=DARK_TEXT, fontweight="bold")
