"""Tests for qldpc.tanner.graph_3d: Tanner graph model smoke tests (H7)."""

import matplotlib

matplotlib.use("Agg")

from qldpc.tanner.graph_3d import QuantumLDPCTannerGraph


class TestTannerGraphInit:
    def test_default_construction(self):
        graph = QuantumLDPCTannerGraph()
        assert graph is not None

    def test_custom_construction(self):
        graph = QuantumLDPCTannerGraph(n_qubits=15, n_checks=8)
        assert graph.n_qubits == 15
        assert graph.n_checks == 8

    def test_graph_initialization(self):
        graph = QuantumLDPCTannerGraph()
        graph.initialize_graph()
        # Graph should have nodes
        assert graph.graph.number_of_nodes() > 0
        # Graph should have edges
        assert graph.graph.number_of_edges() > 0

    def test_node_count(self):
        nq, nc = 10, 5
        graph = QuantumLDPCTannerGraph(n_qubits=nq, n_checks=nc)
        graph.initialize_graph()
        assert graph.graph.number_of_nodes() == nq + nc


class TestTannerGraphSyndrome:
    def test_trigger_syndrome(self):
        graph = QuantumLDPCTannerGraph()
        graph.initialize_graph()
        total_nodes = graph.graph.number_of_nodes()
        # Trigger the first check node (checks come after qubits)
        check_idx = graph.n_qubits
        if check_idx < total_nodes:
            graph.trigger_syndrome(check_idx)

    def test_edge_positions(self):
        graph = QuantumLDPCTannerGraph()
        graph.initialize_graph()
        edges = graph.get_edge_positions()
        assert len(edges) > 0
