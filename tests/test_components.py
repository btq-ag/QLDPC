"""
Tests for qldpc.components module.

Covers ComponentType enum classification, Component3D serialization,
and view mode utilities.
"""

import pytest
from qldpc.components import (
    ComponentType, Component3D, ViewMode,
    get_categories_for_mode,
    CIRCUIT_MODE_CATEGORIES, SURFACE_MODE_CATEGORIES,
    LDPC_TANNER_CATEGORIES, LDPC_PHYSICAL_CATEGORIES,
)


# ---------- ViewMode ----------

class TestViewMode:
    def test_all_modes(self):
        modes = list(ViewMode)
        assert len(modes) == 4
        assert ViewMode.ISOMETRIC_3D in modes
        assert ViewMode.SURFACE_CODE_2D in modes
        assert ViewMode.LDPC_TANNER in modes
        assert ViewMode.LDPC_PHYSICAL in modes


# ---------- ComponentType ----------

class TestComponentType:
    def test_single_qubit_gates(self):
        singles = [ComponentType.X_GATE, ComponentType.Z_GATE, ComponentType.Y_GATE,
                   ComponentType.H_GATE, ComponentType.S_GATE, ComponentType.T_GATE]
        for gate in singles:
            assert not ComponentType.is_two_qubit_gate(gate)

    def test_two_qubit_gates(self):
        for gate in [ComponentType.CNOT_GATE, ComponentType.CZ_GATE, ComponentType.SWAP_GATE]:
            assert ComponentType.is_two_qubit_gate(gate)

    def test_surface_components(self):
        assert ComponentType.is_surface_component(ComponentType.SURFACE_DATA)
        assert ComponentType.is_surface_component(ComponentType.SURFACE_X_STABILIZER)
        assert ComponentType.is_surface_component(ComponentType.SURFACE_Z_STABILIZER)
        assert not ComponentType.is_surface_component(ComponentType.X_GATE)

    def test_ldpc_components(self):
        assert ComponentType.is_ldpc_component(ComponentType.LDPC_DATA_QUBIT)
        assert ComponentType.is_ldpc_component(ComponentType.LDPC_CAVITY_BUS)
        assert not ComponentType.is_ldpc_component(ComponentType.DATA_QUBIT)

    def test_error_components(self):
        assert ComponentType.is_error_component(ComponentType.SURFACE_X_ERROR)
        assert ComponentType.is_error_component(ComponentType.SURFACE_Z_ERROR)
        assert ComponentType.is_error_component(ComponentType.SURFACE_Y_ERROR)
        assert not ComponentType.is_error_component(ComponentType.X_GATE)

    def test_get_by_value(self):
        assert ComponentType.get_by_value_or_name("X") == ComponentType.X_GATE
        assert ComponentType.get_by_value_or_name("CNOT") == ComponentType.CNOT_GATE
        assert ComponentType.get_by_value_or_name("nonexistent") is None

    def test_get_by_name(self):
        assert ComponentType.get_by_value_or_name("X_GATE") == ComponentType.X_GATE


# ---------- Component3D ----------

class TestComponent3D:
    def test_defaults(self):
        comp = Component3D(
            component_type=ComponentType.X_GATE,
            position=(0, 0, 0),
        )
        assert comp.rotation == 0.0
        assert comp.connections == []
        assert comp.properties == {}

    def test_serialization_roundtrip(self):
        original = Component3D(
            component_type=ComponentType.H_GATE,
            position=(1, 2, 3),
            rotation=45.0,
            size=(1.0, 1.0, 1.0),
            color=(0.1, 0.2, 0.3),
            connections=[10, 20],
            properties={"label": "hadamard"},
        )
        data = original.to_dict()
        restored = Component3D.from_dict(data)

        assert restored is not None
        assert restored.component_type == original.component_type
        assert tuple(restored.position) == tuple(original.position)
        assert restored.rotation == original.rotation
        assert restored.properties == original.properties

    def test_from_dict_invalid_type(self):
        data = {"type": "INVALID_GATE", "position": [0, 0, 0]}
        assert Component3D.from_dict(data) is None

    def test_two_qubit_size_override(self):
        data = {
            "type": "CNOT",
            "position": [0, 0, 0],
            "size": [1.0, 1.0, 1.0],
        }
        comp = Component3D.from_dict(data)
        assert comp is not None
        assert comp.size == (1.0, 1.0, 2.0)

    def test_is_at_position(self):
        comp = Component3D(ComponentType.X_GATE, position=(5, 3, 0))
        assert comp.is_at_position(5, 3)
        assert not comp.is_at_position(6, 3)

    def test_is_two_qubit_property(self):
        single = Component3D(ComponentType.X_GATE, position=(0, 0, 0))
        double = Component3D(ComponentType.CNOT_GATE, position=(0, 0, 0))
        assert not single.is_two_qubit
        assert double.is_two_qubit

    def test_control_target_lanes(self):
        comp = Component3D(
            ComponentType.CNOT_GATE,
            position=(0, 2, 0),
            properties={"control": 2, "target": 4},
        )
        assert comp.control_lane == 2
        assert comp.target_lane == 4

    def test_control_target_defaults(self):
        comp = Component3D(ComponentType.CNOT_GATE, position=(0, 5, 0))
        assert comp.control_lane == 5
        assert comp.target_lane == 6

    def test_single_gate_no_lanes(self):
        comp = Component3D(ComponentType.H_GATE, position=(0, 0, 0))
        assert comp.control_lane is None
        assert comp.target_lane is None

    def test_color_override_from_dict(self):
        data = {"type": "X", "position": [0, 0, 0], "color": [0.1, 0.2, 0.3]}
        comp = Component3D.from_dict(data, color_override=(0.9, 0.8, 0.7))
        assert comp.color == (0.9, 0.8, 0.7)


# ---------- Categories ----------

class TestCategories:
    def test_circuit_mode_categories(self):
        cats = get_categories_for_mode(ViewMode.ISOMETRIC_3D)
        assert cats is CIRCUIT_MODE_CATEGORIES

    def test_surface_mode_categories(self):
        cats = get_categories_for_mode(ViewMode.SURFACE_CODE_2D)
        assert cats is SURFACE_MODE_CATEGORIES

    def test_tanner_mode_categories(self):
        cats = get_categories_for_mode(ViewMode.LDPC_TANNER)
        assert cats is LDPC_TANNER_CATEGORIES

    def test_physical_mode_categories(self):
        cats = get_categories_for_mode(ViewMode.LDPC_PHYSICAL)
        assert cats is LDPC_PHYSICAL_CATEGORIES
