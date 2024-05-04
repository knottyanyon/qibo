from functools import cache
from inspect import signature
from itertools import product
from typing import Union

import numpy as np
from sympy import S

from qibo import Circuit, gates, symbols
from qibo.backends import GlobalBackend
from qibo.config import raise_error
from qibo.hamiltonians import SymbolicHamiltonian


@cache
def _gates(nqubits):
    """Returns a list of gates used in state preparation.

    Args:
        nqubits (int): Number of qubits for the circuit.
    Returns:
        list(:class:`qibo.gates.abstract.Gate`): list of the gates used in state preparation.
    """

    return list(
        product(
            [(gates.I,), (gates.X,), (gates.H,), (gates.H, gates.S)], repeat=nqubits
        )
    )


@cache
def _measurements(nqubits):
    """Returns a list of gates used for measurement bases.

    Args:
        nqubits (int): Number of qubits for the circuit.
    Returns:
        list(:class:`qibo.gates.abstract.Gate`): list of the gates used for measurement bases.
    """

    return list(product([gates.Z, gates.X, gates.Y, gates.Z], repeat=nqubits))


@cache
def _observables(nqubits):
    """Returns a list of gates used for the function _get_observable().

    Args:
        nqubits (int): Number of qubits for the circuit.
    Returns:
        list(:class:`qibo.gates.abstract.Gate`): list of the gates used for the function _get_observable().
    """

    return list(product([symbols.I, symbols.Z, symbols.Z, symbols.Z], repeat=nqubits))


@cache
def _get_observable(j, nqubits):
    """Returns a list of gates used for the function _get_observable(). Here,

    .. math::
        j \\in \\{0, 1, 2, 3\\}^{\\otimes n} \\equiv \\{ I, X, Y, Z\\}^{\\otimes n}.

    Args:
        j (int): The index of the measurement basis.
        nqubits (int): Number of qubits.
    Returns:
        list(:class:`qibo.hamiltonians.SymbolicHamiltonian`): Symbolic hamiltonian of the observable.
    """

    if j == 0 and nqubits >= 3:
        raise_error(
            ValueError,
            f"nqubits given as {nqubits}. nqubits needs to be either 1 or 2.",
        )
    observables = _observables(nqubits)[j]
    observable = S(1)
    for q, obs in enumerate(observables):
        if obs is not symbols.I:
            observable *= obs(q)
    return SymbolicHamiltonian(observable, nqubits=nqubits)


@cache
def _prepare_state(k, nqubits):
    """Prepares the :math:`k`-th state for an :math:`n`-qubits (`nqubits`) circuit, where

    .. math::
        k \\in \\{0, 1, 2, 3\\}^{\\otimes n} \\equiv \\{ 0\\rangle\\langle0|, |1\\rangle\\langle1|,
        |+\\rangle\\langle +|, |y+\\rangle\\langle y+|\\}^{\\otimes n}.

    Args:
        k (int): The index of the state to be prepared.
        nqubits (int): Number of qubits.

    Returns:
        list(:class:`qibo.gates.abstract.Gate`): list of the gates that prepare the k-th state.
    """

    if not nqubits in (1, 2):
        raise_error(
            ValueError,
            f"nqubits needs to be either 1 or 2, but is {nqubits}.",
        )
    gates = _gates(nqubits)[k]
    return [gate(q) for q in range(len(gates)) for gate in gates[q]]


@cache
def _measurement_basis(j, nqubits):
    """Constructs the j-th measurement basis for an :math:`n`-qubits (`nqubits`) circuit, where

    .. math::
        j \\in \\{0, 1, 2, 3\\}^{\\otimes n} \\equiv \\{ I, X, Y, Z\\}^{\\otimes n}.

    Args:
        j (int): The index of the measurement basis.
        nqubits (int): Number of qubits.

    Returns:
        list[:class:`qibo.gates.abstract.Gate`]: list of gates forming the :math:`j`-th element
        of the Pauli measurement basis.
    """

    if not nqubits in (1, 2):
        raise_error(
            ValueError,
            f"nqubits given as {nqubits}. nqubits needs to be either 1 or 2.",
        )

    measurements = _measurements(nqubits)[j]
    return [gates.M(q, basis=measurements[q]) for q in range(len(measurements))]


def _expectation_value(circuit, j, nshots=int(1e4), backend=None):
    """Executes a circuit used in gate set tomography and processes the
        measurement outcomes for the Pauli Transfer Matrix notation. The circuit
        should already have noise models implemented, if any, prior to using this
        function.

        The function returns the expectation value given by either
        :math:`\\text{tr}(M_j rho_k)` or :math:`\\Tr(M_j O_l rho_k)`,
        where :math:`k` is the index of the state prepared (which is not necessary
        in this function since it has been used earlier), :math:`j` is the index
        of the measurement basis, and :math:`O_l` is the :math:`i`-th gate of
        the circuit.

    Args:
        circuit (:class:`qibo.models.Circuit`): The Qibo circuit to be executed.
        j (int): The index of the measurement basis.
        nshots (int, optional): Number of shots to execute the circuit with.
    Returns:
        numpy.float: Expectation value.
    """

    nqubits = circuit.nqubits
    if not nqubits in (1, 2):
        raise_error(
            ValueError,
            f"nqubits given as {nqubits}. nqubits needs to be either 1 or 2.",
        )

    else:
        if j == 0:
            return 1.0
        if backend is None:  # pragma: no cover
            backend = GlobalBackend()

        result = backend.execute_circuit(circuit, nshots=nshots)
        observable = _get_observable(j, nqubits)
        return result.expectation_from_samples(observable)


def _gate_tomography(
    nqubits,
    gate=None,
    nshots=int(1e4),
    noise_model=None,
    backend=None,
):
    """Runs gate set tomography for a 1 or 2 qubit gate to obtain a :math:`4^n` by :math:`4^n` matrix (where :math:`n`
    is the number of qubits in the circuit). This matrix needs to be processed further to get the Pauli-Liouville
    representation of the `gate`. The matrix has elements :math:`\\text{tr}(M_{j} \\, \\rho_{k})` or
    :math:`\\text{tr}(M_{j} \\, O_{l} \\rho_{k})` depending on whether the gate :math:`O_l` is present.

    Args:
        nshots (int, optional): Number of shots used in Gate Set Tomography.
        gate (:class:`qibo.gates.abstract.Gate`, optional): The gate to perform gate set tomography on. If ``None``, then gate set tomography will be performed for an empty circuit.
        noise_model (:class:`qibo.noise.NoiseModel`, optional): Noise model applied to simulate noisy computation.
        backend (:class:`qibo.backends.abstract.Backend`, optional): Calculation engine.
    Returns:
        ndarray: array with elements ``jk``.
    """

    # Check if gate is 1 or 2 qubit gate.
    if not nqubits in (1, 2):
        raise_error(
            ValueError,
            f"nqubits given as {nqubits}. nqubits needs to be either 1 or 2.",
        )

    if backend is None:  # pragma: no cover
        backend = GlobalBackend()

    if gate is not None:
        if nqubits != len(gate.qubits):
            raise_error(
                ValueError,
                f"Mismatched inputs: nqubits given as {nqubits}. {gate} is a {len(gate.qubits)}-qubit gate.",
            )
        gate = gate.__class__(*gate.qubits, **gate.init_kwargs)

    # GST for empty circuit or with gates
    matrix_jk = np.zeros((4**nqubits, 4**nqubits))
    for k in range(4**nqubits):
        circ = Circuit(nqubits, density_matrix=True)
        circ.add(_prepare_state(k, nqubits))

        if gate is not None:
            circ.add(gate)

        for j in range(4**nqubits):
            new_circ = circ.copy()
            measurements = _measurement_basis(j, nqubits)
            new_circ.add(measurements)
            if noise_model is not None and backend.name != "qibolab":
                new_circ = noise_model.apply(new_circ)
            expectation_val = _expectation_value(new_circ, j, nshots, backend=backend)
            matrix_jk[j, k] = expectation_val
    return matrix_jk


def GST(
    gate_set=Union[tuple, set, list],
    nshots=int(1e4),
    noise_model=None,
    include_empty=False,
    Pauli_Liouville=False,
    T=None,
    backend=None,
):
    """This is a wrapper function that runs gate set tomography for a list of gates. One can choose to output the gate set tomography
    for each gate in the Pauli-Liouville representation or not.


    Args:
        gate_set (tuple, set, list): A list containing :class:`qibo.gates.abstract.Gate`.
        nshots (int, optional): Number of shots used in Gate Set Tomography.
        noise_model (:class:`qibo.noise.NoiseModel`, optional): Noise model applied to simulate noisy computation.
        include_empty (bool, optional): If ``True``, perform gate set tomography for empty circuits.
        Pauli_Liouville (bool, optional): If ``True``, returns gate set tomography of the gates in the Pauli-Liouville representation.
        T (numpy array): A 4x4 invertible matrix that must be the same for all gates on the same qubit.
        backend (:class:`qibo.backends.abstract.Backend`, optional): Calculation engine.
    Returns:
        list(ndarray): List of matrices of the gate(s) in gate set tomography.
    """

    matrices = []
    empty_matrices = []
    if include_empty or Pauli_Liouville:
        for nqubits in range(1, 3):
            empty_matrix = _gate_tomography(
                nqubits=nqubits,
                gate=None,
                nshots=nshots,
                noise_model=noise_model,
                backend=backend,
            )
            empty_matrices.append(empty_matrix)

    for gate in gate_set:
        if gate is not None:
            init_args = signature(gate).parameters
            if "q" in init_args:
                nqubits = 1
            elif "q0" in init_args and "q1" in init_args and "q2" not in init_args:
                nqubits = 2
            else:
                raise_error(
                    RuntimeError,
                    f"Gate {gate} is not supported for `GST`, only 1- and 2-qubits gates are supported.",
                )
            gate = gate(*range(nqubits))

        matrices.append(
            _gate_tomography(
                nqubits=nqubits,
                gate=gate,
                nshots=nshots,
                noise_model=noise_model,
                backend=backend,
            )
        )

    if Pauli_Liouville:
        if T is not None:
            if np.linalg.det(T) == 0:
                raise_error(ValueError, "Matrix is not invertible")
        else:
            T = np.array([[1, 1, 1, 1], [0, 0, 1, 0], [0, 0, 0, 1], [1, -1, 0, 0]])
        PL_matrices = []
        for matrix in matrices:
            T_matrix = T if matrix.shape[0] == 4 else np.kron(T, T)
            empty = empty_matrices[0] if matrix.shape[0] == 4 else empty_matrices[1]
            PL_matrix = (
                T_matrix @ np.linalg.inv(empty) @ matrix @ np.linalg.inv(T_matrix)
            )
            PL_matrices.append(PL_matrix)
        matrices = PL_matrices

    if include_empty:
        matrices = empty_matrices + matrices

    return matrices
