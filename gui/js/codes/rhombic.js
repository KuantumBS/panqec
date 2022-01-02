import * as THREE from 'https://cdn.skypack.dev/three@v0.130.1';

import { AbstractCode, stringToArray } from './base.js';

export {RhombicCode};

class RhombicCode extends AbstractCode {
    constructor(size, Hx, Hz, indices, scene) {
        super(size, Hx, Hz, indices, scene);

        this.Lx = size[0];
        this.Ly = size[1];
        this.Lz = size[2];

        this.cubes = [];
        this.triangles = [];

        this.qubitIndex = indices['qubit'];
        this.triangleIndex = indices['vertex'];
        this.cubeIndex = indices['face'];

        this.stabilizers['X'] = this.triangles;
        this.stabilizers['Z'] = this.cubes;

        this.toggleStabFn['X'] = this.toggleTriangle;
        this.toggleStabFn['Z'] = this.toggleCube;

        this.SIZE = {radiusEdge: 0.05, radiusVertex: 0.1, lengthEdge: 1};
        this.COLOR = Object.assign(this.COLOR, {
            activatedTriangle: 0xf1c232,
            activatedCube: 0xf1c232,
            deactivatedCube: 0xf2f28c,
            deactivatedTriangle: 0xf2f2cc,
            deactivatedEdge: 0xffbcbc,
        });

        this.OPACITY = {
            activatedQubit: 1,
            minDeactivatedQubit: 0.1,
            maxDeactivatedQubit: 0.6,

            activatedStabilizer: {'X': 1, 'Z': 0.6},
            minDeactivatedStabilizer: {'X': 0.1, 'Z': 0},
            maxDeactivatedStabilizer: {'X': 0.6, 'Z': 0}
        }
    }

    getIndexQubit(x, y, z) {
        let key = `[${x}, ${y}, ${z}]`;
        return this.qubitIndex[key];
    }

    getIndexTriangle(axis, x, y, z) {
        let key = `[${axis}, ${x}, ${y}, ${z}]`;
        return this.triangleIndex[key];
    }

    getIndexCube(x, y, z) {
        let key = `[${x}, ${y}, ${z}]`;
        return this.cubeIndex[key];
    }

    toggleCube(cube, activate) {
        cube.isActivated = activate;
        let color = activate ? this.COLOR.activatedCube : this.COLOR.deactivatedCube;
        cube.material.color.setHex(color);
        
        if (this.opacityActivated) {
            cube.material.opacity = activate ? this.OPACITY.activatedStabilizer['Z'] : this.OPACITY.minDeactivatedStabilizer['Z'];
        }
        else {
            cube.material.opacity = activate ? this.OPACITY.activatedStabilizer['Z'] : this.OPACITY.maxDeactivatedStabilizer['Z'];
        }
    }

    toggleTriangle(triangle, activate) {
        triangle.isActivated = activate;
        let color = activate ? this.COLOR.activatedTriangle : this.COLOR.deactivatedTriangle;
        triangle.material.color.setHex(color);

        if (this.opacityActivated) {
            triangle.material.opacity = activate ? this.OPACITY.activatedStabilizer['X'] : this.OPACITY.minDeactivatedStabilizer['X'];
        }
        else {
            triangle.material.opacity = activate ? this.OPACITY.activatedStabilizer['X'] : this.OPACITY.maxDeactivatedStabilizer['X'];
        }
    }

    buildQubit(x, y, z) {
        const geometry = new THREE.CylinderGeometry(this.SIZE.radiusEdge, this.SIZE.radiusEdge, this.SIZE.lengthEdge, 32);

        const material = new THREE.MeshPhongMaterial({color: this.COLOR.deactivatedEdge, 
                                                      opacity: this.OPACITY.maxDeactivatedQubit, 
                                                      transparent: true});
        const edge = new THREE.Mesh(geometry, material);

        edge.position.x = x * this.SIZE.lengthEdge / 2;
        edge.position.y = y * this.SIZE.lengthEdge / 2;
        edge.position.z = z * this.SIZE.lengthEdge / 2;

        let x_axis = ((z % 2 == 0) && y % 2 == 0);
        let y_axis = ((z % 2 == 0) && x % 2 == 0);
        let z_axis = (z % 2 == 1);

        if (x_axis) {
            edge.rotateZ(Math.PI / 2)
        }
        else if (z_axis) {
            edge.rotateX(Math.PI / 2)
        }

        edge.hasError = {'X': false, 'Z': false};

        let index = this.getIndexQubit(x, y, z)

        edge.index = index;
        this.qubits[index] = edge;

        this.scene.add(edge);
    }

    buildTriangle(axis, x, y, z) {
        const L = this.SIZE.lengthEdge / 4

        const geometry = new THREE.BufferGeometry();

        let pos_x = x * this.SIZE.lengthEdge / 2;
        let pos_y = y * this.SIZE.lengthEdge / 2;
        let pos_z = z * this.SIZE.lengthEdge / 2;

        let delta_1 = [[1, 1, 1], [-1, -1, 1], [1, -1, -1], [-1, 1, -1]];
        let delta_2 = [[1, 1, -1], [-1, -1, -1], [1, -1, 1], [-1, 1, 1]];

        let delta = ((x + y + z) % 4 == 0) ? delta_1 : delta_2

        var vertices = new Float32Array([
            pos_x + delta[axis][0]*L, pos_y,                    pos_z,
            pos_x,                    pos_y + delta[axis][1]*L, pos_z,
            pos_x,                    pos_y,                    pos_z+delta[axis][2]*L
        ]);

        geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3) );

        const material = new THREE.MeshBasicMaterial({color: this.COLOR.deactivatedTriangle, 
                                                      opacity: this.OPACITY.maxDeactivatedStabilizer['X'], 
                                                      transparent: true, 
                                                      side: THREE.DoubleSide});
        const triangle = new THREE.Mesh(geometry, material);

        var geo = new THREE.EdgesGeometry(triangle.geometry);
        var mat = new THREE.LineBasicMaterial({color: 0x000000, linewidth: 1,
                                               opacity: this.OPACITY.maxDeactivatedStabilizer['X'], 
                                               transparent: true});
        var wireframe = new THREE.LineSegments(geo, mat);
        wireframe.renderOrder = 1; // make sure wireframes are rendered 2nd
        triangle.add(wireframe);

        let index = this.getIndexTriangle(axis, x, y, z);
        triangle.index = index;
        triangle.isActivated = false;

        this.triangles[index] = triangle;

        this.scene.add(triangle);
    }

    buildCube(x, y, z) {
        const L = this.SIZE.lengthEdge - 0.3
        const geometry = new THREE.BoxBufferGeometry(L, L, L);
        const material = new THREE.MeshToonMaterial({color: this.COLOR.deactivatedCube, 
                                                     opacity: this.OPACITY.maxDeactivatedStabilizer['Z'], 
                                                     transparent: true});
        const cube = new THREE.Mesh(geometry, material);

        var geo = new THREE.EdgesGeometry( cube.geometry );
        var mat = new THREE.LineBasicMaterial({color: 0x000000, linewidth: 2, 
                                               opacity: this.OPACITY.maxDeactivatedStabilizer['Z'], 
                                               transparent: true });
        var wireframe = new THREE.LineSegments( geo, mat );
        wireframe.renderOrder = 1; // make sure wireframes are rendered 2nd
        cube.add(wireframe);

        cube.position.x = x * this.SIZE.lengthEdge / 2;
        cube.position.y = y * this.SIZE.lengthEdge / 2;
        cube.position.z = z * this.SIZE.lengthEdge / 2;

        let index = this.getIndexCube(x, y, z);
        cube.index = index;
        cube.isActivated = false;
        this.cubes[index] = cube;

        this.scene.add(cube);
    }


    build() {
        for (const [coord, index] of Object.entries(this.qubitIndex)) {
            let [x, y, z] = stringToArray(coord)
            this.buildQubit(x, y, z)
        }
        for (const [coord, index] of Object.entries(this.cubeIndex)) {
            let [x, y, z] = stringToArray(coord)
            this.buildCube(x, y, z)
        }
        for (const [coord, index] of Object.entries(this.triangleIndex)) {
            let [axis, x, y, z] = stringToArray(coord)
            this.buildTriangle(axis, x, y, z)
        }
    }
}
