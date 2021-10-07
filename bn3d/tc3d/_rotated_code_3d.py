from typing import Tuple, Optional, Dict
import numpy as np
from qecsim.model import StabilizerCode
from ._rotated_3d_pauli import Rotated3DPauli
from bn3d.bpauli import bcommute


class RotatedCode3D(StabilizerCode):

    _size: Tuple[int, int, int]
    _qubit_index: Dict[Tuple[int, int, int], int]
    _vertex_index: Dict[Tuple[int, int, int], int]
    _face_index: Dict[Tuple[int, int, int], int]
    _stabilizers = np.array([])
    _Hx = np.array([])
    _Hz = np.array([])
    _logical_xs = np.array([])
    _logical_zs = np.array([])

    def __init__(
        self, L_x: int,
        L_y: Optional[int] = None,
        L_z: Optional[int] = None
    ):
        if L_y is None:
            L_y = L_x
        if L_z is None:
            L_z = L_x

        self._size = (L_x, L_y, L_z)
        self._qubit_index = self._create_qubit_indices()
        self._vertex_index = self._create_vertex_indices()
        self._face_index = self._create_face_indices()

    # StabilizerCode interface methods.

    @property
    def n_k_d(self) -> Tuple[int, int, int]:
        Lx, Ly, Lz = self.size
        n_horizontals = 4*np.product(self.size)
        n_verticals = 2*Lx*Ly*(Lz-1)
        return (n_horizontals + n_verticals, -1, -1)

    @property
    def qubit_index(self) -> Dict[Tuple[int, int, int], int]:
        return self._qubit_index

    @property
    def vertex_index(self) -> Dict[Tuple[int, int, int], int]:
        return self._vertex_index
    
    @property
    def face_index(self) -> Dict[Tuple[int, int, int], int]:
        return self._face_index

    @property
    def label(self) -> str:
        return 'Rotated Toric {}x{}x{}'.format(*self.size)

    @property
    def stabilizers(self) -> np.ndarray:
        if self._stabilizers.size == 0:
            face_stabilizers = self.get_face_X_stabilizers()
            vertex_stabilizers = self.get_vertex_Z_stabilizers()
            self._stabilizers = np.concatenate([
                face_stabilizers,
                vertex_stabilizers,
            ])
        return self._stabilizers

    @property
    def Hz(self) -> np.ndarray:
        if self._Hz.size == 0:
            self._Hz = self.get_face_X_stabilizers()
        return self._Hz[:, :self.n_k_d[0]]

    @property
    def Hx(self) -> np.ndarray:
        if self._Hx.size == 0:
            self._Hx = self.get_vertex_Z_stabilizers()
        return self._Hx[:, self.n_k_d[0]:]

    @property
    def logical_xs(self) -> np.ndarray:
        """The 3 logical X operators."""

        if self._logical_xs.size == 0:
            L_x, L_y, L_z = self.size
            logicals = []

            # X operators along x edges in x direction.
            logical = Rotated3DPauli(self)
            for x in range(L_x):
                logical.site('X', (0, x, 0, 0))
            logicals.append(logical.to_bsf())

            # X operators along y edges in y direction.
            logical = Rotated3DPauli(self)
            for y in range(L_y):
                logical.site('X', (1, 0, y, 0))
            logicals.append(logical.to_bsf())

            # X operators along z edges in z direction
            logical = Rotated3DPauli(self)
            for z in range(L_z):
                logical.site('X', (2, 0, 0, z))
            logicals.append(logical.to_bsf())

            self._logical_xs = np.array(logicals, dtype=np.uint)

        return self._logical_xs

    @property
    def logical_zs(self) -> np.ndarray:
        """Get the 3 logical Z operators."""
        if self._logical_zs.size == 0:
            L_x, L_y, L_z = self.size
            logicals = []

            # Z operators on x edges forming surface normal to x (yz plane).
            logical = Rotated3DPauli(self)
            for y in range(L_y):
                for z in range(L_z):
                    logical.site('Z', (0, 0, y, z))
            logicals.append(logical.to_bsf())

            # Z operators on y edges forming surface normal to y (zx plane).
            logical = Rotated3DPauli(self)
            for z in range(L_z):
                for x in range(L_x):
                    logical.site('Z', (1, x, 0, z))
            logicals.append(logical.to_bsf())

            # Z operators on z edges forming surface normal to z (xy plane).
            logical = Rotated3DPauli(self)
            for x in range(L_x):
                for y in range(L_y):
                    logical.site('Z', (2, x, y, 0))
            logicals.append(logical.to_bsf())

            self._logical_zs = np.array(logicals, dtype=np.uint)

        return self._logical_zs

    @property
    def size(self) -> Tuple[int, int, int]:
        """Dimensions of lattice."""
        return self._size

    def _create_qubit_indices(self):
        Lx, Ly, Lz = self.size

        coordinates = []

        # Horizontal
        for x in range(1, 4*Lx, 2):
            for y in range(1, 4*Ly, 2):
                for z in range(1, 2*Lz, 2):
                    coordinates.append((x, y, z))

        # Vertical
        for x in range(2, 4*Lx, 2):
            for y in range(0, 4*Ly+1, 2):
                for z in range(2, 2*Lz, 2):
                    if (x + y) % 4 == 2:
                        coordinates.append((x, y, z))

        coord_to_index = {coord: i for i, coord in enumerate(coordinates)}

        return coord_to_index

    def _create_vertex_indices(self):
        Lx, Ly, Lz = self.size

        coordinates = []

        for z in range(1, 2*Lz, 2):
            for x in range(2, 4*Lx, 2):
                for y in range(0, 4*Ly+1, 2):
                    if (x + y) % 4 == 2:
                        coordinates.append((x, y, z))

        coord_to_index = {coord: i for i, coord in enumerate(coordinates)}

        return coord_to_index

    def _create_face_indices(self):
        Lx, Ly, Lz = self.size

        coordinates = []

        # Horizontal faces
        for x in range(0, 4*Lx+1, 2):
            for y in range(2, 4*Ly, 2):
                for z in range(1, 2*Lz, 2):
                    if (x + y) % 4 == 0:
                        coordinates.append((x, y, z))
        # Vertical faces
        for x in range(3, 4*Lx-1, 2):
            for y in range(1, 4*Ly, 2):
                for z in range(2, 2*Lz, 2):
                    coordinates.append((x, y, z))

        coord_to_index = {coord: i for i, coord in enumerate(coordinates)}

        return coord_to_index

    def get_vertex_Z_stabilizers(self) -> np.ndarray:
        vertex_stabilizers = []

        for (x, y, z) in self.vertex_index.keys():
            operator = Rotated3DPauli(self)
            operator.vertex('Z', (x, y, z))
            vertex_stabilizers.append(operator.to_bsf())

        return np.array(vertex_stabilizers, dtype=np.uint)

    def get_face_X_stabilizers(self) -> np.ndarray:
        face_stabilizers = []

        for (x, y, z) in self.face_index.keys():
            operator = Rotated3DPauli(self)
            operator.face('X', (x, y, z))
            face_stabilizers.append(operator.to_bsf())

        return np.array(face_stabilizers, dtype=np.uint)

    def measure_syndrome(self, error: Rotated3DPauli) -> np.ndarray:
        """Perfectly measure syndromes given Pauli error."""
        return bcommute(self.stabilizers, error.to_bsf())


if __name__ == "__main__":
    code = RotatedCode3D(2)

    print("Vertices", code.face_index)