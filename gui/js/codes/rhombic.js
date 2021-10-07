import * as THREE from 'https://cdn.skypack.dev/three@v0.130.1';

import { AbstractCode } from './base.js';

export {RhombicCode};

class RhombicCode extends AbstractCode {
    constructor(L, Hx, Hz, indices, scene) {
        super(L, Hx, Hz, scene);

        this.cubes = [];
        this.triangles = [];

        this.stabilizers['X'] = this.triangles;
        this.stabilizers['Z'] = this.cubes;

        this.toggleStabFn['X'] = this.toggleTriangle;
        this.toggleStabFn['Z'] = this.toggleCube;

        this.X_AXIS = 1;
        this.Y_AXIS = 2;
        this.Z_AXIS = 0;
        
        this.SIZE = {radiusEdge: 0.05, radiusVertex: 0.1, lengthEdge: 1};
        this.COLOR = {activatedTriangle: 0xf1c232, activatedCube: 0xf1c232,
                      deactivatedCube: 0xf2f28c, deactivatedTriangle: 0xf2f2cc,
                      deactivatedEdge: 0xffbcbc,
                      errorX: 0xff0000, errorZ: 0x25CCF7, errorY: 0xa55eea};
    }

    getIndexQubit(axis, x, y, z) {
        let L = this.L;

        return axis*L**3 + x*L**2 + y*L + z;
    }

    getIndexCube(x, y, z) {
        let L = this.L;
    
        return Math.floor((x*L**2 + y*L + z) / 2);
    }
    
    getIndexTriangle(axis, x, y, z) {
        let L = this.L;
    
        return axis*L**3 + x*L**2 + y*L + z;
    }

    toggleCube(cube, activate) {
        cube.isActivated = activate;
        cube.material.opacity = activate ? this.MAX_OPACITY : this.currentOpacity;
        let color = activate ? this.COLOR.activatedCube : this.COLOR.deactivatedCube;
        cube.material.color.setHex(color);
        cube.material.opacity = this.currentOpacity;
    }
    
    toggleTriangle(triangle, activate) {
        triangle.isActivated = activate;
        triangle.material.transparent = !activate;
        let color = activate ? this.COLOR.activatedTriangle : this.COLOR.deactivatedTriangle;
        triangle.material.color.setHex(color);
        triangle.material.opacity = this.currentOpacity;
    }

    changeOpacity() {
        if (this.currentOpacity == this.MIN_OPACITY) {
            this.currentOpacity = this.MAX_OPACITY;
        }
        else {
            this.currentOpacity = this.MIN_OPACITY;
        }

        this.qubits.forEach(q => {
            if (!q.hasError['X'] && !q.hasError['Z']) {
                q.material.opacity = this.currentOpacity;
            }
        });
    
        this.cubes.forEach(c => {
            if (!c.isActivated) {
                c.material.opacity = this.currentOpacity;
                c.children[0].material.opacity = this.currentOpacity;
            }
        });
        this.triangles.forEach(t => {
            if (!t.isActivated) {
                t.material.opacity = this.currentOpacity;
                t.children[0].material.opacity = this.currentOpacity;
            }
        });
    }

    buildEdge(axis, x, y, z) {
        const geometry = new THREE.CylinderGeometry(this.SIZE.radiusEdge, this.SIZE.radiusEdge, this.SIZE.lengthEdge, 32);
    
        const material = new THREE.MeshPhongMaterial({color: this.COLOR.deactivatedEdge, opacity: this.currentOpacity, transparent: true});
        const edge = new THREE.Mesh(geometry, material);
    
        edge.position.x = x;
        edge.position.y = y;
        edge.position.z = z;
    
        if (axis == this.X_AXIS) {
            edge.position.y += this.SIZE.lengthEdge / 2
        }
        if (axis == this.Y_AXIS) {
            edge.rotateX(Math.PI / 2)
            edge.position.z += this.SIZE.lengthEdge / 2
        }
        else if (axis == this.Z_AXIS) {
            edge.rotateZ(Math.PI / 2)
            edge.position.x += this.SIZE.lengthEdge / 2
        }
    
        edge.hasError = {'X': false, 'Z': false};
    
        let index = this.getIndexQubit(axis, x, y, z)
    
        edge.index = index;
        this.qubits[index] = edge;
    
        this.scene.add(edge);
    }

    buildTriangle(axis, x, y, z) {
        const L = this.SIZE.lengthEdge / 4
    
        const geometry = new THREE.BufferGeometry();
    
        if (axis == 0) {
            if ((x + y + z) % 2 == 0) {
                var vertices = new Float32Array([
                    x+L,   y,   z,
                    x,   y+L, z,
                    x,   y,   z+L
                ]);
            }
            else {
                var vertices = new Float32Array([
                    x-L,   y,   z,
                    x,   y-L, z,
                    x,   y,   z-L
                ]);
            }
        }
    
        else if (axis == 1) {
            if ((x + y + z) % 2 == 0) {
                var vertices = new Float32Array([
                    x+L,   y,   z,
                    x,   y-L, z,
                    x,   y,   z-L
                ]);
            }
            else {
                var vertices = new Float32Array([
                    x-L,   y,   z,
                    x,   y+L, z,
                    x,   y,   z+L
                ]);
            }
        }
    
        else if (axis == 2) {
            if ((x + y + z) % 2 == 0) {
                var vertices = new Float32Array([
                    x-L,   y,   z,
                    x,   y+L, z,
                    x,   y,   z-L
                ]);
            }
            else {
                var vertices = new Float32Array([
                    x+L,   y,   z,
                    x,   y-L, z,
                    x,   y,   z+L
                ]);
            }
        }
    
        else if (axis == 3) {
            if ((x + y + z) % 2 == 0) {
                var vertices = new Float32Array([
                    x-L,   y,   z,
                    x,   y-L, z,
                    x,   y,   z+L
                ]);
            }
            else {
                var vertices = new Float32Array([
                    x+L,   y,   z,
                    x,   y+L, z,
                    x,   y,   z-L
                ]);
            }
        }
    
        geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3) );
    
        const material = new THREE.MeshBasicMaterial({color: this.COLOR.deactivatedTriangle, opacity: this.currentOpacity, transparent: true, side: THREE.DoubleSide});
        const triangle = new THREE.Mesh(geometry, material);
    
        var geo = new THREE.EdgesGeometry(triangle.geometry);
        var mat = new THREE.LineBasicMaterial({color: 0x000000, linewidth: 1, opacity: this.currentOpacity, transparent: true});
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
        if ((x + y + z) % 2 == 1) {
            const L = this.SIZE.lengthEdge - 0.3
            const geometry = new THREE.BoxBufferGeometry(L, L, L);
            const material = new THREE.MeshToonMaterial({color: this.COLOR.deactivatedCube, opacity: this.currentOpacity, transparent: true});
            const cube = new THREE.Mesh(geometry, material);
    
            var geo = new THREE.EdgesGeometry( cube.geometry );
            var mat = new THREE.LineBasicMaterial( { color: 0x000000, linewidth: 2, opacity: this.currentOpacity, transparent: true } );
            var wireframe = new THREE.LineSegments( geo, mat );
            wireframe.renderOrder = 1; // make sure wireframes are rendered 2nd
            cube.add(wireframe);
    
            cube.position.x = x + this.SIZE.lengthEdge / 2;
            cube.position.y = y + this.SIZE.lengthEdge / 2;
            cube.position.z = z + this.SIZE.lengthEdge / 2;
    
            let index = this.getIndexCube(x, y, z);
            cube.index = index;
            cube.isActivated = false;
            this.cubes[index] = cube;
    
            this.scene.add(cube);
        }
    }


    build() {
        for(let x=0; x < this.L; x++) {
            for(let y=0; y < this.L; y++) {
                for(let z=0; z < this.L; z++) {
                    for (let axis=0; axis < 3; axis++) {
                        this.buildEdge(axis, x, y, z);
                    }
                    for (let axis=0; axis < 4; axis++) {
                        this.buildTriangle(axis, x, y, z);
                    }
                    this.buildCube(x, y, z);
                }
            }
        }
    }
}