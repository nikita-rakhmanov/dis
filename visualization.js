// ==================== Configuration ====================
const CONFIG = {
    websocketUrl: 'ws://localhost:8765',
    reconnectInterval: 3000,
    maxTrailLength: 100,
    particleCount: 500,
    rotationSpeed: 0.003,
    noteScale: 0.8,  // Larger spheres for more dramatic effect
    spaceScale: {
        pitch: 2.5,   // For 1 octave (12 notes) → ~(-15 to 15)
        duration: 20, // Duration (0-2s) → (0 to 40)
        step: 15      // Z-axis depth for timing
    }
};

// ==================== Scene Setup ====================
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x000510);
scene.fog = new THREE.FogExp2(0x000510, 0.015);

const camera = new THREE.PerspectiveCamera(
    75,
    window.innerWidth / window.innerHeight,
    0.1,
    1000
);
camera.position.set(0, 25, 20);  // Higher and closer to see notes better
camera.lookAt(0, 15, -30);  // Look toward negative Z where notes appear

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
document.getElementById('canvas-container').appendChild(renderer.domElement);

// ==================== Lighting ====================
const ambientLight = new THREE.AmbientLight(0x404040, 1);
scene.add(ambientLight);

const pointLight1 = new THREE.PointLight(0x00ffff, 2, 100);
pointLight1.position.set(0, 20, 20);
scene.add(pointLight1);

const pointLight2 = new THREE.PointLight(0xff00ff, 1.5, 100);
pointLight2.position.set(-20, 10, -20);
scene.add(pointLight2);

// ==================== Particle System ====================
const particleGeometry = new THREE.BufferGeometry();
const particleCount = CONFIG.particleCount;
const particlePositions = new Float32Array(particleCount * 3);
const particleVelocities = [];

for (let i = 0; i < particleCount; i++) {
    particlePositions[i * 3] = (Math.random() - 0.5) * 100;
    particlePositions[i * 3 + 1] = (Math.random() - 0.5) * 100;
    particlePositions[i * 3 + 2] = (Math.random() - 0.5) * 100;

    particleVelocities.push({
        x: (Math.random() - 0.5) * 0.02,
        y: (Math.random() - 0.5) * 0.02,
        z: (Math.random() - 0.5) * 0.02
    });
}

particleGeometry.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));

const particleMaterial = new THREE.PointsMaterial({
    color: 0x4488ff,
    size: 0.2,
    transparent: true,
    opacity: 0.6,
    blending: THREE.AdditiveBlending
});

const particleSystem = new THREE.Points(particleGeometry, particleMaterial);
scene.add(particleSystem);

// ==================== Note Visualization ====================
const notes = [];
const noteGroup = new THREE.Group();
scene.add(noteGroup);

function midiToPosition(pitch, step, duration) {
    return new THREE.Vector3(
        (pitch - 64) * CONFIG.spaceScale.pitch,  // Center around middle C (64)
        duration * CONFIG.spaceScale.duration,
        -step * CONFIG.spaceScale.step
    );
}

function velocityToColor(velocity) {
    // Map velocity (0-127) to color gradient (red -> yellow -> green -> cyan -> blue)
    const normalized = velocity / 127;
    const hue = normalized * 0.7; // 0 (red) to 0.7 (blue)
    return new THREE.Color().setHSL(hue, 1.0, 0.5);
}

function addNote(noteData) {
    const position = midiToPosition(noteData.pitch, noteData.step, noteData.duration);
    const color = velocityToColor(noteData.velocity);

    // Size varies with velocity for dramatic effect
    const sizeMultiplier = 0.7 + (noteData.velocity / 127) * 0.6; // 0.7 to 1.3
    const noteSize = CONFIG.noteScale * sizeMultiplier;

    // Create note sphere
    const geometry = new THREE.SphereGeometry(noteSize, 32, 32);
    const material = new THREE.MeshPhongMaterial({
        color: color,
        emissive: color,
        emissiveIntensity: 0.8,  // Brighter emission
        shininess: 100
    });

    const noteSphere = new THREE.Mesh(geometry, material);
    noteSphere.position.copy(position);

    // Add larger, brighter glow effect
    const glowGeometry = new THREE.SphereGeometry(noteSize * 2.5, 32, 32);
    const glowMaterial = new THREE.MeshBasicMaterial({
        color: color,
        transparent: true,
        opacity: 0.5,
        blending: THREE.AdditiveBlending
    });
    const glow = new THREE.Mesh(glowGeometry, glowMaterial);
    noteSphere.add(glow);

    // Add outer rim glow
    const outerGlowGeometry = new THREE.SphereGeometry(noteSize * 4, 32, 32);
    const outerGlowMaterial = new THREE.MeshBasicMaterial({
        color: color,
        transparent: true,
        opacity: 0.15,
        blending: THREE.AdditiveBlending
    });
    const outerGlow = new THREE.Mesh(outerGlowGeometry, outerGlowMaterial);
    noteSphere.add(outerGlow);

    noteGroup.add(noteSphere);

    // Draw thicker, more visible line to previous note
    if (notes.length > 0) {
        const prevNote = notes[notes.length - 1];

        // Create tube geometry for thicker line
        const curve = new THREE.LineCurve3(prevNote.position.clone(), position);
        const tubeGeometry = new THREE.TubeGeometry(curve, 20, 0.1, 8, false);
        const tubeMaterial = new THREE.MeshBasicMaterial({
            color: color,
            transparent: true,
            opacity: 0.7,
            blending: THREE.AdditiveBlending
        });
        const tube = new THREE.Mesh(tubeGeometry, tubeMaterial);
        noteGroup.add(tube);

        notes[notes.length - 1].line = tube;
        notes[notes.length - 1].lineOpacity = 0.7;
    }

    notes.push({
        mesh: noteSphere,
        position: position,
        data: noteData,
        creationTime: Date.now(),
        baseScale: sizeMultiplier,
        glow: glow,
        outerGlow: outerGlow
    });

    // Manage trail length
    const maxLength = parseInt(document.getElementById('trail-length').value);
    while (notes.length > maxLength) {
        const oldNote = notes.shift();
        noteGroup.remove(oldNote.mesh);
        if (oldNote.line) {
            noteGroup.remove(oldNote.line);
        }
    }

    // Update UI
    document.getElementById('note-count').textContent = notes.length;
    document.getElementById('latest-note').innerHTML = `
        <span>${noteData.note_name}</span> |
        Pitch: ${noteData.pitch} |
        Duration: ${noteData.duration.toFixed(3)}s<br>
        Velocity: ${noteData.velocity} |
        Step: ${noteData.step.toFixed(3)}s
    `;
}

function clearVisualization() {
    while (notes.length > 0) {
        const note = notes.shift();
        noteGroup.remove(note.mesh);
        if (note.line) {
            noteGroup.remove(note.line);
        }
    }
    document.getElementById('note-count').textContent = '0';
}

// ==================== WebSocket Connection ====================
let ws = null;
let reconnectTimeout = null;

function connectWebSocket() {
    try {
        ws = new WebSocket(CONFIG.websocketUrl);

        ws.onopen = () => {
            console.log('WebSocket connected');
            document.getElementById('status-indicator').className = 'status-indicator connected';
            document.getElementById('status-text').textContent = 'Connected';
            if (reconnectTimeout) {
                clearTimeout(reconnectTimeout);
                reconnectTimeout = null;
            }
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'note') {
                    addNote(data);
                }
            } catch (e) {
                console.error('Error parsing message:', e);
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        ws.onclose = () => {
            console.log('WebSocket disconnected');
            document.getElementById('status-indicator').className = 'status-indicator disconnected';
            document.getElementById('status-text').textContent = 'Disconnected - Reconnecting...';

            // Attempt to reconnect
            reconnectTimeout = setTimeout(() => {
                console.log('Attempting to reconnect...');
                connectWebSocket();
            }, CONFIG.reconnectInterval);
        };
    } catch (e) {
        console.error('Failed to create WebSocket:', e);
        document.getElementById('status-text').textContent = 'Connection failed - Retrying...';
        reconnectTimeout = setTimeout(connectWebSocket, CONFIG.reconnectInterval);
    }
}

// ==================== Animation Loop ====================
let lastTime = Date.now();
let frames = 0;
let fpsUpdateTime = Date.now();

function animate() {
    requestAnimationFrame(animate);

    const currentTime = Date.now();
    const deltaTime = currentTime - lastTime;
    lastTime = currentTime;

    // Update FPS counter
    frames++;
    if (currentTime - fpsUpdateTime > 1000) {
        document.getElementById('fps').textContent = frames;
        frames = 0;
        fpsUpdateTime = currentTime;
    }

    // Rotate scene
    const rotationSpeed = parseFloat(document.getElementById('rotation-speed').value) / 10000;
    noteGroup.rotation.y += rotationSpeed;

    // Orbital camera movement around the note space
    const cameraDistance = 50;
    const cameraSpeed = currentTime * 0.0001;
    const orbitCenterZ = -30;  // Orbit around where notes appear
    camera.position.x = Math.sin(cameraSpeed) * cameraDistance;
    camera.position.z = orbitCenterZ + Math.cos(cameraSpeed) * cameraDistance;
    camera.position.y = 25 + Math.sin(cameraSpeed * 0.5) * 10;
    camera.lookAt(0, 15, orbitCenterZ);  // Always look at note space center

    // Animate notes (pulsing and fading)
    notes.forEach((note, index) => {
        const age = currentTime - note.creationTime;
        const maxAge = 30000; // 30 seconds

        // Pulsing effect - more dramatic for newer notes
        const pulseSpeed = 0.003;
        const pulseAmount = Math.max(0, 1 - age / 10000) * 0.3; // Fade pulse over time
        const pulse = 1 + Math.sin(currentTime * pulseSpeed + index) * pulseAmount;
        note.mesh.scale.set(pulse, pulse, pulse);

        // Fade out old notes
        const fadeStart = maxAge * 0.6;
        if (age > fadeStart) {
            const fadeProgress = (age - fadeStart) / (maxAge - fadeStart);
            const opacity = 1 - fadeProgress;

            // Fade sphere material
            note.mesh.material.opacity = opacity;
            note.mesh.material.transparent = true;

            // Fade glows
            if (note.glow) note.glow.material.opacity = 0.5 * opacity;
            if (note.outerGlow) note.outerGlow.material.opacity = 0.15 * opacity;
        }

        // Fade out connecting lines gradually
        if (note.line && note.lineOpacity !== undefined) {
            const lineFadeSpeed = 0.015;
            note.lineOpacity = Math.max(0, note.lineOpacity - lineFadeSpeed * deltaTime / 1000);
            note.line.material.opacity = note.lineOpacity;
        }

        // Gentle rotation of each sphere
        note.mesh.rotation.y += 0.01;
        note.mesh.rotation.x += 0.005;
    });

    // Animate particles - more dramatic movement
    const positions = particleSystem.geometry.attributes.position.array;
    for (let i = 0; i < particleCount; i++) {
        positions[i * 3] += particleVelocities[i].x;
        positions[i * 3 + 1] += particleVelocities[i].y;
        positions[i * 3 + 2] += particleVelocities[i].z;

        // Boundary check - wrap around
        if (Math.abs(positions[i * 3]) > 50) particleVelocities[i].x *= -1;
        if (Math.abs(positions[i * 3 + 1]) > 50) particleVelocities[i].y *= -1;
        if (Math.abs(positions[i * 3 + 2]) > 50) particleVelocities[i].z *= -1;
    }
    particleSystem.geometry.attributes.position.needsUpdate = true;

    // Rotate particle system
    particleSystem.rotation.y += 0.0003;
    particleSystem.rotation.x += 0.0005;

    // DRAMATIC: More intense pulsing lights
    pointLight1.intensity = 3 + Math.sin(currentTime * 0.002) * 1.5;
    pointLight2.intensity = 2.5 + Math.cos(currentTime * 0.0025) * 1.5;

    // Move lights around
    pointLight1.position.x = Math.sin(currentTime * 0.0005) * 30;
    pointLight1.position.z = Math.cos(currentTime * 0.0005) * 30;

    renderer.render(scene, camera);
}

// ==================== Controls ====================
document.getElementById('particle-density').addEventListener('input', (e) => {
    const newCount = parseInt(e.target.value);
    document.getElementById('particle-count').textContent = newCount;
});

document.getElementById('clear-btn').addEventListener('click', clearVisualization);

// ==================== Responsive Canvas ====================
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

// ==================== Initialize ====================
document.getElementById('particle-count').textContent = particleCount;
connectWebSocket();
animate();

console.log('Music Visualization initialized');
console.log('Waiting for MIDI data from realtime_midi_generator.py...');
