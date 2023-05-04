import functools as ft

import numpy as np

from qibo.backends import GlobalBackend
from qibo.quantum_info import meyer_wallach, random_unitary


def haar_integral(nqubits, t, samples, backend=None):
    """Computes the integral over pure states over the Haar measure.
    .. math:: \\int_{\text{Haar}}\\left(|\\psi\rangle\\langle\\psi|\right)^{\\otimes t}d\\psi

    Args:
        nqubits (int): Number of qubits.
        t (int): index t to define the t-design.
        samples (int): number of samples to estimate the integral.
        backend (qibo.backends.abstract.Backend): Calculation engine.

    Return:
        (array) : Estimation of the Haar integral.
    """

    if backend == None:
        backend = GlobalBackend()

    dim = 2**nqubits
    randunit_density = backend.cast(np.zeros((dim**t, dim**t), dtype=complex))
    for _ in range(samples):
        haar_unit = random_unitary(dim, "haar", backend=backend)[:, 0].reshape(-1, 1)
        rho = haar_unit @ haar_unit.conjugate().transpose()
        randunit_density += ft.reduce(np.kron, [rho] * t)
    return randunit_density / samples


def pqc_integral(circuit, t, samples, backend=None):
    """Computes the integral over pure states generated by uniformly sampling in the
        parameter space described by the parametrized `circuit`.
    .. math:: \\int_{\\Theta}\\left(|\\psi_{\theta}\rangle\\langle\\psi_{\theta}|\right)^{\\otimes t}d\\psi

    Args:
        circuit (qibo.models.Circuit): Parametrized circuit.
        t (int): index t to define the t-design.
        samples (int): number of samples to estimate the integral.
        backend (qibo.backends.abstract.Backend): Calculation engine.

    Return:
        (array) : Estimation of the integral.
    """

    if backend == None:
        backend = GlobalBackend()

    circuit.density_matrix = True
    dim = 2**circuit.nqubits
    randunit_density = backend.cast(np.zeros((dim**t, dim**t), dtype=complex))
    nparams = 0
    for gate in circuit.queue:
        if hasattr(gate, "trainable") and gate.trainable:
            nparams += len(gate.parameters)
    for _ in range(samples):
        params = np.random.uniform(-np.pi, np.pi, nparams)
        circuit.set_parameters(params)
        rho = backend.execute_circuit(circuit).state()
        randunit_density += ft.reduce(np.kron, [rho] * t)
    return randunit_density / samples


def entangling_capability(circuit, samples, backend=None):
    """Computes the Meyer-Wallach entanglement Q of the `circuit`,
    .. math:: Ent = 1-\frac{1}{N}\\sum_{k}\text{Tr}\\left(\rho_k^2(\theta_i)\right)

    Args:
        circuit (qibo.models.Circuit): Parametrized circuit.
        samples (int): number of samples to estimate the integral.
        backend (qibo.backends.abstract.Backend): Calculation engine.

    Return:
        (int) : Entangling capability.
    """

    res = backend.cast(np.zeros(samples, dtype=complex))
    nparams = 0
    for gate in circuit.queue:
        if hasattr(gate, "trainable") and gate.trainable:
            nparams += len(gate.parameters)
    for i in range(samples):
        params = np.random.uniform(-np.pi, np.pi, nparams)
        circuit.set_parameters(params)
        res[i] = meyer_wallach(circuit, backend=None)
    return 2 * np.sum(res).real / samples
