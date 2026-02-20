"""
Tests for qldpc.config module.

Covers configuration defaults, color validity, and component color mappings.
"""

import re
import pytest
from qldpc.config import (
    Config, GridConfig, UIConfig, SimulationConfig,
    ColorPalette, LDPC_COLORS, COMPONENT_COLORS, DEFAULT_CONFIG,
)
from qldpc.components import ComponentType


HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


class TestConfigDefaults:
    def test_default_config_exists(self):
        assert isinstance(DEFAULT_CONFIG, Config)

    def test_grid_defaults(self):
        g = GridConfig()
        assert g.min_coord == -10
        assert g.max_coord == 10
        assert g.default_scale == 30.0

    def test_ui_defaults(self):
        u = UIConfig()
        assert u.click_tolerance == 50

    def test_simulation_defaults(self):
        s = SimulationConfig()
        assert s.bp_max_iterations == 10
        assert s.default_shots == 1024


class TestColorPalette:
    def test_palette_hex_validity(self):
        palette = ColorPalette()
        for field_name in vars(palette):
            value = getattr(palette, field_name)
            if isinstance(value, str) and value.startswith("#"):
                assert HEX_RE.match(value), f"Invalid hex color: {field_name}={value}"


class TestLDPCColors:
    def test_all_hex_valid(self):
        for key, value in LDPC_COLORS.items():
            assert HEX_RE.match(value), f"Invalid hex in LDPC_COLORS[{key}]={value}"

    def test_required_keys_present(self):
        required = ["data_qubit", "x_check", "z_check", "ancilla", "edge", "cavity_bus"]
        for key in required:
            assert key in LDPC_COLORS, f"Missing LDPC_COLORS key: {key}"


class TestComponentColors:
    def test_rgb_range(self):
        for name, (r, g, b) in COMPONENT_COLORS.items():
            assert 0.0 <= r <= 1.0, f"{name} red out of range: {r}"
            assert 0.0 <= g <= 1.0, f"{name} green out of range: {g}"
            assert 0.0 <= b <= 1.0, f"{name} blue out of range: {b}"

    def test_all_component_types_have_color(self):
        """Every ComponentType should have a corresponding color entry."""
        for ct in ComponentType:
            assert ct.name in COMPONENT_COLORS, f"Missing color for {ct.name}"

    def test_get_component_color_known(self):
        color = Config.get_component_color("X_GATE")
        assert len(color) == 3
        assert all(0.0 <= c <= 1.0 for c in color)

    def test_get_component_color_unknown(self):
        color = Config.get_component_color("NONEXISTENT")
        assert color == (0.5, 0.5, 0.5)
