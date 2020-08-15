# -*- coding: utf-8 -*-
import numpy as np
from qibo import matrices, K
from qibo.config import BACKEND_NAME, DTYPES, raise_error
from qibo.base import hamiltonians as base_hamiltonians
from qibo.base.hamiltonians import TrotterHamiltonian
if BACKEND_NAME == "tensorflow":
    from qibo.tensorflow import hamiltonians
else: # pragma: no cover
    # case not tested because backend is preset to TensorFlow
    raise raise_error(NotImplementedError,
                      "Only Tensorflow backend is implemented.")


class Hamiltonian(base_hamiltonians.Hamiltonian):
    """"""

    def __new__(cls, nqubits, matrix):
        if isinstance(matrix, np.ndarray):
            return hamiltonians.NumpyHamiltonian(nqubits, matrix)
        elif isinstance(matrix, K.Tensor):
            return hamiltonians.TensorflowHamiltonian(nqubits, matrix)
        else:
            raise raise_error(TypeError, "Invalid type {} of Hamiltonian "
                                         "matrix.".format(type(matrix)))


def _multikron(matrix_list):
    """Calculates Kronecker product of a list of matrices.

    Args:
        matrices (list): List of matrices as ``np.ndarray``s.

    Returns:
        ``np.ndarray`` of the Kronecker product of all ``matrices``.
    """
    h = 1
    for m in matrix_list:
        h = np.kron(h, m)
    return h


def _build_spin_model(nqubits, matrix, condition):
    """Helper method for building nearest-neighbor spin model Hamiltonians."""
    h = sum(_multikron((matrix if condition(i, j) else matrices.I
                        for j in range(nqubits)))
            for i in range(nqubits))
    return h


def XXZ(nqubits, delta=0.5, numpy=False, trotter=False):
    """Heisenberg XXZ model with periodic boundary conditions.

    .. math::
        H = \\sum _{i=0}^N \\left ( X_iX_{i + 1} + Y_iY_{i + 1} + \\delta Z_iZ_{i + 1} \\right ).

    Args:
        nqubits (int): number of quantum bits.
        delta (float): coefficient for the Z component (default 0.5).
        numpy (bool): If ``True`` the Hamiltonian is created using numpy as the
            calculation backend, otherwise TensorFlow is used.
        trotter (bool): If ``True`` it creates the Hamiltonian as a
            :class:`qibo.base.hamiltonians.TrotterHamiltonian` object, otherwise
            it creates a :class:`qibo.base.hamiltonians.Hamiltonian` object.

    Example:
        ::

            from qibo.hamiltonians import XXZ
            h = XXZ(3) # initialized XXZ model with 3 qubits
    """
    if trotter:
        hx = np.kron(matrices.X, matrices.X)
        hy = np.kron(matrices.Y, matrices.Y)
        hz = np.kron(matrices.Z, matrices.Z)
        term = Hamiltonian(2, hx + hy + delta * hz)
        return TrotterHamiltonian.from_twoqubit_term(nqubits, term)

    condition = lambda i, j: i in {j % nqubits, (j+1) % nqubits}
    hx = _build_spin_model(nqubits, matrices.X, condition)
    hy = _build_spin_model(nqubits, matrices.Y, condition)
    hz = _build_spin_model(nqubits, matrices.Z, condition)
    matrix = hx + hy + delta * hz
    if not numpy:
        matrix = K.cast(matrix, dtype=DTYPES.get('DTYPECPX'))
    return Hamiltonian(nqubits, matrix)


def _OneBodyPauli(nqubits, matrix, numpy=False, trotter=False):
    """Helper method for constracting non-interacting X, Y, Z Hamiltonians."""
    if trotter:
        term_matrix = -np.kron(matrix, matrices.I)
        term = Hamiltonian(2, term_matrix)
        return TrotterHamiltonian.from_twoqubit_term(nqubits, term)

    condition = lambda i, j: i == j % nqubits
    ham = -_build_spin_model(nqubits, matrix, condition)
    if not numpy:
        ham = K.cast(ham, dtype=DTYPES.get('DTYPECPX'))
    return Hamiltonian(nqubits, ham)


def X(nqubits, numpy=False, trotter=False):
    """Non-interacting pauli-X Hamiltonian.

    .. math::
        H = - \\sum _{i=0}^N X_i.

    Args:
        nqubits (int): number of quantum bits.
        numpy (bool): If ``True`` the Hamiltonian is created using numpy as the
            calculation backend, otherwise TensorFlow is used.
        trotter (bool): If ``True`` it creates the Hamiltonian as a
            :class:`qibo.base.hamiltonians.TrotterHamiltonian` object, otherwise
            it creates a :class:`qibo.base.hamiltonians.Hamiltonian` object.
    """
    return _OneBodyPauli(nqubits, matrices.X, numpy, trotter)


def Y(nqubits, numpy=False, trotter=False):
    """Non-interacting pauli-X Hamiltonian.

    .. math::
        H = - \\sum _{i=0}^N Y_i.

    Args:
        nqubits (int): number of quantum bits.
        numpy (bool): If ``True`` the Hamiltonian is created using numpy as the
            calculation backend, otherwise TensorFlow is used.
        trotter (bool): If ``True`` it creates the Hamiltonian as a
            :class:`qibo.base.hamiltonians.TrotterHamiltonian` object, otherwise
            it creates a :class:`qibo.base.hamiltonians.Hamiltonian` object.
    """
    return _OneBodyPauli(nqubits, matrices.Y, numpy, trotter)


def Z(nqubits, numpy=False, trotter=False):
    """Non-interacting pauli-X Hamiltonian.

    .. math::
        H = - \\sum _{i=0}^N Z_i.

    Args:
        nqubits (int): number of quantum bits.
        numpy (bool): If ``True`` the Hamiltonian is created using numpy as the
            calculation backend, otherwise TensorFlow is used.
        trotter (bool): If ``True`` it creates the Hamiltonian as a
            :class:`qibo.base.hamiltonians.TrotterHamiltonian` object, otherwise
            it creates a :class:`qibo.base.hamiltonians.Hamiltonian` object.
    """
    return _OneBodyPauli(nqubits, matrices.Z, numpy, trotter)


def TFIM(nqubits, h=0.0, numpy=False, trotter=False):
    """Transverse field Ising model with periodic boundary conditions.

    .. math::
        H = - \\sum _{i=0}^N \\left ( Z_i Z_{i + 1} + h X_i \\right ).

    Args:
        nqubits (int): number of quantum bits.
        h (float): value of the transverse field.
        numpy (bool): If ``True`` the Hamiltonian is created using numpy as the
            calculation backend, otherwise TensorFlow is used.
        trotter (bool): If ``True`` it creates the Hamiltonian as a
            :class:`qibo.base.hamiltonians.TrotterHamiltonian` object, otherwise
            it creates a :class:`qibo.base.hamiltonians.Hamiltonian` object.
    """
    if trotter:
        term_matrix = -np.kron(matrices.Z, matrices.Z)
        term_matrix -= h * np.kron(matrices.X, matrices.I)
        term = Hamiltonian(2, term_matrix)
        return TrotterHamiltonian.from_twoqubit_term(nqubits, term)

    condition = lambda i, j: i in {j % nqubits, (j+1) % nqubits}
    ham = -_build_spin_model(nqubits, matrices.Z, condition)
    if h != 0:
        condition = lambda i, j: i == j % nqubits
        ham -= h * _build_spin_model(nqubits, matrices.X, condition)
    if not numpy:
        ham = K.cast(ham, dtype=DTYPES.get('DTYPECPX'))
    return Hamiltonian(nqubits, ham)
