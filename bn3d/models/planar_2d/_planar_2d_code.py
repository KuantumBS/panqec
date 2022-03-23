from typing import Tuple, Dict
from bn3d.models import StabilizerCode
from ._planar_2d_pauli import Planar2DPauli
from ... import bsparse
from scipy.sparse import csr_matrix

Indexer = Dict[Tuple[int, int], int]  # coordinate to index


class Planar2DCode(StabilizerCode):

    pauli_class = Planar2DPauli

    # StabilizerCode interface methods.

    @property
    def dimension(self) -> int:
        return 2

    @property
    def label(self) -> str:
        return 'Toric {}x{}'.format(*self.size)

    @property
    def logical_xs(self) -> csr_matrix:
        if self._logical_xs.size == 0:
            Lx, Ly = self.size
            logicals = bsparse.empty_row(2*self.n)

            # X operators along x edges in x direction.
            logical = self.pauli_class(self)
            for x in range(1, 2*Lx, 2):
                logical.site('X', (x, 0))
            logicals = bsparse.vstack([logicals, logical.to_bsf()])

            self._logical_xs = logicals

        return self._logical_xs

    @property
    def logical_zs(self) -> csr_matrix:
        if self._logical_zs.size == 0:
            Lx, Ly = self.size
            logicals = bsparse.empty_row(2*self.n)

            # Z operators on x edges forming surface normal to x (yz plane).
            logical = self.pauli_class(self)
            for y in range(0, 2*Ly, 2):
                logical.site('Z', (1, y))
            logicals = bsparse.vstack([logicals, logical.to_bsf()])

            self._logical_zs = logicals

        return self._logical_zs

    def axis(self, location: Tuple[int, int]) -> int:
        x, y = location

        if (x % 2 == 1) and (y % 2 == 0):
            axis = self.X_AXIS
        elif (x % 2 == 0) and (y % 2 == 1):
            axis = self.Y_AXIS
        else:
            raise ValueError(f'Location {location} does not correspond to a qubit')

        return axis

    def _create_qubit_indices(self) -> Indexer:
        coordinates = []
        Lx, Ly = self.size

        # Qubits along e_x
        for x in range(1, 2*Lx, 2):
            for y in range(0, 2*Ly, 2):
                coordinates.append((x, y))

        # Qubits along e_y
        for x in range(2, 2*Lx, 2):
            for y in range(1, 2*Ly-1, 2):
                coordinates.append((x, y))

        coord_to_index = {coord: i for i, coord in enumerate(coordinates)}

        return coord_to_index

    def _create_vertex_indices(self) -> Indexer:
        coordinates = []
        Lx, Ly = self.size

        for x in range(2, 2*Lx, 2):
            for y in range(0, 2*Ly, 2):
                coordinates.append((x, y))

        coord_to_index = {coord: i for i, coord in enumerate(coordinates)}

        return coord_to_index

    def _create_face_indices(self) -> Indexer:
        coordinates = []
        Lx, Ly = self.size

        for x in range(1, 2*Lx, 2):
            for y in range(1, 2*Ly-1, 2):
                coordinates.append((x, y))

        coord_to_index = {coord: i for i, coord in enumerate(coordinates)}

        return coord_to_index
