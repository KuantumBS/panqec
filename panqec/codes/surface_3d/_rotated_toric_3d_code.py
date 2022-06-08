from typing import Tuple, Dict, List
import numpy as np
from panqec.codes import StabilizerCode

Location = Tuple
Operator = Dict[Location, str]  # Location to pauli ('X', 'Y' or 'Z')
Coordinates = List[Tuple]  # List of locations


def on_defect_boundary(Lx, Ly, x, y):
    """Determine whether or not to defect each boundary."""
    defect_x_boundary = False
    defect_y_boundary = False
    if Lx % 2 == 1 and x == 2*Lx:
        defect_x_boundary = True
    if Ly % 2 == 1 and y == 2*Ly:
        defect_y_boundary = True
    return defect_x_boundary, defect_y_boundary


class RotatedToric3DCode(StabilizerCode):
    """Rotated Toric Code for good subthreshold scaling."""

    dimension = 3

    @property
    def label(self) -> str:
        return 'Rotated Toric 3D {}x{}x{}'.format(*self.size)

    def get_qubit_coordinates(self) -> Coordinates:
        Lx, Ly, Lz = self.size

        coordinates: Coordinates = []

        # Horizontal
        for x in range(1, 2*Lx, 2):
            for y in range(1, 2*Ly, 2):
                for z in range(1, 2*Lz, 2):
                    coordinates.append((x, y, z))

        # Vertical
        for x in range(2, 2*Lx + 1, 2):
            for y in range(2, 2*Ly + 1, 2):
                for z in range(2, 2*Lz, 2):
                    if (x + y) % 4 == 2:
                        coordinates.append((x, y, z))

        return coordinates

    def get_stabilizer_coordinates(self) -> Coordinates:
        coordinates: Coordinates = []
        Lx, Ly, Lz = self.size

        # Vertices
        for x in range(2, 2*Lx + 1, 2):
            for y in range(2, 2*Ly + 1, 2):
                for z in range(1, 2*Lz, 2):
                    if (x + y) % 4 == 2:
                        coordinates.append((x, y, z))

        # Horizontal faces
        for x in range(2, 2*Lx + 1, 2):
            for y in range(2, 2*Ly + 1, 2):
                for z in range(1, 2*Lz, 2):
                    if (x + y) % 4 == 0:
                        coordinates.append((x, y, z))

        # Vertical faces
        for x in range(1, 2*Lx, 2):
            for y in range(1, 2*Ly, 2):
                for z in range(2, 2*Lz, 2):
                    if not (
                        (Ly % 2 == 1 and y == 1)
                        or (Lx % 2 == 1 and x == 1)
                    ):
                        coordinates.append((x, y, z))

        return coordinates

    def stabilizer_type(self, location: Location) -> str:
        if not self.is_stabilizer(location):
            raise ValueError(f"Invalid coordinate {location} for a stabilizer")

        x, y, z = location
        if (x + y) % 4 == 2 and z % 2 == 1:
            return 'vertex'
        else:
            return 'face'

    def get_stabilizer(self, location, deformed_axis=None) -> Operator:
        if not self.is_stabilizer(location):
            raise ValueError(f"Invalid coordinate {location} for a stabilizer")

        if self.stabilizer_type(location) == 'vertex':
            pauli = 'Z'
        else:
            pauli = 'X'

        deformed_pauli = {'X': 'Z', 'Z': 'X'}[pauli]

        x, y, z = location
        Lx, Ly, Lz = self.size
        defect_x_boundary, defect_y_boundary = on_defect_boundary(Lx, Ly, x, y)

        if self.stabilizer_type(location) == 'vertex':
            delta = [
                (1, -1, 0), (-1, 1, 0), (1, 1, 0), (-1, -1, 0), (0, 0, 1),
                (0, 0, -1)
            ]
        else:
            # z-normal so face is xy-plane.
            if z % 2 == 1:
                delta = [(-1, -1, 0), (1, 1, 0), (-1, 1, 0), (1, -1, 0)]
            # x-normal so face is in yz-plane.
            elif (x + y) % 4 == 0:
                delta = [(-1, -1, 0), (1, 1, 0), (0, 0, -1), (0, 0, 1)]
            # y-normal so face is in zx-plane.
            elif (x + y) % 4 == 2:
                delta = [(-1, 1, 0), (1, -1, 0), (0, 0, -1), (0, 0, 1)]

        operator: Operator = dict()
        for d in delta:
            qx, qy, qz = tuple(np.add(location, d))
            if qx > 2*Lx:
                qx = 1
            elif qx == 0:
                qx = 2*Lx
            if qy > 2*Ly:
                qy = 1
            elif qy == 0:
                qy = 2*Ly
            qubit_location = (qx, qy, qz)

            if self.is_qubit(qubit_location):
                defect_x_on_edge = defect_x_boundary and qubit_location[0] == 1
                defect_y_on_edge = defect_y_boundary and qubit_location[1] == 1
                has_defect = (defect_x_on_edge != defect_y_on_edge)

                is_deformed = (
                    self.qubit_axis(qubit_location) == deformed_axis
                )

                operator[qubit_location] = (
                    deformed_pauli if is_deformed != has_defect else pauli
                )

        return operator

    def qubit_axis(self, location: Location) -> str:
        x, y, z = location

        if location not in self.qubit_coordinates:
            raise ValueError(
                f'Location {location} does not correspond to a qubit'
            )

        if z % 2 == 0:
            axis = 'z'
        elif (x + y) % 4 == 2:
            axis = 'x'
        elif (x + y) % 4 == 0:
            axis = 'y'

        return axis

    def get_logicals_x(self) -> List[Operator]:
        """Get the logical X operators."""

        Lx, Ly, Lz = self.size
        logicals: List[Operator] = []

        # Even times even - two logicals.
        if Lx % 2 == 0 and Ly % 2 == 0:
            # X string operator along y.
            logicals.append({
                (x, y, z): 'X'
                for x, y, z in self.qubit_coordinates
                if y == 1 and z == 1
            })

            # X string operator along x.
            logicals.append({
                (x, y, z): 'X'
                for x, y, z in self.qubit_coordinates
                if x == 1 and z == 1
            })

        # TODO: Get odd times odd to work
        # Odd times odd
        elif Lx % 2 == 1 and Ly % 2 == 1:
            operator: Operator = dict()
            for x, y, z in self.qubit_coordinates:
                # X string operator in undeformed code. (OK)
                if z == 1 and x + y == 2*Lx-2:
                    operator[(x, y, z)] = 'X'
            logicals.append(operator)

        # Odd times even or even times odd - only one logical.
        else:

            # Odd times even.
            if Lx % 2 == 1:
                logicals.append({
                    (x, y, z): 'X'
                    for x, y, z in self.qubit_coordinates
                    if x == 1 and z == 1
                })

            # Even times odd.
            else:
                logicals.append({
                    (x, y, z): 'X'
                    for x, y, z in self.qubit_coordinates
                    if y == 1 and z == 1
                })

        return logicals

    def get_logicals_z(self) -> List[Operator]:
        """Get the logical Z operators."""

        Lx, Ly, Lz = self.size
        logicals = []

        # Even times even.
        if (Lx % 2 == 0) and (Ly % 2 == 0):
            operator: Operator = dict()
            for x, y, z in self.qubit_coordinates:
                if x == 1:
                    operator[(x, y, z)] = 'Z'
            logicals.append(operator)

            operator = dict()
            for x, y, z in self.qubit_coordinates:
                if y == 1:
                    operator[(x, y, z)] = 'Z'

            logicals.append(operator)

        # TODO get this to work.
        # Odd times odd
        elif (Lx % 2 == 1) and (Ly % 2 == 1):
            operator = dict()
            for x, y, z in self.qubit_coordinates:
                if x == y:
                    operator[(x, y, z)] = 'Z'

            logicals.append(operator)

        # Odd times even
        else:
            operator = dict()
            for x, y, z in self.qubit_coordinates:
                if (Lx % 2 == 1 and y == 1) or (Ly % 2 == 1 and x == 1):
                    operator[(x, y, z)] = 'Y'

            logicals.append(operator)

        return logicals

    def qubit_representation(
        self, location, rotated_picture=False, json_file=None
    ) -> Dict:
        representation = super().qubit_representation(
            location, rotated_picture, json_file
        )

        if self.qubit_axis(location) == 'z':
            representation['params']['length'] = 2

        return representation

    def stabilizer_representation(
        self, location, rotated_picture=False, json_file=None
    ) -> Dict:
        representation = super().stabilizer_representation(
            location, rotated_picture, json_file
        )

        x, y, z = location
        if not rotated_picture and self.stabilizer_type(location) == 'face':
            if z % 2 == 1:
                representation['params']['normal'] = [0, 0, 1]
                representation['params']['angle'] = np.pi/4
            else:
                representation['params']['w'] = 1.5
                representation['params']['angle'] = 0

                if (x + y) % 4 == 0:
                    representation['params']['normal'] = [1, 1, 0]
                else:
                    representation['params']['normal'] = [-1, 1, 0]

        if rotated_picture and self.stabilizer_type(location) == 'face':
            if z % 2 == 1:
                representation['params']['normal'] = [0, 0, 1]
                representation['params']['angle'] = 0
            else:
                representation['params']['w'] = 1.4142
                representation['params']['h'] = 1.4142
                representation['params']['angle'] = np.pi/4

                if (x + y) % 4 == 0:
                    representation['params']['normal'] = [1, 1, 0]
                else:
                    representation['params']['normal'] = [-1, 1, 0]

        return representation
