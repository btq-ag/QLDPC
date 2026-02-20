"""
Quantum computation backend for the Circuit Builder.

This module handles quantum circuit construction, syndrome calculation,
error correction decoding, and quantum state simulation.
Author: Jeffrey Morais"""

import numpy as np
from typing import Dict, List, Optional, Any, TYPE_CHECKING

from .components import ComponentType, Component3D
from .config import DEFAULT_CONFIG

if TYPE_CHECKING:
    pass

# Quantum computing libraries
try:
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
    from qiskit.quantum_info import Statevector, Operator
    from qiskit_aer import AerSimulator
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False
    QuantumCircuit = None
    QuantumRegister = None
    ClassicalRegister = None
    print("Warning: Qiskit not available. Some quantum computations will be simulated.")


class QuantumLDPCProcessor:
    """
    Handles quantum LDPC computations for real-time circuit analysis.
    
    This class processes the built quantum circuits and performs:
    - Syndrome calculation
    - Error correction decoding
    - Quantum state evolution
    """
    
    def __init__(self, config=None):
        """Initialize the quantum processor."""
        self.config = config or DEFAULT_CONFIG
        self.circuit = None
        self.current_state = None
        self.syndrome_history: List[np.ndarray] = []
        self.error_corrections: List[Dict[str, Any]] = []
    
    def build_circuit_from_components(self, components: List[Component3D]) -> Optional[QuantumCircuit]:
        """
        Build a Qiskit quantum circuit from placed components.
        
        Uses a qubit registry built from DATA_QUBIT and ANCILLA_QUBIT components,
        then maps gates to qubits based on lane (Y-position) matching.
        
        Args:
            components: List of placed 3D components
            
        Returns:
            Constructed QuantumCircuit or None if build fails
        """
        if not QISKIT_AVAILABLE:
            return self._simulate_circuit_build(components)
        
        try:
            # Build qubit registry: map lane (Y-position) to qubit index
            qubit_components = [comp for comp in components 
                               if comp.component_type in [ComponentType.DATA_QUBIT, ComponentType.ANCILLA_QUBIT]]
            
            if not qubit_components:
                print("No qubit components found in circuit")
                return None
            
            # Create lane-to-qubit mapping (sorted by Y-position for consistent ordering)
            qubit_components_sorted = sorted(qubit_components, key=lambda c: c.position[1])
            lane_to_qubit: Dict[int, int] = {}
            for idx, comp in enumerate(qubit_components_sorted):
                lane = comp.position[1]
                if lane not in lane_to_qubit:
                    lane_to_qubit[lane] = idx
            
            num_qubits = len(lane_to_qubit)
            
            # Create circuit
            qreg = QuantumRegister(num_qubits, 'q')
            creg = ClassicalRegister(num_qubits, 'c')
            circuit = QuantumCircuit(qreg, creg)
            
            # Sort components by x-position for temporal ordering
            sorted_components = sorted(components, key=lambda c: c.position[0])
            
            for comp in sorted_components:
                lane = comp.position[1]
                # Check if this lane has a qubit (skip components on empty lanes)
                if lane not in lane_to_qubit:
                    # For two-qubit gates, check if control lane exists
                    if not comp.is_two_qubit:
                        continue
                
                self._add_component_to_circuit(circuit, comp, qreg, creg, lane_to_qubit)
            
            self.circuit = circuit
            return circuit
            
        except Exception as e:
            print(f"Error building circuit: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _add_component_to_circuit(self, circuit: QuantumCircuit, 
                                 component: Component3D,
                                 qreg: QuantumRegister, 
                                 creg: ClassicalRegister,
                                 lane_to_qubit: Dict[int, int]):
        """
        Add a single component to the quantum circuit.
        
        Args:
            circuit: The Qiskit QuantumCircuit to add to
            component: The 3D component to add
            qreg: Quantum register
            creg: Classical register
            lane_to_qubit: Mapping from Y-position (lane) to qubit index
        """
        comp_type = component.component_type
        lane = component.position[1]
        
        # Skip if lane doesn't have a qubit (except for two-qubit gates which use properties)
        if lane not in lane_to_qubit:
            if not component.is_two_qubit:
                return
        
        # Get qubit index from lane
        qubit_idx = lane_to_qubit.get(lane, -1)
        
        # Single-qubit gates
        gate_map = {
            ComponentType.X_GATE: lambda: circuit.x(qreg[qubit_idx]),
            ComponentType.Z_GATE: lambda: circuit.z(qreg[qubit_idx]),
            ComponentType.Y_GATE: lambda: circuit.y(qreg[qubit_idx]),
            ComponentType.H_GATE: lambda: circuit.h(qreg[qubit_idx]),
            ComponentType.S_GATE: lambda: circuit.s(qreg[qubit_idx]),
            ComponentType.T_GATE: lambda: circuit.t(qreg[qubit_idx]),
        }
        
        if comp_type in gate_map and qubit_idx >= 0:
            gate_map[comp_type]()
            return
        
        # Two-qubit gates
        if comp_type in [ComponentType.CNOT_GATE, ComponentType.CZ_GATE, ComponentType.SWAP_GATE]:
            control_lane = component.control_lane
            target_lane = component.target_lane
            
            if control_lane is not None and target_lane is not None:
                ctrl_idx = lane_to_qubit.get(control_lane, -1)
                tgt_idx = lane_to_qubit.get(target_lane, -1)
                if ctrl_idx >= 0 and tgt_idx >= 0 and ctrl_idx != tgt_idx:
                    if comp_type == ComponentType.CNOT_GATE:
                        circuit.cx(qreg[ctrl_idx], qreg[tgt_idx])
                    elif comp_type == ComponentType.CZ_GATE:
                        circuit.cz(qreg[ctrl_idx], qreg[tgt_idx])
                    elif comp_type == ComponentType.SWAP_GATE:
                        circuit.swap(qreg[ctrl_idx], qreg[tgt_idx])
            else:
                # Fallback: gate at control lane, target is next lane
                if qubit_idx >= 0:
                    target_lane_fallback = lane + 1
                    tgt_idx = lane_to_qubit.get(target_lane_fallback, -1)
                    if tgt_idx >= 0 and tgt_idx != qubit_idx:
                        if comp_type == ComponentType.CNOT_GATE:
                            circuit.cx(qreg[qubit_idx], qreg[tgt_idx])
                        elif comp_type == ComponentType.CZ_GATE:
                            circuit.cz(qreg[qubit_idx], qreg[tgt_idx])
                        elif comp_type == ComponentType.SWAP_GATE:
                            circuit.swap(qreg[qubit_idx], qreg[tgt_idx])
            return
        
        # Measurement and reset
        if comp_type == ComponentType.MEASURE and qubit_idx >= 0:
            circuit.measure(qreg[qubit_idx], creg[qubit_idx])
        elif comp_type == ComponentType.RESET and qubit_idx >= 0:
            circuit.reset(qreg[qubit_idx])
    
    def _simulate_circuit_build(self, components: List[Component3D]) -> Dict[str, Any]:
        """Simulate circuit building when Qiskit is not available."""
        return {
            'num_qubits': len(set(comp.position[1] for comp in components)),
            'num_gates': len(components),
            'depth': max([comp.position[0] for comp in components], default=0) + 1
        }
    
    def calculate_syndrome(self, components: List[Component3D]) -> np.ndarray:
        """
        Calculate syndrome for current circuit configuration.
        
        Args:
            components: List of placed components
            
        Returns:
            Syndrome vector as numpy array
        """
        # Extract parity check components
        parity_checks = [c for c in components if c.component_type == ComponentType.PARITY_CHECK]
        ancilla_qubits = [c for c in components if c.component_type == ComponentType.ANCILLA_QUBIT]
        data_qubits = [c for c in components if c.component_type == ComponentType.DATA_QUBIT]
        
        # Use ancilla qubits as syndrome extractors if no dedicated parity checks
        if not parity_checks and ancilla_qubits:
            parity_checks = ancilla_qubits
        
        if not parity_checks or not data_qubits:
            return np.array([])
        
        # Build parity check matrix
        num_checks = len(parity_checks)
        num_data = len(data_qubits)
        
        parity_matrix = np.zeros((num_checks, num_data), dtype=int)
        
        # Simulate connections between parity checks and data qubits
        connection_distance = self.config.simulation.parity_connection_distance
        for i, check in enumerate(parity_checks):
            for j, data in enumerate(data_qubits):
                # Simple distance-based connection rule
                distance = abs(check.position[0] - data.position[0]) + abs(check.position[1] - data.position[1])
                if distance <= connection_distance:
                    parity_matrix[i, j] = 1
        
        # Check if we have any connections
        if np.sum(parity_matrix) == 0:
            # If no automatic connections, create a simple pattern
            for i in range(min(num_checks, num_data)):
                parity_matrix[i, i] = 1
                if i + 1 < num_data:
                    parity_matrix[i, i + 1] = 1
        
        # Build error vector from actual X_GATE positions in the circuit
        error_vector = np.zeros(num_data, dtype=int)
        
        # Find all X gates and map them to data qubits by Y-coordinate (lane)
        x_gates = [c for c in components if c.component_type == ComponentType.X_GATE]
        for x_gate in x_gates:
            gate_lane = x_gate.position[1]
            for j, data in enumerate(data_qubits):
                if data.position[1] == gate_lane:
                    error_vector[j] = 1
                    break
        
        # Calculate syndrome
        syndrome = np.dot(parity_matrix, error_vector) % 2
        
        self.syndrome_history.append(syndrome.copy())
        return syndrome
    
    def perform_error_correction(self, syndrome: np.ndarray, components: List[Component3D]) -> Dict[str, Any]:
        """
        Perform belief propagation decoding for error correction.
        
        Args:
            syndrome: Current syndrome vector
            components: List of circuit components
            
        Returns:
            Dictionary with correction results
        """
        if len(syndrome) == 0:
            return {'success': False, 'error': 'No syndrome available'}
        
        # Count data qubits
        data_qubits = [c for c in components if c.component_type == ComponentType.DATA_QUBIT]
        num_bits = len(data_qubits)
        
        if num_bits == 0:
            return {'success': False, 'error': 'No data qubits found'}
        
        # Simple belief propagation simulation
        max_iterations = self.config.simulation.bp_max_iterations
        convergence_threshold = self.config.simulation.bp_convergence_threshold
        
        # Initialize belief probabilities
        beliefs = np.ones(num_bits) * 0.5
        
        correction_history = []
        
        for iteration in range(max_iterations):
            old_beliefs = beliefs.copy()
            
            # Update beliefs based on syndrome constraints
            if len(syndrome) > 0:
                syndrome_weight = np.sum(syndrome) / len(syndrome)
                for i in range(num_bits):
                    if syndrome_weight > 0.5:
                        beliefs[i] = min(0.9, beliefs[i] + syndrome_weight * 0.2)
                    else:
                        beliefs[i] = max(0.1, beliefs[i] - (1 - syndrome_weight) * 0.1)
            
            beliefs = np.clip(beliefs, 0.01, 0.99)
            correction_history.append(beliefs.copy())
            
            # Check convergence
            if np.linalg.norm(beliefs - old_beliefs) < convergence_threshold:
                break
        
        # Determine correction
        correction = (beliefs > 0.5).astype(int)
        
        result = {
            'success': True,
            'correction': correction,
            'beliefs': beliefs,
            'iterations': iteration + 1,
            'history': correction_history,
            'syndrome_weight': np.sum(syndrome),
            'num_data_qubits': num_bits
        }
        
        self.error_corrections.append(result)
        return result
    
    def simulate_evolution(self, components: List[Component3D], shots: int = None) -> Dict[str, Any]:
        """
        Simulate quantum state evolution for the circuit.
        
        Args:
            components: List of placed components
            shots: Number of measurement shots
            
        Returns:
            Dictionary with simulation results
        """
        if shots is None:
            shots = self.config.simulation.default_shots
        
        circuit = self.build_circuit_from_components(components)
        
        if circuit is None:
            return {'success': False, 'error': 'Failed to build quantum circuit'}
        
        if QISKIT_AVAILABLE and hasattr(circuit, 'num_qubits'):
            try:
                simulator = AerSimulator()
                
                # Add measurements if not present
                if not any(instr.operation.name == 'measure' for instr in circuit.data):
                    circuit.measure_all()
                
                transpiled = transpile(circuit, simulator)
                job = simulator.run(transpiled, shots=shots)
                result = job.result()
                counts = result.get_counts()
                
                # Sort by count
                sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
                
                return {
                    'success': True,
                    'counts': counts,
                    'sorted_counts': sorted_counts[:10],  # Top 10 outcomes
                    'shots': shots
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}
        else:
            # Fallback simulation info
            return {
                'success': True,
                'fallback': True,
                'circuit_info': circuit
            }
    
    def clear_history(self):
        """Clear syndrome and correction history."""
        self.syndrome_history.clear()
        self.error_corrections.clear()
