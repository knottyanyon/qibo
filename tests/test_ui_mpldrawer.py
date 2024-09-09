"""Test that Qibo matplotlib drawer"""

import pytest
import matplotlib.pyplot
import numpy as np
from qibo import gates, callbacks, Circuit
from qibo.models import QFT
from qibo.ui import plot_circuit
from qibo.ui.drawer_utils import FusedEndGateBarrier, FusedStartGateBarrier
from qibo.ui.mpldrawer import _plot_params, _process_gates

# defining a dummy circuit
def circuit(nqubits=2):
    c = Circuit(nqubits)
    c.add(gates.H(0))
    c.add(gates.CNOT(0, 1))
    c.add(gates.M(0))
    c.add(gates.M(1))
    return c


def test_plot_circuit():
    """Test for main plot function"""
    circ = circuit()
    ax, _ = plot_circuit(circ)
    assert ax.title == ax.title


def test_empty_gates():
    "Empty gates test"
    assert _process_gates([], 2) == []


def test_circuit_measure():
    """Measure circuit"""
    c = Circuit(3)
    c.add(gates.M(qubit) for qubit in range(2))
    ax, _ = plot_circuit(c)
    assert ax.title == ax.title


def test_plot_circuit_error_style():
    """Test for style error function"""
    style = _plot_params(style="test")
    assert style == None


@pytest.mark.parametrize("clustered", [False, True])
def test_complex_circuit(clustered):
    """Complex circuits for several cases"""
    c = Circuit(3)
    c.add(gates.H(0))
    c.add(gates.H(1))
    c.add(gates.H(2))
    c.add(gates.X(1))
    c.add(gates.Z(0))
    c.add(gates.CNOT(0, 1))
    c.add(gates.CZ(0, 1))
    c.add(gates.CRX(0, 1, np.pi))
    c.add(gates.Y(1))
    c.add(gates.RY(1, np.pi))
    c.add(gates.CRY(1, 2, np.pi))
    c.add(gates.Z(1))
    c.add(gates.SX(2))
    c.add(gates.CSX(0, 2))
    c.add(gates.X(0))
    c.add(gates.TOFFOLI(0, 1, 2))
    c.add(gates.X(0))
    c.add(gates.CNOT(1, 2))
    c.add(gates.SWAP(1, 2))
    c.add(gates.SWAP(1, 2).dagger())
    c.add(gates.SX(1).dagger())
    c.add(gates.X(0))
    c.add(gates.X(2))
    c.add(gates.H(0))
    c.add(gates.SiSWAP(1, 2).dagger())
    c.add(gates.FSWAP(1, 2).dagger())
    c.add(gates.DEUTSCH(1, 0, 2, np.pi))
    c.add(gates.X(0))
    c.add(gates.M(qubit) for qubit in range(2))
    ax, _ = plot_circuit(c.invert(), cluster_gates=clustered, scale=0.70)
    assert ax.title == ax.title


def test_fused_gates():
    """Test for FusedStartGateBarrier and FusedEndGateBarrier"""
    min_q = 0
    max_q = 1
    l_gates = 1
    equal_qbits = True
    start_barrier = FusedStartGateBarrier(min_q, max_q, l_gates, equal_qbits)
    end_barrier = FusedEndGateBarrier(min_q, max_q)
    assert start_barrier.unitary == start_barrier.unitary
    assert end_barrier.unitary == end_barrier.unitary


def test_circuit_fused_gates():
    """Test for FusedStartGateBarrier and FusedEndGateBarrier"""
    c = QFT(5)
    c.add(gates.M(qubit) for qubit in range(2))
    ax, _ = plot_circuit(c.fuse(), scale=0.8, cluster_gates=True, style="quantumspain")
    assert ax.title == ax.title


def test_empty_circuit():
    """Test for printing empty circuit"""
    c = Circuit(2)
    ax, _ = plot_circuit(c)
    assert ax.title == ax.title


def test_circuit_entangled_entropy():
    """Circuit test for printing entanglement entropy circuit"""
    entropy = callbacks.EntanglementEntropy([0])
    c = Circuit(2)
    c.add(gates.CallbackGate(entropy))
    c.add(gates.H(0))
    c.add(gates.CallbackGate(entropy))
    c.add(gates.CNOT(0, 1))
    c.add(gates.CallbackGate(entropy))
    ax, _ = plot_circuit(c)
    assert ax.title == ax.title
