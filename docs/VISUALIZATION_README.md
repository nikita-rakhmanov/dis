# 🎵 Generative Music 3D Visualization

An interactive real-time 3D visualization for the RNN-based generative music system. Watch your AI-generated music come alive as flowing vectors in 3D space with particle effects and dynamic lighting.

![Visualization Preview](https://img.shields.io/badge/Three.js-Powered-blue) ![WebSocket](https://img.shields.io/badge/WebSocket-Real--time-green) ![Python](https://img.shields.io/badge/Python-3.8+-yellow)

## ✨ Features

- **Real-time 3D Visualization**: MIDI notes rendered as spheres with connecting traces in 3D space
- **WebSocket Streaming**: Live data feed from the music generator
- **Particle System**: Ambient floating particles for atmospheric effect
- **Auto-rotation**: Continuously rotating view of the musical space
- **Interactive Controls**:
  - Adjust rotation speed
  - Control trail length (how many notes to display)
  - Modify particle density
  - Clear visualization on demand
- **Visual Mapping**:
  - **X-axis**: MIDI Pitch (0-127) - centered around middle C
  - **Y-axis**: Note Duration (seconds)
  - **Z-axis**: Step/Timing between notes
  - **Color**: Note Velocity (loudness) - red to blue gradient
- **Modular Design**: Ready for future UI integration and customization

## 🚀 Quick Start

### 1. Install Dependencies

First, install the new WebSocket dependency:

```bash
pip install -r requirements.txt
```

Or just install websockets:

```bash
pip install websockets>=11.0.0
```

### 2. Start the Music Generator

Run the real-time generator with visualization enabled (default):

```bash
python realtime_midi_generator.py
```

The generator will:
- Load the trained model
- Start a WebSocket server on port 8765
- Begin generating and playing MIDI notes
- Broadcast note data to visualization clients

### 3. Open the Visualization

Open `visualization.html` in your web browser:

```bash
# Option 1: Direct file open
open visualization.html  # macOS
xdg-open visualization.html  # Linux
start visualization.html  # Windows

# Option 2: Or just drag the file into your browser
```

The visualization will automatically connect to the WebSocket server and start displaying notes in 3D space!

## 🎮 Controls & Interface

### Info Panel (Top Left)
- **Connection Status**: Shows if connected to the generator
- **Latest Note**: Displays the most recent note's data
- **Statistics**:
  - Total notes currently visible
  - Particle count
  - FPS counter

### Control Panel (Bottom Left)
- **Rotation Speed**: Adjust the auto-rotation speed (0-100)
- **Trail Length**: Number of notes to keep visible (10-200)
- **Particle Density**: Number of ambient particles (100-2000)
- **Clear Button**: Remove all notes and start fresh

### Legend (Top Right)
- Shows the 3D axis mapping
- Color gradient explanation

## 🛠️ Advanced Usage

### Custom WebSocket Port

If port 8765 is in use, specify a different port:

```bash
# Generator
python realtime_midi_generator.py --ws-port 9000
```

Then update `visualization.html` line 186:
```javascript
websocketUrl: 'ws://localhost:9000',
```

### Disable Visualization

If you only want MIDI output without the WebSocket server:

```bash
python realtime_midi_generator.py --no-visualization
```

### Full Command Options

```bash
python realtime_midi_generator.py \
  --model music_rnn_model.keras \
  --seed seed_sequence.npy \
  --temperature 2.0 \
  --velocity 80 \
  --num-notes 500 \
  --ws-port 8765 \
  --port "Your MIDI Port Name"
```

## 🎨 Visualization Details

### 3D Space Mapping

The visualization maps MIDI parameters to 3D coordinates:

```
MIDI Data:                      3D Space:
-----------                     ----------
Pitch (0-127)         →         X-axis (-10 to +10, centered at middle C)
Duration (0-2s)       →         Y-axis (0 to 20 units)
Step/Timing           →         Z-axis (depth, flowing forward)
Velocity (0-127)      →         Color (red → yellow → green → cyan → blue)
```

### Visual Elements

1. **Note Spheres**:
   - Each note is a glowing sphere
   - Inner solid sphere + outer transparent glow
   - Color based on velocity

2. **Connection Traces**:
   - Lines connecting consecutive notes
   - Shows the melodic flow through space
   - Same color as the target note

3. **Particle System**:
   - 500+ ambient particles (configurable)
   - Slow random movement with boundary wrapping
   - Creates atmospheric depth

4. **Dynamic Lighting**:
   - Cyan and magenta point lights
   - Pulsing intensity synchronized to time
   - Creates dramatic shadows and highlights

5. **Auto-rotation**:
   - Smooth Y-axis rotation
   - Configurable speed via UI
   - Provides 360° view of the musical structure

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│  realtime_midi_generator.py             │
│  - Loads RNN model                       │
│  - Generates MIDI notes                  │
│  - Sends to Ableton/DAW (MIDI)          │
│  - Broadcasts to visualization (WebSocket)│
└────────────────┬────────────────────────┘
                 │
                 │ WebSocket (port 8765)
                 │ JSON: {pitch, step, duration, velocity, ...}
                 │
┌────────────────▼────────────────────────┐
│  visualization.html                      │
│  - Three.js 3D scene                     │
│  - Receives note data                    │
│  - Maps to 3D coordinates                │
│  - Renders spheres, lines, particles     │
└──────────────────────────────────────────┘
```

### WebSocket Message Format

```json
{
  "type": "note",
  "pitch": 60,
  "step": 0.425,
  "duration": 0.315,
  "velocity": 80,
  "note_name": "C4",
  "timestamp": "2025-11-02T10:30:45.123456",
  "index": 42
}
```

## 🔧 Customization

### Modifying Visual Parameters

Edit `visualization.html` lines 186-197 to adjust:

```javascript
const CONFIG = {
    websocketUrl: 'ws://localhost:8765',
    reconnectInterval: 3000,        // WebSocket reconnect delay
    maxTrailLength: 100,            // Default trail length
    particleCount: 500,             // Number of particles
    rotationSpeed: 0.003,           // Base rotation speed
    noteScale: 0.3,                 // Size of note spheres
    spaceScale: {
        pitch: 0.15,                // X-axis scaling
        duration: 10,               // Y-axis scaling
        step: 8                     // Z-axis scaling
    }
};
```

### Changing Colors

Modify the `velocityToColor()` function (line 282) to change the color mapping:

```javascript
function velocityToColor(velocity) {
    const normalized = velocity / 127;
    const hue = normalized * 0.7;  // Change 0.7 to adjust color range
    return new THREE.Color().setHSL(hue, 1.0, 0.5);
}
```

### Adding Camera Movement

Add this to the `animate()` function for orbital camera:

```javascript
camera.position.x = Math.sin(currentTime * 0.0001) * 30;
camera.position.z = Math.cos(currentTime * 0.0001) * 30;
camera.lookAt(0, 10, 0);
```

## 🎯 Future UI Integration

The visualization is designed with modularity in mind for easy UI integration:

### Planned Features
- **Preset Saving**: Save and load visual presets
- **Color Schemes**: Switch between different color palettes
- **Export**: Capture screenshots or record video
- **Playback Controls**: Pause, rewind, adjust speed
- **Multiple Visualizations**: Switch between different visual modes
- **MIDI Input Mapping**: Custom mapping of MIDI to visual parameters

### Integration Points

The code is structured with clean separation:

1. **Configuration** (lines 186-197): Easy to expose as UI settings
2. **Visual Parameters**: All major values are in CONFIG object
3. **WebSocket Handler**: Can be extended for bidirectional communication
4. **Event System**: Ready for UI callbacks and controls

To add UI, simply:
1. Create a UI framework wrapper (React, Vue, etc.)
2. Expose CONFIG values as props/state
3. Use existing control functions
4. Add new visualization modes by extending `addNote()`

## 🐛 Troubleshooting

### "WebSocket connection failed"
- Ensure `realtime_midi_generator.py` is running
- Check that port 8765 is not blocked by firewall
- Verify correct WebSocket URL in visualization.html

### "No notes appearing"
- Check browser console for errors (F12)
- Verify MIDI generator is actually generating notes
- Look for WebSocket messages in Network tab

### "Visualization is laggy"
- Reduce particle density via control panel
- Reduce trail length
- Close other browser tabs
- Check FPS counter in info panel

### "Notes appear in wrong positions"
- Verify MIDI data is within expected ranges
- Check `spaceScale` values in CONFIG
- Ensure model is properly loaded

## 📊 Performance

- **Recommended**: Modern browser with WebGL support
- **FPS**: 60 FPS with 100 notes + 500 particles
- **Latency**: <50ms from MIDI generation to visualization
- **Memory**: ~100MB with typical usage

## 📝 Technical Notes

- Uses Three.js r128 from CDN (no installation required)
- WebGL-based rendering for smooth performance
- Automatic reconnection on WebSocket disconnect
- Responsive canvas sizing
- No external assets or dependencies beyond Three.js

## 🤝 Contributing

This visualization system is designed to be easily extensible. Some ideas:

- Add VR/AR support using Three.js VRButton
- Implement beat detection visualization
- Add audio waveform analysis
- Create different visual modes (tunnel, galaxy, etc.)
- Export to video or GIF

## 📄 License

Part of the Generative Music RNN project.

## 🙏 Credits

- **Three.js**: 3D rendering library
- **WebSocket**: Real-time communication
- **TensorFlow**: RNN model training and inference

---

**Enjoy your visualized generative music! 🎵✨**

For questions or issues, check the main project README or open an issue on GitHub.
