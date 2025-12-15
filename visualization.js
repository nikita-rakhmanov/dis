// ==================== Configuration ====================
const CONFIG = {
    // WebSocket
    websocketUrl: 'ws://localhost:8765',
    reconnectInterval: 3000,

    // Display
    fontSize: 14,
    fontFamily: '"Courier New", Consolas, monospace',

    // Notes (ASCII Spheres)
    noteChars: ['@', '#', '%', '&', '*', 'O', '●', '◉', '○', '◎'],
    sphereLayers: [
        { chars: ['◉', '●', '@'], radiusRatio: 0.3, density: 8 },
        { chars: ['O', '#', '%'], radiusRatio: 0.6, density: 12 },
        { chars: ['○', '*', '·'], radiusRatio: 1.0, density: 16 },
    ],
    maxNotes: 100,
    notePulseSpeed: 0.004,
    notePulseAmount: 0.25,
    noteBaseRadius: 25,
    noteFadeTime: 30000,

    // Trails
    trailChars: ['●', '•', '·', '.'],
    maxTrailLength: 100,
    trailFadeSpeed: 0.02,

    // Particles
    particleChars: ['✦', '✧', '*', '·', '+', '×', '○', '◦', '.'],
    particleCount: 150,
    particleSpeedMin: 0.2,
    particleSpeedMax: 0.6,

    // Visual
    backgroundColor: '#000510',
    glowEnabled: true,
    glowBlur: 6,

    // Space mapping
    spaceScale: {
        pitch: 25,
        duration: 80,
        step: 0.5
    },

    // Camera settings
    orbitEnabled: true,
    orbitSpeed: 0.0005,
    orbitAmplitude: 60,
    orbitYAmplitude: 30,

    // Zoom
    zoomLevel: 1.3,              // Camera zoom (1 = normal, >1 = zoomed in)

    // Note-tracking camera
    trackingEnabled: true,
    trackingSmoothing: 0.03,
    trackingRecentNotes: 5,
    trackingCenterX: 0.5,
    trackingCenterY: 0.5,
    trackingStrength: 0.7,

    // Reactive shake on big pitch jumps
    shakeEnabled: false,
    shakePitchThreshold: 25,     // Minimum pitch difference to trigger shake
    shakeIntensity: 15,          // Max shake amount in pixels
    shakeDecay: 0.85,            // How fast shake fades (0.8 = fast, 0.95 = slow)

    // ==================== NEW: Starfield Background ====================
    // DISABLED: User preferred original background
    starfieldEnabled: false,
    starfieldLayers: [
        { count: 100, speed: 0.1, size: 1, opacity: 0.3 },   // Distant stars
        { count: 60, speed: 0.3, size: 1.5, opacity: 0.5 },  // Mid stars
        { count: 30, speed: 0.6, size: 2, opacity: 0.8 }     // Close stars
    ],
    starfieldReactivity: 0.3,    // How much stars react to music (0-1)

    // Synthwave grid - TRON style blue
    synthwaveGridEnabled: true,
    synthwaveGridLines: 20,
    synthwaveGridSpeed: 0.5,
    synthwaveGridColor: '#00d4ff',      // Tron blue (was magenta)
    synthwaveGridOpacity: 0.25,         // Increased base opacity
    synthwaveGridPulseIntensity: 0.6,   // How bright the pulse gets (0-1)

    // ==================== NEW: Hand Tracking Overlay ====================
    handTrackingEnabled: true,
    leftHandColor: '#00ffff',    // Cyan for left hand (effects)
    rightHandColor: '#ff8800',   // Orange for right hand (tempo)
    handIndicatorSize: 40,
    handLabelOffset: 60,
    handTrailLength: 10,
    handSmoothingFactor: 0.15,

    // ==================== NEW: Start Gesture Requirement ====================
    startGestureRequired: true,
    startGestureCenterMin: 0.25,  // Left boundary of "center" area
    startGestureCenterMax: 0.75,  // Right boundary of "center" area
    startGestureYMin: 0.2,
    startGestureYMax: 0.8,
    startGestureHoldTime: 1500    // ms both hands must hold peace sign
};

// ==================== Canvas Setup ====================
const canvas = document.createElement('canvas');
const ctx = canvas.getContext('2d', { alpha: false });
document.getElementById('canvas-container').appendChild(canvas);

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}
resizeCanvas();
window.addEventListener('resize', resizeCanvas);

// ==================== Precomputed Data ====================
function generateSpherePattern() {
    const patterns = [];
    for (let layerIdx = 0; layerIdx < CONFIG.sphereLayers.length; layerIdx++) {
        const layer = CONFIG.sphereLayers[layerIdx];
        const layerPattern = [];
        for (let i = 0; i < layer.density; i++) {
            layerPattern.push({
                angleOffset: (i / layer.density) * Math.PI * 2,
                distanceFactor: 0.5 + Math.random() * 0.5,
                char: layer.chars[i % layer.chars.length]
            });
        }
        patterns.push(layerPattern);
    }
    return patterns;
}

const spherePatterns = [];
for (let i = 0; i < 20; i++) {
    spherePatterns.push(generateSpherePattern());
}

// ==================== Color Utilities ====================
function velocityToColor(velocity) {
    const normalized = velocity / 127;
    const hue = normalized * 252; // 0 (red) to 252 (blue)
    return `hsl(${hue}, 100%, 60%)`;
}

// ==================== Optimized ASCII Renderer ====================
class ASCIIRenderer {
    constructor(context) {
        this.ctx = context;
        this.baseFont = `${CONFIG.fontSize}px ${CONFIG.fontFamily}`;
    }

    clear() {
        this.ctx.fillStyle = CONFIG.backgroundColor;
        this.ctx.fillRect(0, 0, canvas.width, canvas.height);
    }

    drawChar(char, x, y, color, scale = 1, opacity = 1, glow = false) {
        if (opacity < 0.05) return;

        this.ctx.globalAlpha = opacity;
        this.ctx.fillStyle = color;

        if (glow && CONFIG.glowEnabled) {
            this.ctx.shadowColor = color;
            this.ctx.shadowBlur = CONFIG.glowBlur;
        } else {
            this.ctx.shadowBlur = 0;
        }

        if (scale !== 1) {
            this.ctx.font = `${CONFIG.fontSize * scale}px ${CONFIG.fontFamily}`;
        } else {
            this.ctx.font = this.baseFont;
        }

        this.ctx.fillText(char, x, y);
    }

    drawSphere(centerX, centerY, baseRadius, color, pulsePhase, opacity = 1, patternIdx = 0) {
        if (opacity < 0.05) return;

        const pulse = 1 + Math.sin(pulsePhase) * CONFIG.notePulseAmount;
        const radius = baseRadius * pulse;
        const pattern = spherePatterns[patternIdx % spherePatterns.length];

        this.ctx.fillStyle = color;
        this.ctx.font = this.baseFont;

        for (let layerIdx = CONFIG.sphereLayers.length - 1; layerIdx >= 0; layerIdx--) {
            const layer = CONFIG.sphereLayers[layerIdx];
            const layerRadius = radius * layer.radiusRatio;
            const layerPattern = pattern[layerIdx];
            const charOpacity = opacity * (1 - layerIdx * 0.2);

            if (charOpacity < 0.05) continue;

            this.ctx.globalAlpha = charOpacity;

            if (layerIdx === 0 && CONFIG.glowEnabled) {
                this.ctx.shadowColor = color;
                this.ctx.shadowBlur = CONFIG.glowBlur;
            } else {
                this.ctx.shadowBlur = 0;
            }

            for (const point of layerPattern) {
                const angle = point.angleOffset + pulsePhase * 0.3;
                const dist = layerRadius * point.distanceFactor;
                const x = centerX + Math.cos(angle) * dist;
                const y = centerY + Math.sin(angle) * dist;
                this.ctx.fillText(point.char, x, y);
            }
        }

        if (CONFIG.glowEnabled) {
            this.ctx.shadowColor = color;
            this.ctx.shadowBlur = CONFIG.glowBlur * 1.5;
        }
        this.ctx.globalAlpha = opacity;
        this.ctx.font = `${CONFIG.fontSize * 1.5}px ${CONFIG.fontFamily}`;
        this.ctx.fillText(CONFIG.noteChars[0], centerX, centerY);
        this.ctx.shadowBlur = 0;
    }

    drawTrail(x1, y1, x2, y2, color, opacity) {
        if (opacity < 0.05) return;

        const dx = x2 - x1;
        const dy = y2 - y1;
        const distance = Math.sqrt(dx * dx + dy * dy);
        const steps = Math.max(3, Math.floor(distance / 20));

        this.ctx.fillStyle = color;
        this.ctx.font = this.baseFont;
        this.ctx.shadowBlur = 0;

        for (let i = 0; i <= steps; i++) {
            const t = i / steps;
            const x = x1 + dx * t;
            const y = y1 + dy * t;
            const charIdx = Math.min(Math.floor(t * CONFIG.trailChars.length), CONFIG.trailChars.length - 1);
            const charOpacity = opacity * (0.4 + 0.6 * (1 - t));

            this.ctx.globalAlpha = charOpacity;
            this.ctx.fillText(CONFIG.trailChars[charIdx], x, y);
        }
    }

    resetState() {
        this.ctx.globalAlpha = 1;
        this.ctx.shadowBlur = 0;
        this.ctx.font = this.baseFont;
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
    }
}

const renderer = new ASCIIRenderer(ctx);

// ==================== Note Class ====================
class Note {
    constructor(noteData, index) {
        this.data = noteData;
        this.index = index;
        this.creationTime = Date.now();
        this.baseX = 0;
        this.baseY = 0;
        this.x = 0;
        this.y = 0;
        this.color = velocityToColor(noteData.velocity);
        this.patternIdx = index % spherePatterns.length;

        this.baseRadius = CONFIG.noteBaseRadius * (0.6 + (noteData.velocity / 127) * 0.6);
        this.depth = Math.min(noteData.step / 10, 1);

        this.calculatePosition();
    }

    calculatePosition() {
        const padding = 100;
        const usableWidth = canvas.width - padding * 2;
        this.baseX = padding + (this.data.pitch / 127) * usableWidth;

        const usableHeight = canvas.height - padding * 2;
        const yProgress = (this.index % 20) / 20;
        this.baseY = padding + yProgress * usableHeight + (this.data.duration * 30);

        const pseudoRandom = Math.sin(this.data.pitch * 0.5 + this.index * 0.3) * 50;
        this.baseY += pseudoRandom;

        this.baseY = Math.max(padding, Math.min(canvas.height - padding, this.baseY));

        const depthScale = 0.6 + (1 - this.depth) * 0.4;
        this.baseRadius = CONFIG.noteBaseRadius * (0.5 + (this.data.velocity / 127) * 0.5) * depthScale;
    }

    update(time, orbitOffset, cameraOffset = { x: 0, y: 0 }) {
        const parallaxX = orbitOffset.x * (0.3 + (1 - this.depth) * 0.7);
        const parallaxY = orbitOffset.y * (0.3 + (1 - this.depth) * 0.7);

        this.x = this.baseX + parallaxX + cameraOffset.x;
        this.y = this.baseY + parallaxY + cameraOffset.y;

        if (this.needsRecalc) {
            this.calculatePosition();
            this.needsRecalc = false;
        }
    }

    getOpacity() {
        const age = Date.now() - this.creationTime;
        const fadeStart = CONFIG.noteFadeTime * 0.6;

        if (age > fadeStart) {
            return Math.max(0, 1 - (age - fadeStart) / (CONFIG.noteFadeTime - fadeStart));
        }
        return 1;
    }

    getPulsePhase(time) {
        return time * CONFIG.notePulseSpeed + this.index;
    }

    render(renderer, time) {
        const opacity = this.getOpacity();
        if (opacity <= 0) return false;

        renderer.drawSphere(this.x, this.y, this.baseRadius, this.color,
            this.getPulsePhase(time), opacity, this.patternIdx);
        return true;
    }
}

// ==================== Trail Class ====================
class Trail {
    constructor(note1, note2) {
        this.note1 = note1;
        this.note2 = note2;
        this.opacity = 0.8;
    }

    update(deltaTime) {
        this.opacity -= CONFIG.trailFadeSpeed * (deltaTime / 1000);
        return this.opacity > 0;
    }

    render(renderer) {
        if (this.opacity <= 0) return;
        const combinedOpacity = this.opacity * Math.min(this.note1.getOpacity(), this.note2.getOpacity());
        renderer.drawTrail(this.note1.x, this.note1.y, this.note2.x, this.note2.y,
            this.note1.color, combinedOpacity);
    }
}

// ==================== Chord Line Class (for polyphony) ====================
class ChordLine {
    constructor(melodyNote, harmonyNote) {
        this.melodyNote = melodyNote;
        this.harmonyNote = harmonyNote;
    }

    render(ctx) {
        const melodyOpacity = this.melodyNote.getOpacity();
        const harmonyOpacity = this.harmonyNote.getOpacity();
        const opacity = Math.min(melodyOpacity, harmonyOpacity) * 0.6;

        if (opacity <= 0) return false;

        // Draw glowing chord connection line
        ctx.save();
        ctx.globalAlpha = opacity;
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
        ctx.shadowColor = '#ffffff';
        ctx.shadowBlur = 8;

        ctx.beginPath();
        ctx.moveTo(this.melodyNote.x, this.melodyNote.y);
        ctx.lineTo(this.harmonyNote.x, this.harmonyNote.y);
        ctx.stroke();

        ctx.restore();
        return true;
    }
}

// ==================== Particle Class ====================
class Particle {
    constructor() {
        this.reset();
    }

    reset() {
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.vx = (Math.random() - 0.5) * CONFIG.particleSpeedMax;
        this.vy = (Math.random() - 0.5) * CONFIG.particleSpeedMax;
        this.char = CONFIG.particleChars[Math.floor(Math.random() * CONFIG.particleChars.length)];
        this.opacity = 0.2 + Math.random() * 0.4;
        this.hue = Math.random() * 360;
        this.twinkleSpeed = 0.001 + Math.random() * 0.002;
        this.twinklePhase = Math.random() * Math.PI * 2;
    }

    update(time) {
        this.x += this.vx;
        this.y += this.vy;

        if (this.x < 0) this.x = canvas.width;
        else if (this.x > canvas.width) this.x = 0;
        if (this.y < 0) this.y = canvas.height;
        else if (this.y > canvas.height) this.y = 0;

        this.currentOpacity = this.opacity * (0.5 + 0.5 * Math.sin(time * this.twinkleSpeed + this.twinklePhase));
    }
}

// ==================== Particle System ====================
class ParticleSystem {
    constructor(count) {
        this.particles = [];
        for (let i = 0; i < count; i++) {
            this.particles.push(new Particle());
        }
    }

    setCount(count) {
        while (this.particles.length < count) this.particles.push(new Particle());
        while (this.particles.length > count) this.particles.pop();
    }

    update(time) {
        for (const p of this.particles) p.update(time);
    }

    render(ctx, time) {
        ctx.shadowBlur = 0;
        ctx.font = `${CONFIG.fontSize}px ${CONFIG.fontFamily}`;

        for (const p of this.particles) {
            if (p.currentOpacity < 0.05) continue;
            ctx.globalAlpha = p.currentOpacity;
            ctx.fillStyle = `hsl(${p.hue}, 50%, 70%)`;
            ctx.fillText(p.char, p.x, p.y);
        }
    }
}

// ==================== NEW: Starfield Background ====================
class StarfieldBackground {
    constructor() {
        this.layers = [];
        this.musicIntensity = 0;
        this.initLayers();
    }

    initLayers() {
        this.layers = [];
        for (const layerConfig of CONFIG.starfieldLayers) {
            const stars = [];
            for (let i = 0; i < layerConfig.count; i++) {
                stars.push({
                    x: Math.random() * canvas.width,
                    y: Math.random() * canvas.height,
                    baseOpacity: layerConfig.opacity * (0.5 + Math.random() * 0.5),
                    twinklePhase: Math.random() * Math.PI * 2,
                    twinkleSpeed: 0.001 + Math.random() * 0.002
                });
            }
            this.layers.push({
                stars,
                config: layerConfig
            });
        }
    }

    setMusicIntensity(velocity) {
        // Smooth intensity transition
        const targetIntensity = velocity / 127;
        this.musicIntensity += (targetIntensity - this.musicIntensity) * 0.1;
    }

    update(time) {
        for (const layer of this.layers) {
            const speed = layer.config.speed * (1 + this.musicIntensity * CONFIG.starfieldReactivity);
            for (const star of layer.stars) {
                // Move stars slowly to the left for subtle motion
                star.x -= speed;
                if (star.x < 0) {
                    star.x = canvas.width;
                    star.y = Math.random() * canvas.height;
                }
            }
        }
    }

    render(ctx, time) {
        if (!CONFIG.starfieldEnabled) return;

        ctx.save();

        for (const layer of this.layers) {
            const intensityBoost = 1 + this.musicIntensity * CONFIG.starfieldReactivity;

            for (const star of layer.stars) {
                const twinkle = 0.5 + 0.5 * Math.sin(time * star.twinkleSpeed + star.twinklePhase);
                const opacity = star.baseOpacity * twinkle * intensityBoost;

                ctx.globalAlpha = Math.min(1, opacity);
                ctx.fillStyle = '#ffffff';
                ctx.beginPath();
                ctx.arc(star.x, star.y, layer.config.size, 0, Math.PI * 2);
                ctx.fill();
            }
        }

        ctx.restore();
    }
}

// ==================== NEW: Synthwave Grid ====================
class SynthwaveGrid {
    constructor() {
        this.gridOffset = 0;
        this.pulseIntensity = 0;
    }

    pulse(velocity) {
        // Set pulse to full intensity on note hit
        this.pulseIntensity = velocity / 127;
    }

    render(ctx, time) {
        if (!CONFIG.synthwaveGridEnabled) return;

        ctx.save();

        const gridHeight = canvas.height * 0.4;
        const startY = canvas.height - gridHeight;

        // Animate grid moving towards viewer
        this.gridOffset = (this.gridOffset + CONFIG.synthwaveGridSpeed) % 50;

        // Fade pulse more slowly for dramatic effect
        this.pulseIntensity *= 0.92;

        const baseOpacity = CONFIG.synthwaveGridOpacity;
        const pulseBoost = this.pulseIntensity * CONFIG.synthwaveGridPulseIntensity;
        const opacity = Math.min(1, baseOpacity + pulseBoost);

        // Enhanced: Add glow during pulse
        if (this.pulseIntensity > 0.1) {
            ctx.shadowColor = CONFIG.synthwaveGridColor;
            ctx.shadowBlur = 15 * this.pulseIntensity;
        }

        ctx.strokeStyle = CONFIG.synthwaveGridColor;
        // Thicker lines during pulse
        ctx.lineWidth = 1 + this.pulseIntensity * 2;

        // Horizontal lines (perspective)
        const numHLines = CONFIG.synthwaveGridLines;
        for (let i = 0; i <= numHLines; i++) {
            const progress = (i + this.gridOffset / 50) / numHLines;
            const y = startY + gridHeight * Math.pow(progress, 1.5);

            // Fade lines at top, but boost during pulse
            ctx.globalAlpha = opacity * progress * (1 + this.pulseIntensity);

            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(canvas.width, y);
            ctx.stroke();
        }

        // Vertical lines (converging perspective)
        ctx.globalAlpha = opacity;
        const vanishX = canvas.width / 2;
        const vanishY = startY;
        const numVLines = 15;

        for (let i = 0; i <= numVLines; i++) {
            const t = i / numVLines;
            const bottomX = t * canvas.width;

            ctx.beginPath();
            ctx.moveTo(vanishX, vanishY);
            ctx.lineTo(bottomX, canvas.height);
            ctx.stroke();
        }

        ctx.restore();
    }
}

// ==================== NEW: Hand Tracking Overlay ====================
class HandTrackingOverlay {
    constructor() {
        this.leftHand = null;
        this.rightHand = null;
        this.leftHandSmooth = { x: 0.3, y: 0.5 };
        this.rightHandSmooth = { x: 0.7, y: 0.5 };
        this.leftTrail = [];
        this.rightTrail = [];
    }

    update(handData) {
        if (handData.left_hand && handData.left_hand.visible) {
            this.leftHand = handData.left_hand;
            // Smooth position
            this.leftHandSmooth.x += (handData.left_hand.x - this.leftHandSmooth.x) * CONFIG.handSmoothingFactor;
            this.leftHandSmooth.y += (handData.left_hand.y - this.leftHandSmooth.y) * CONFIG.handSmoothingFactor;

            // Add to trail
            this.leftTrail.push({ x: this.leftHandSmooth.x, y: this.leftHandSmooth.y });
            if (this.leftTrail.length > CONFIG.handTrailLength) this.leftTrail.shift();
        } else {
            this.leftHand = null;
        }

        if (handData.right_hand && handData.right_hand.visible) {
            this.rightHand = handData.right_hand;
            this.rightHandSmooth.x += (handData.right_hand.x - this.rightHandSmooth.x) * CONFIG.handSmoothingFactor;
            this.rightHandSmooth.y += (handData.right_hand.y - this.rightHandSmooth.y) * CONFIG.handSmoothingFactor;

            this.rightTrail.push({ x: this.rightHandSmooth.x, y: this.rightHandSmooth.y });
            if (this.rightTrail.length > CONFIG.handTrailLength) this.rightTrail.shift();
        } else {
            this.rightHand = null;
        }
    }

    renderHand(ctx, hand, smoothPos, trail, color, label, values, isRight = false) {
        if (!hand) return;

        const x = smoothPos.x * canvas.width;
        const y = smoothPos.y * canvas.height;
        const size = CONFIG.handIndicatorSize;

        ctx.save();

        // Draw trail
        if (trail.length > 1) {
            ctx.strokeStyle = color;
            ctx.lineWidth = 3;
            ctx.globalAlpha = 0.3;
            ctx.beginPath();
            ctx.moveTo(trail[0].x * canvas.width, trail[0].y * canvas.height);
            for (let i = 1; i < trail.length; i++) {
                ctx.lineTo(trail[i].x * canvas.width, trail[i].y * canvas.height);
            }
            ctx.stroke();
        }

        // Draw hand indicator (pulsing circle)
        const pulse = 1 + 0.1 * Math.sin(Date.now() * 0.005);

        // Outer glow
        ctx.globalAlpha = 0.3;
        ctx.fillStyle = color;
        ctx.shadowColor = color;
        ctx.shadowBlur = 20;
        ctx.beginPath();
        ctx.arc(x, y, size * pulse * 1.2, 0, Math.PI * 2);
        ctx.fill();

        // Inner circle
        ctx.globalAlpha = 0.8;
        ctx.shadowBlur = 10;
        ctx.beginPath();
        ctx.arc(x, y, size * pulse * 0.6, 0, Math.PI * 2);
        ctx.fill();

        // Center dot
        ctx.globalAlpha = 1;
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.fill();

        // Draw hand icon (✋ for left, 🖐️ stylized for right)
        ctx.globalAlpha = 1;
        ctx.font = '24px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = '#ffffff';
        ctx.fillText(isRight ? '🖐️' : '✋', x, y);

        // Draw label and values
        ctx.shadowBlur = 0;
        ctx.font = 'bold 14px "Courier New", monospace';
        ctx.textAlign = isRight ? 'left' : 'right';

        const labelX = isRight ? x + CONFIG.handLabelOffset : x - CONFIG.handLabelOffset;
        let labelY = y - 30;

        // Hand label
        ctx.fillStyle = color;
        ctx.fillText(label, labelX, labelY);
        labelY += 20;

        // Control values
        ctx.font = '12px "Courier New", monospace';
        ctx.fillStyle = '#ffffff';
        for (const [key, value] of Object.entries(values)) {
            ctx.fillText(`${key}: ${value}`, labelX, labelY);
            labelY += 16;
        }

        ctx.restore();
    }

    render(ctx) {
        if (!CONFIG.handTrackingEnabled) return;

        // Left hand - effects control
        if (this.leftHand) {
            const values = {
                'Filter': this.leftHand.filter_cutoff || 0,
                'Reverb': this.leftHand.reverb || 0,
                'Gesture': this.leftHand.gesture || 'None'
            };
            this.renderHand(ctx, this.leftHand, this.leftHandSmooth, this.leftTrail,
                CONFIG.leftHandColor, 'LEFT HAND', values, false);
        }

        // Right hand - tempo control
        if (this.rightHand) {
            const speed = this.rightHand.tempo_speed || 1.0;
            const speedBar = '█'.repeat(Math.round(speed)) + '░'.repeat(Math.max(0, 4 - Math.round(speed)));
            const values = {
                'Speed': `${speed.toFixed(2)}x`,
                'Meter': speedBar
            };
            this.renderHand(ctx, this.rightHand, this.rightHandSmooth, this.rightTrail,
                CONFIG.rightHandColor, 'RIGHT HAND', values, true);
        }
    }
}

// ==================== NEW: Start Gesture Overlay ====================
class StartGestureOverlay {
    constructor() {
        this.isActive = CONFIG.startGestureRequired;
        this.hasStarted = false;
        this.holdStartTime = null;
        this.progress = 0;
        this.leftHandReady = false;
        this.rightHandReady = false;
    }

    isInCenterArea(x, y) {
        return x >= CONFIG.startGestureCenterMin &&
            x <= CONFIG.startGestureCenterMax &&
            y >= CONFIG.startGestureYMin &&
            y <= CONFIG.startGestureYMax;
    }

    update(handData) {
        if (!this.isActive || this.hasStarted) return;

        // Check left hand
        this.leftHandReady = false;
        if (handData.left_hand && handData.left_hand.visible) {
            const inCenter = this.isInCenterArea(handData.left_hand.x, handData.left_hand.y);
            const isPeace = handData.left_hand.gesture === 'Peace Sign';
            this.leftHandReady = inCenter && isPeace;
        }

        // Check right hand
        this.rightHandReady = false;
        if (handData.right_hand && handData.right_hand.visible) {
            const inCenter = this.isInCenterArea(handData.right_hand.x, handData.right_hand.y);
            const isPeace = handData.right_hand.gesture === 'Peace Sign';
            this.rightHandReady = inCenter && isPeace;
        }

        // Both hands ready?
        if (this.leftHandReady && this.rightHandReady) {
            if (!this.holdStartTime) {
                this.holdStartTime = Date.now();
            }

            const elapsed = Date.now() - this.holdStartTime;
            this.progress = Math.min(1, elapsed / CONFIG.startGestureHoldTime);

            if (this.progress >= 1) {
                this.hasStarted = true;
                this.isActive = false;
                console.log('Start gesture detected! Music generation can begin.');
            }
        } else {
            // Reset if either hand breaks the pose
            this.holdStartTime = null;
            this.progress = Math.max(0, this.progress - 0.05); // Fade out smoothly
        }
    }

    render(ctx) {
        if (!this.isActive || this.hasStarted) return;

        ctx.save();

        // Dim background overlay
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Draw center target area
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const areaWidth = canvas.width * (CONFIG.startGestureCenterMax - CONFIG.startGestureCenterMin);
        const areaHeight = canvas.height * (CONFIG.startGestureYMax - CONFIG.startGestureYMin);

        ctx.strokeStyle = '#00d4ff';
        ctx.lineWidth = 2;
        ctx.setLineDash([10, 10]);
        ctx.globalAlpha = 0.5;
        ctx.strokeRect(
            canvas.width * CONFIG.startGestureCenterMin,
            canvas.height * CONFIG.startGestureYMin,
            areaWidth,
            areaHeight
        );
        ctx.setLineDash([]);

        // Title
        ctx.globalAlpha = 1;
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 36px "Courier New", monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('READY TO START', centerX, centerY - 100);

        // Instructions
        ctx.font = '20px "Courier New", monospace';
        ctx.fillStyle = '#00d4ff';
        ctx.fillText('Position both hands in the center area', centerX, centerY - 40);
        ctx.fillText('and make a ✌️ PEACE SIGN with both hands', centerX, centerY);

        // Hand status indicators - smaller font, stacked vertically
        ctx.font = '14px "Courier New", monospace';

        // Left hand status
        ctx.fillStyle = this.leftHandReady ? '#00ff00' : '#ff4444';
        ctx.fillText(this.leftHandReady ? '[OK] Left Hand Ready' : '[X] Left Hand: Peace sign in center', centerX, centerY + 50);

        // Right hand status
        ctx.fillStyle = this.rightHandReady ? '#00ff00' : '#ff4444';
        ctx.fillText(this.rightHandReady ? '[OK] Right Hand Ready' : '[X] Right Hand: Peace sign in center', centerX, centerY + 70);

        // Progress bar
        if (this.progress > 0) {
            const barWidth = 400;
            const barHeight = 20;
            const barX = centerX - barWidth / 2;
            const barY = centerY + 120;

            // Background
            ctx.fillStyle = 'rgba(255, 255, 255, 0.2)';
            ctx.fillRect(barX, barY, barWidth, barHeight);

            // Progress
            ctx.fillStyle = '#00ff00';
            ctx.shadowColor = '#00ff00';
            ctx.shadowBlur = 10;
            ctx.fillRect(barX, barY, barWidth * this.progress, barHeight);

            // Label
            ctx.shadowBlur = 0;
            ctx.fillStyle = '#ffffff';
            ctx.font = '14px "Courier New", monospace';
            ctx.fillText(`Hold for ${((1 - this.progress) * CONFIG.startGestureHoldTime / 1000).toFixed(1)}s...`, centerX, barY + 45);
        }

        ctx.restore();
    }

    shouldBlockNotes() {
        return this.isActive && !this.hasStarted;
    }
}

const notes = [];
const trails = [];
const chordLines = [];  // For polyphony chord connections
const particleSystem = new ParticleSystem(CONFIG.particleCount);

// NEW: Background and overlay systems
const starfield = new StarfieldBackground();
const synthwaveGrid = new SynthwaveGrid();
const handOverlay = new HandTrackingOverlay();
const startGestureOverlay = new StartGestureOverlay();

let orbitOffset = { x: 0, y: 0 };

// Camera tracking state
let cameraOffset = { x: 0, y: 0 };
let targetCameraOffset = { x: 0, y: 0 };

// Shake state
let shakeAmount = 0;
let shakeOffset = { x: 0, y: 0 };
let lastNotePitch = null;

function addNote(noteData) {
    const melodyNote = new Note(noteData, notes.length);

    // Check for big pitch jump and trigger shake
    if (CONFIG.shakeEnabled && lastNotePitch !== null) {
        const pitchDiff = Math.abs(noteData.pitch - lastNotePitch);
        if (pitchDiff >= CONFIG.shakePitchThreshold) {
            shakeAmount = Math.min(pitchDiff / 127, 1) * CONFIG.shakeIntensity;
        }
    }
    lastNotePitch = noteData.pitch;

    if (notes.length > 0) {
        trails.push(new Trail(notes[notes.length - 1], melodyNote));
    }

    notes.push(melodyNote);

    // Handle polyphony - create harmony note if present
    let harmonyNote = null;
    if (noteData.harmony_pitch !== undefined && noteData.harmony_pitch !== null) {
        const harmonyData = {
            ...noteData,
            pitch: noteData.harmony_pitch,
            note_name: noteData.harmony_name || 'H',
            velocity: noteData.velocity * 0.85  // Slightly quieter harmony
        };
        harmonyNote = new Note(harmonyData, notes.length);
        notes.push(harmonyNote);

        // Create chord connection line
        chordLines.push(new ChordLine(melodyNote, harmonyNote));
    }

    const maxLength = parseInt(document.getElementById('trail-length').value);
    while (notes.length > maxLength) notes.shift();
    while (trails.length > maxLength) trails.shift();
    while (chordLines.length > maxLength / 2) chordLines.shift();

    document.getElementById('note-count').textContent = notes.length;

    // Show harmony info if present
    const harmonyInfo = harmonyNote ? ` + <span>${noteData.harmony_name}</span>` : '';
    document.getElementById('latest-note').innerHTML = `
        <span>${noteData.note_name}</span>${harmonyInfo} |
        Pitch: ${noteData.pitch}${harmonyNote ? '+' + noteData.harmony_pitch : ''} |
        Duration: ${noteData.duration.toFixed(3)}s<br>
        Velocity: ${noteData.velocity} |
        Step: ${noteData.step.toFixed(3)}s
    `;
}

function clearVisualization() {
    notes.length = 0;
    trails.length = 0;
    chordLines.length = 0;
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
                    // Block notes until start gesture is completed
                    if (!startGestureOverlay.shouldBlockNotes()) {
                        addNote(data);
                        // NEW: Update starfield and grid intensity
                        starfield.setMusicIntensity(data.velocity);
                        synthwaveGrid.pulse(data.velocity);
                    }
                }
                // NEW: Handle hand tracking data
                else if (data.type === 'hand_data') {
                    handOverlay.update(data);
                    // Update start gesture overlay
                    startGestureOverlay.update(data);
                }
            } catch (e) {
                console.error('Error parsing message:', e);
            }
        };

        ws.onerror = (error) => console.error('WebSocket error:', error);

        ws.onclose = () => {
            console.log('WebSocket disconnected');
            document.getElementById('status-indicator').className = 'status-indicator disconnected';
            document.getElementById('status-text').textContent = 'Disconnected - Reconnecting...';
            reconnectTimeout = setTimeout(connectWebSocket, CONFIG.reconnectInterval);
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

    frames++;
    if (currentTime - fpsUpdateTime > 1000) {
        document.getElementById('fps').textContent = frames;
        frames = 0;
        fpsUpdateTime = currentTime;
    }

    if (CONFIG.orbitEnabled) {
        const rotationSpeed = parseFloat(document.getElementById('rotation-speed').value) / 100;
        const orbitPhase = currentTime * CONFIG.orbitSpeed * rotationSpeed;

        orbitOffset.x = Math.sin(orbitPhase) * CONFIG.orbitAmplitude
            + Math.sin(orbitPhase * 1.5) * CONFIG.orbitAmplitude * 0.3;
        orbitOffset.y = Math.cos(orbitPhase * 0.7) * CONFIG.orbitYAmplitude
            + Math.sin(orbitPhase * 0.4) * CONFIG.orbitYAmplitude * 0.2;
    }

    // Note-tracking camera
    if (CONFIG.trackingEnabled && notes.length > 0) {
        // Calculate average position of recent notes
        const recentCount = Math.min(CONFIG.trackingRecentNotes, notes.length);
        let avgX = 0, avgY = 0;
        for (let i = notes.length - recentCount; i < notes.length; i++) {
            avgX += notes[i].baseX;
            avgY += notes[i].baseY;
        }
        avgX /= recentCount;
        avgY /= recentCount;

        // Calculate offset to center the notes
        const screenCenterX = canvas.width * CONFIG.trackingCenterX;
        const screenCenterY = canvas.height * CONFIG.trackingCenterY;
        targetCameraOffset.x = (screenCenterX - avgX) * CONFIG.trackingStrength;
        targetCameraOffset.y = (screenCenterY - avgY) * CONFIG.trackingStrength;

        // Smooth interpolation
        cameraOffset.x += (targetCameraOffset.x - cameraOffset.x) * CONFIG.trackingSmoothing;
        cameraOffset.y += (targetCameraOffset.y - cameraOffset.y) * CONFIG.trackingSmoothing;
    }

    // Update shake (decay over time)
    if (shakeAmount > 0.1) {
        shakeOffset.x = (Math.random() - 0.5) * shakeAmount * 2;
        shakeOffset.y = (Math.random() - 0.5) * shakeAmount * 2;
        shakeAmount *= CONFIG.shakeDecay;
    } else {
        shakeOffset.x = 0;
        shakeOffset.y = 0;
        shakeAmount = 0;
    }

    renderer.clear();
    renderer.resetState();

    // NEW: Render starfield background BEFORE zoom transform (fixed background)
    starfield.update(currentTime);
    starfield.render(ctx, currentTime);

    // NEW: Render synthwave grid
    synthwaveGrid.render(ctx, currentTime);

    // Apply zoom transform
    ctx.save();
    const zoomCenterX = canvas.width / 2;
    const zoomCenterY = canvas.height / 2;
    ctx.translate(zoomCenterX + shakeOffset.x, zoomCenterY + shakeOffset.y);
    ctx.scale(CONFIG.zoomLevel, CONFIG.zoomLevel);
    ctx.translate(-zoomCenterX, -zoomCenterY);

    particleSystem.update(currentTime);
    particleSystem.render(ctx, currentTime);

    for (const note of notes) {
        note.update(currentTime, orbitOffset, cameraOffset);
    }

    for (let i = trails.length - 1; i >= 0; i--) {
        if (!trails[i].update(deltaTime)) {
            trails.splice(i, 1);
        } else {
            trails[i].render(renderer);
        }
    }

    // Render chord lines (polyphony connections)
    for (let i = chordLines.length - 1; i >= 0; i--) {
        if (!chordLines[i].render(ctx)) {
            chordLines.splice(i, 1);
        }
    }

    for (let i = notes.length - 1; i >= 0; i--) {
        if (!notes[i].render(renderer, currentTime)) {
            notes.splice(i, 1);
        }
    }

    // Restore context after zoom transform
    ctx.restore();

    // NEW: Render hand tracking overlay AFTER restore (so it's not zoomed/transformed)
    // Reset context state to ensure hands are visible
    ctx.globalAlpha = 1;
    ctx.shadowBlur = 0;
    handOverlay.render(ctx);

    // NEW: Render start gesture overlay on top of everything
    startGestureOverlay.render(ctx);
}

// ==================== Controls ====================
document.getElementById('particle-density').addEventListener('input', (e) => {
    const newCount = parseInt(e.target.value);
    particleSystem.setCount(newCount);
    document.getElementById('particle-count').textContent = newCount;
});

document.getElementById('clear-btn').addEventListener('click', clearVisualization);

window.addEventListener('resize', () => {
    resizeCanvas();
    for (const note of notes) note.needsRecalc = true;
});

// ==================== Initialize ====================
document.getElementById('particle-count').textContent = CONFIG.particleCount;
connectWebSocket();
animate();

console.log('ASCII Music Visualization initialized');
console.log('Waiting for MIDI data from realtime_midi_generator.py...');
