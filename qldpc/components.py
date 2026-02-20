"""
Quantum circuit component definitions.

This module defines the component types (gates, qubits, stabilizers) and
the Component3D data class that represents placed components in the circuit.
Author: Jeffrey Morais"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Any, Optional


class ViewMode(Enum):
    """Enumeration of available view modes."""
    ISOMETRIC_3D = "isometric"        # Standard isometric view for circuit diagrams
    SURFACE_CODE_2D = "surface_2d"    # Top-down 2D view for surface code lattice
    LDPC_TANNER = "ldpc_tanner"       # Tanner graph view (3-layer: X-checks, qubits, Z-checks)
    LDPC_PHYSICAL = "ldpc_physical"   # Physical layout (linear arrays with cavity bus)


class ComponentType(Enum):
    """Enumeration of available quantum circuit components."""
    
    # Single qubit gates
    X_GATE = "X"
    Z_GATE = "Z"
    Y_GATE = "Y"
    H_GATE = "H"
    S_GATE = "S"
    T_GATE = "T"
    
    # Two qubit gates
    CNOT_GATE = "CNOT"
    CZ_GATE = "CZ"
    SWAP_GATE = "SWAP"
    
    # LDPC specific components
    PARITY_CHECK = "Parity Check"
    DATA_QUBIT = "Data Qubit"
    ANCILLA_QUBIT = "Ancilla"
    
    # Measurement and reset
    MEASURE = "Measure"
    RESET = "Reset"
    
    # Surface code specific components (2D lattice mode)
    SURFACE_DATA = "Surface Data"           # Data qubit on edge (surface code)
    SURFACE_X_STABILIZER = "X Stabilizer"   # X-type stabilizer (plaquette/face)
    SURFACE_Z_STABILIZER = "Z Stabilizer"   # Z-type stabilizer (vertex/star)
    SURFACE_BOUNDARY = "Boundary"           # Boundary (rough or smooth)
    SURFACE_X_ERROR = "X Error"             # X (bit-flip) error on data qubit
    SURFACE_Z_ERROR = "Z Error"             # Z (phase-flip) error on data qubit
    SURFACE_Y_ERROR = "Y Error"             # Y (combined) error on data qubit
    
    # LDPC specific components (Tanner graph and physical layout modes)
    LDPC_DATA_QUBIT = "LDPC Data"           # Data qubit in LDPC lattice
    LDPC_X_CHECK = "LDPC X-Check"           # X-type check node (coral/salmon)
    LDPC_Z_CHECK = "LDPC Z-Check"           # Z-type check node (gold/amber)
    LDPC_ANCILLA = "LDPC Ancilla"           # Ancilla qubit for syndrome extraction
    LDPC_X_ANCILLA = "LDPC X-Ancilla"       # X-ancilla (tri-layer physical layout)
    LDPC_Z_ANCILLA = "LDPC Z-Ancilla"       # Z-ancilla (tri-layer physical layout)
    LDPC_EDGE = "LDPC Edge"                 # Non-local edge/connection
    LDPC_CAVITY_BUS = "Cavity Bus"          # Cavity bus for non-local connectivity
    
    # Circuit mode error components (for QEC demonstrations)
    CIRCUIT_X_ERROR = "X Err"               # X bit-flip error marker
    CIRCUIT_Z_ERROR = "Z Err"               # Z phase-flip error marker
    CIRCUIT_Y_ERROR = "Y Err"               # Y combined error marker
    CIRCUIT_CORRECTION = "Correct"          # Error correction operation marker
    
    @classmethod
    def is_two_qubit_gate(cls, comp_type: 'ComponentType') -> bool:
        """Check if a component type is a two-qubit gate."""
        return comp_type in [cls.CNOT_GATE, cls.CZ_GATE, cls.SWAP_GATE]
    
    @classmethod
    def is_surface_component(cls, comp_type: 'ComponentType') -> bool:
        """Check if a component type is a surface code component."""
        return comp_type in [
            cls.SURFACE_DATA, cls.SURFACE_X_STABILIZER, cls.SURFACE_Z_STABILIZER,
            cls.SURFACE_BOUNDARY, cls.SURFACE_X_ERROR, cls.SURFACE_Z_ERROR, cls.SURFACE_Y_ERROR
        ]
    
    @classmethod
    def is_ldpc_component(cls, comp_type: 'ComponentType') -> bool:
        """Check if a component type is an LDPC-specific component."""
        return comp_type in [
            cls.LDPC_DATA_QUBIT, cls.LDPC_X_CHECK, cls.LDPC_Z_CHECK,
            cls.LDPC_ANCILLA, cls.LDPC_X_ANCILLA, cls.LDPC_Z_ANCILLA,
            cls.LDPC_EDGE, cls.LDPC_CAVITY_BUS
        ]
    
    @classmethod
    def is_error_component(cls, comp_type: 'ComponentType') -> bool:
        """Check if a component type is an error marker."""
        return comp_type in [cls.SURFACE_X_ERROR, cls.SURFACE_Z_ERROR, cls.SURFACE_Y_ERROR]
    
    @classmethod
    def get_by_value_or_name(cls, identifier: str) -> Optional['ComponentType']:
        """Find a ComponentType by either its value or name."""
        for ct in cls:
            if ct.value == identifier or ct.name == identifier:
                return ct
        return None


@dataclass
class Component3D:
    """
    Represents a 3D quantum circuit component with position and properties.
    
    Attributes:
        component_type: Type of quantum component
        position: (x, y, z) grid coordinates
        rotation: Rotation angle in degrees
        size: (width, height, depth) in grid units
        color: RGB color tuple for rendering
        connections: List of connected component IDs
        properties: Component-specific properties dictionary
    """
    
    component_type: ComponentType
    position: Tuple[int, int, int]
    rotation: float = 0.0
    size: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    color: Tuple[float, float, float] = (0.5, 0.5, 0.8)
    connections: List[int] = None
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.connections is None:
            self.connections = []
        if self.properties is None:
            self.properties = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize the component to a dictionary."""
        return {
            'type': self.component_type.value,
            'position': list(self.position),
            'rotation': self.rotation,
            'size': list(self.size),
            'color': list(self.color),
            'connections': self.connections,
            'properties': self.properties
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], color_override: Optional[Tuple[float, float, float]] = None) -> Optional['Component3D']:
        """
        Deserialize a component from a dictionary.
        
        Args:
            data: Dictionary with component data
            color_override: Optional color to use instead of saved color
            
        Returns:
            Component3D instance or None if component type is invalid
        """
        type_str = data.get('type', '')
        comp_type = ComponentType.get_by_value_or_name(type_str)
        
        if comp_type is None:
            return None
        
        # Determine correct size based on gate type
        if ComponentType.is_two_qubit_gate(comp_type):
            size = (1.0, 1.0, 2.0)
        else:
            size = tuple(data.get('size', (1.0, 1.0, 1.0)))
        
        return cls(
            component_type=comp_type,
            position=tuple(data['position']),
            rotation=data.get('rotation', 0.0),
            size=size,
            color=color_override if color_override else tuple(data.get('color', (0.5, 0.5, 0.5))),
            connections=data.get('connections', []),
            properties=data.get('properties', {})
        )
    
    def is_at_position(self, x: int, y: int, tolerance: float = 0.5) -> bool:
        """Check if this component is at or near the given position."""
        return (abs(self.position[0] - x) < tolerance and 
                abs(self.position[1] - y) < tolerance)
    
    @property
    def is_two_qubit(self) -> bool:
        """Check if this is a two-qubit gate."""
        return ComponentType.is_two_qubit_gate(self.component_type)
    
    @property
    def control_lane(self) -> Optional[int]:
        """Get the control qubit lane for two-qubit gates."""
        if self.is_two_qubit:
            return self.properties.get('control', self.position[1])
        return None
    
    @property
    def target_lane(self) -> Optional[int]:
        """Get the target qubit lane for two-qubit gates."""
        if self.is_two_qubit:
            return self.properties.get('target', self.position[1] + 1)
        return None


# Component categories for toolbox organization
CIRCUIT_MODE_CATEGORIES = {
    "Single": [
        ComponentType.X_GATE, ComponentType.Z_GATE, ComponentType.Y_GATE,
        ComponentType.H_GATE, ComponentType.S_GATE, ComponentType.T_GATE
    ],
    "Double": [
        ComponentType.CNOT_GATE, ComponentType.CZ_GATE, ComponentType.SWAP_GATE
    ],
    "Qubits": [
        ComponentType.DATA_QUBIT, ComponentType.ANCILLA_QUBIT
    ],
    "Measure": [
        ComponentType.MEASURE, ComponentType.RESET
    ]
}

SURFACE_MODE_CATEGORIES = {
    "Stabilizers": [
        ComponentType.SURFACE_X_STABILIZER,
        ComponentType.SURFACE_Z_STABILIZER,
    ],
    "Lattice": [
        ComponentType.SURFACE_DATA,
        ComponentType.SURFACE_BOUNDARY,
    ],
    "Defects": [
        ComponentType.SURFACE_X_ERROR,
        ComponentType.SURFACE_Z_ERROR,
        ComponentType.SURFACE_Y_ERROR,
    ]
}

LDPC_TANNER_CATEGORIES = {
    "Checks": [
        ComponentType.LDPC_X_CHECK,
        ComponentType.LDPC_Z_CHECK,
    ],
    "Qubits": [
        ComponentType.LDPC_DATA_QUBIT,
        ComponentType.LDPC_ANCILLA,
    ],
    "Connect": [
        ComponentType.LDPC_EDGE,
    ]
}

LDPC_PHYSICAL_CATEGORIES = {
    "Data": [
        ComponentType.LDPC_DATA_QUBIT,
    ],
    "Ancilla": [
        ComponentType.LDPC_X_ANCILLA,
        ComponentType.LDPC_Z_ANCILLA,
        ComponentType.LDPC_ANCILLA,
    ],
    "Bus": [
        ComponentType.LDPC_CAVITY_BUS,
    ]
}


def get_categories_for_mode(view_mode: ViewMode) -> Dict[str, List[ComponentType]]:
    """Get the component categories for the given view mode."""
    if view_mode == ViewMode.SURFACE_CODE_2D:
        return SURFACE_MODE_CATEGORIES
    elif view_mode == ViewMode.LDPC_TANNER:
        return LDPC_TANNER_CATEGORIES
    elif view_mode == ViewMode.LDPC_PHYSICAL:
        return LDPC_PHYSICAL_CATEGORIES
    else:
        return CIRCUIT_MODE_CATEGORIES
