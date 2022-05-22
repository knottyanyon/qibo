import numpy as np
from qibo.config import raise_error, EINSUM_CHARS
from qibo.engines.abstract import Simulator
from qibo.engines.matrices import Matrices


class NumpyEngine(Simulator):

    def __init__(self):
        super().__init__()
        self.matrices = Matrices(self.dtype)

    def set_threads(self, nthreads):
        if nthreads > 1:
            raise_error(ValueError, "numpy does not support more than one thread.")

    def to_numpy(self, x):
        return x

    def zero_state(self, nqubits):
        """Generate |000...0> state as an array."""
        state = np.zeros(2 ** nqubits, dtype=self.dtype)
        state[0] = 1
        return state

    def control_matrix(self, gate):
        if len(gate.control_qubits) > 1:
            raise_error(NotImplementedError, "Cannot calculate controlled "
                                             "unitary for more than two "
                                             "control qubits.")
        matrix = self.asmatrix(gate)
        shape = matrix.shape
        if shape != (2, 2):
            raise_error(ValueError, "Cannot use ``control_unitary`` method on "
                                    "gate matrix of shape {}.".format(shape))
        zeros = np.zeros((2, 2), dtype=self.dtype)
        part1 = np.concatenate([np.eye(2, dtype=self.dtype), zeros], axis=0)
        part2 = np.concatenate([zeros, matrix], axis=0)
        return np.concatenate([part1, part2], axis=1)

    def _einsum_string(self, gate, nqubits):
        inp = list(EINSUM_CHARS[:nqubits])
        out = inp[:]
        trans = list(EINSUM_CHARS[nqubits : nqubits + len(gate.qubits)])
        for i, q in enumerate(gate.qubits):
            trans.append(inp[q])
            out[q] = trans[i]
        return "{},{}->{}".format("".join(inp), "".join(trans), "".join(out))

    def _control_order(self, gate, nqubits):
        loop_start = 0
        order = list(gate.control_qubits)
        targets = list(gate.target_qubits)
        for control in gate.control_qubits:
            for i in range(loop_start, control):
                order.append(i)
            loop_start = control + 1
            for i, t in enumerate(gate.target_qubits):
                if t > control:
                    targets[i] -= 1
        for i in range(loop_start, nqubits):
            order.append(i)
        return order, targets

    def apply_gate(self, gate, state, nqubits):
        # TODO: Implement density matrices
        # (most likely in another method or a different engine?)
        state = np.reshape(state, nqubits * (2,))
        opstring = self._einsum_string(gate, nqubits)
        if gate.is_controlled_by:
            matrix = np.reshape(self.asmatrix(gate), 2  * len(gate.target_qubits) * (2,))
            ncontrol = len(gate.control_qubits)
            nactive = nqubits - ncontrol
            order, _ = self._control_order(gate, nqubits)
            state = np.transpose(state, order)
            # Apply `einsum` only to the part of the state where all controls
            # are active. This should be `state[-1]`
            state = np.reshape(state, (2 ** ncontrol,) + nactive * (2,))
            updates = np.einsum(opstring, state[-1], matrix)
            # Concatenate the updated part of the state `updates` with the
            # part of of the state that remained unaffected `state[:-1]`.
            state = np.concatenate([state[:-1], updates[np.newaxis]], axis=0)
            state = np.reshape(state, nqubits * (2,))
            # Put qubit indices back to their proper places
            reverse_order = len(order) * [0]
            for i, r in enumerate(order):
                reverse_order[r] = i
            state = np.transpose(state, reverse_order)
        else:
            matrix = np.reshape(self.asmatrix(gate), 2  * len(gate.qubits) * (2,))
            state = np.einsum(opstring, state, matrix)
        return np.reshape(state, (2 ** nqubits,))

    def assert_allclose(self, value, target, rtol=1e-7, atol=0.0): # pragma: no cover
        np.testing.assert_allclose(value, target, rtol=rtol, atol=atol)