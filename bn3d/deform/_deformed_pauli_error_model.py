import functools
from typing import Tuple
import numpy as np
from qecsim.model import ErrorModel
from qecsim.model import StabilizerCode
from ..noise import PauliErrorModel
from ._deformable_toric_3d_pauli import DeformableToric3DPauli


class DeformedPauliErrorModel(ErrorModel):
    """Pauli error model with qubits deformed."""

    _undeformed_model: PauliErrorModel

    def __init__(self, r_x, r_y, r_z):
        self._undeformed_model = PauliErrorModel(r_x, r_y, r_z)

    @property
    def label(self) -> str:
        return 'Deformed Pauli X{}Y{}Z{}'.format(*self.direction)

    def generate(
        self, code: StabilizerCode, probability: float, rng=None
    ) -> np.ndarray:
        error = self._undeformed_model.generate(code, probability, rng)
        deformed_error = self._deform_operator(code, error)
        return deformed_error

    def _deform_operator(
        self, code: StabilizerCode, error: np.ndarray
    ) -> np.ndarray:
        pauli = DeformableToric3DPauli(code, bsf=error)
        pauli.deform()
        return pauli.to_bsf()

    @functools.lru_cache()
    def probability_distribution(self, code: StabilizerCode, probability: float) -> Tuple:
        r_x, r_y, r_z = self.direction
        is_deformed = self.get_deformation_indices(code)

        p_i = np.array([1 - probability for i in range(code.n_k_d[0])])
        p_x = probability * np.array([r_z if is_deformed[i] else r_x for i in range(code.n_k_d[0])])
        p_y = probability * np.array([r_y for i in range(code.n_k_d[0])])
        p_z = probability * np.array([r_x if is_deformed[i] else r_z for i in range(code.n_k_d[0])])

        return p_i, p_x, p_y, p_z
    
    def get_deformation_indices(self, code: StabilizerCode):
        """Undeformed noise direction (r_X, r_Y, r_Z) for qubits."""
        is_deformed = [False for _ in range(code.n_k_d[0])]
        
        deformed_edge = code.X_AXIS
        ranges = [range(length) for length in code.shape]

        for axis, x, y, z in itertools.product(*ranges):
            if axis == deformed_edge:
                is_deformed[index] = True

        return is_deformed

    @property
    def direction(self):
        """Undeformed noise direction (r_X, r_Y, r_Z) for qubits."""
        return self._undeformed_model.direction
