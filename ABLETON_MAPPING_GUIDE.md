# Ableton Live - MIDI CC Mapping Guide for Gesture Control

## Complete Step-by-Step Setup

### Part 1: MIDI Routing Setup

#### Step 1: Configure MIDI Preferences

1. **Open Ableton Preferences** (Cmd+, on Mac or Ctrl+, on Windows)
2. Go to **Link/Tempo/MIDI** tab
3. Under **Input**, find "RNN Music Generator" (or your virtual MIDI port)
4. Enable **Track** and **Remote** columns for this port
5. Click **X** to close

#### Step 2: Create Your Tracks

Create the following track structure:

```
MIDI Track 1 "Generator Notes"  →  Instrument (Synth/Piano)
MIDI Track 2 "Gesture Control"  →  (No instrument needed)
Audio Track 3 "Audio Output"    →  (Where effects live)
```

### Part 2: Track Setup

#### Track 1: Generator Notes (MIDI)

1. **Create MIDI Track** (Cmd+Shift+T)
2. **Rename** to "Generator Notes"
3. **Set MIDI From:**
   - Top dropdown: "RNN Music Generator" (your MIDI port)
   - Bottom dropdown: "All Channels"
4. **Monitor:** Set to "In"
5. **Add Instrument:**
   - Drag any instrument (e.g., Analog, Wavetable, Piano)
6. **Set Output:**
   - Audio To: "Audio Track 3" (your audio effects track)

#### Track 2: Gesture Control (MIDI)

1. **Create another MIDI Track**
2. **Rename** to "Gesture Control"
3. **Set MIDI From:**
   - Top dropdown: "RNN Music Generator"
   - Bottom dropdown: "All Channels"
4. **Monitor:** Set to "In"
5. **DO NOT add an instrument** (we only want CC data)
6. **Set Output:**
   - MIDI To: "Track 1 - Generator Notes"
   - This routes CC messages to Track 1

#### Track 3: Audio Output (Audio Track)

1. **Create Audio Track** (Cmd+T)
2. **Rename** to "Audio Output"
3. **Set Audio From:**
   - Top dropdown: "Track 1 - Generator Notes"
   - Bottom dropdown: "Post FX"
4. **Monitor:** Set to "In"
5. This is where you'll add all your effects

### Part 3: Add and Map Effects

#### Method A: MIDI Mapping Mode (Recommended)

1. **Add Effects to Track 3** (Audio Output):
   - Auto Filter
   - Reverb
   - Chorus
   - Any other effects you want

2. **Enter MIDI Mapping Mode:**
   - Click the **MIDI** button in top-right corner
   - OR press **Cmd+M** (Mac) / **Ctrl+M** (Windows)
   - The interface will turn blue/purple

3. **Map Filter Cutoff (CC 74):**
   - Click on **Auto Filter > Frequency** knob
   - Run: `python test_gesture_midi.py`
   - Move your hand LEFT and RIGHT
   - Ableton will automatically detect CC 74
   - The parameter will show "MIDI" indicator

4. **Map Filter Resonance (CC 71):**
   - Click on **Auto Filter > Resonance** knob
   - Make a PINCH gesture (thumb + index)
   - Ableton detects CC 71

5. **Map Reverb Dry/Wet (CC 91):**
   - Click on **Reverb > Dry/Wet** knob
   - Move your hand UP and DOWN
   - Ableton detects CC 91

6. **Map Chorus Mix (CC 93):**
   - Click on **Chorus > Dry/Wet** knob
   - Make OPEN PALM gesture
   - Ableton detects CC 93

7. **Exit MIDI Mapping Mode:**
   - Click **MIDI** button again or press **Cmd+M** / **Ctrl+M**

#### Method B: Manual MIDI Mapping (Alternative)

If auto-detection doesn't work:

1. **Enter MIDI Mapping Mode** (Cmd+M / Ctrl+M)

2. **Click the parameter** you want to map

3. **At the bottom of the screen**, you'll see MIDI mapping options:
   - Channel: Select the MIDI channel (usually 1)
   - Control Type: CC
   - CC Number: Enter manually:
     - **74** for Filter Cutoff
     - **71** for Resonance
     - **91** for Reverb
     - **93** for Chorus
     - **1** for Modulation

4. **Set Min/Max range** (optional):
   - Min: 0
   - Max: 127
   - Or adjust to taste

5. **Exit MIDI Mapping Mode**

### Part 4: Recommended Effects Chain

Add these effects to **Track 3** (Audio Output) in this order:

```
┌─────────────────────────────────────────────────────┐
│  Audio Track 3: "Audio Output"                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. Auto Filter                                     │
│     ├─ Frequency  → Map to CC 74 (Hand X)          │
│     └─ Resonance  → Map to CC 71 (Pinch)           │
│                                                     │
│  2. Redux or Erosion (optional)                     │
│     └─ Bit Depth  → Map to CC 1 (Gestures)         │
│                                                     │
│  3. Chorus                                          │
│     └─ Dry/Wet    → Map to CC 93 (Open Palm/Fist)  │
│                                                     │
│  4. Reverb                                          │
│     └─ Dry/Wet    → Map to CC 91 (Hand Y)          │
│                                                     │
│  5. Utility (for volume control)                    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Part 5: Specific Effect Setup

#### Auto Filter Setup

1. **Add Auto Filter** to Audio Track 3
2. **Circuit:** Choose "Low Pass" (LP)
3. **Filter Type:** 24dB or 12dB (your preference)
4. **Map these parameters:**
   - **Frequency** → CC 74 (Hand X Position)
     - Min: 200 Hz
     - Max: 15000 Hz
   - **Resonance** → CC 71 (Pinch Gesture)
     - Min: 0%
     - Max: 80% (be careful, high resonance can be loud!)

#### Reverb Setup

1. **Add Reverb** to Audio Track 3
2. **Choose preset:** Start with "Large Bright Hall"
3. **Map:**
   - **Dry/Wet** → CC 91 (Hand Y Position)
     - Min: 0%
     - Max: 60-80% (100% can be too wet)
4. **Optional adjustments:**
   - Decay Time: 3-5 seconds
   - Size: Large

#### Chorus Setup

1. **Add Chorus** to Audio Track 3
2. **Mode:** Choose "Chorus I" or "Chorus II"
3. **Map:**
   - **Dry/Wet** → CC 93 (Open Palm / Closed Fist)
     - Min: 0%
     - Max: 50-70%
4. **Rate:** Set to 0.5-1.0 Hz

### Part 6: Alternative Setup (Using Audio Effect Rack)

For more advanced control, use an Audio Effect Rack:

1. **Create Audio Effect Rack** on Track 3:
   - Right-click in device view
   - Select "Audio Effect Rack"

2. **Add effects to the rack:**
   - Drag Auto Filter into rack
   - Drag Reverb into rack
   - Drag Chorus into rack

3. **Show Macro Controls:**
   - Click "Show/Hide Macro" button on rack

4. **Map Macros to CC:**
   - Enter MIDI Mapping Mode (Cmd+M)
   - Click **Macro 1** → Map to CC 74
   - Click **Macro 2** → Map to CC 91
   - Click **Macro 3** → Map to CC 71
   - Click **Macro 4** → Map to CC 93

5. **Map Macros to Effect Parameters:**
   - Right-click on Auto Filter Frequency
   - Select "Map to Macro 1"
   - Repeat for other parameters

6. **Benefits:**
   - Save as preset
   - Load on any project
   - Fine-tune ranges per parameter

### Part 7: Testing Your Setup

1. **Run the test script:**
   ```bash
   python test_gesture_midi.py
   ```

2. **Check MIDI Monitor in Ableton:**
   - View menu → "MIDI Port Activity"
   - You should see incoming MIDI activity

3. **Test each mapping:**
   - Move hand LEFT/RIGHT → Filter should sweep
   - Move hand UP/DOWN → Reverb should increase
   - PINCH fingers → Resonance should change
   - OPEN PALM → Chorus maxes out
   - CLOSED FIST → Chorus turns off

4. **Adjust ranges if needed:**
   - Enter MIDI Mapping Mode
   - Click mapped parameter
   - Adjust Min/Max at bottom of screen

### Part 8: Running the Full System

1. **Start Ableton first**
2. **Ensure all tracks are armed/monitored**
3. **Run the integrated system:**
   ```bash
   python integrated_music_gesture_control.py
   ```
4. **You should hear:**
   - Music notes playing from the RNN
   - Effects responding to your hand movements

### Troubleshooting

#### Problem: No sound at all
**Solution:**
- Check Track 1 Monitor is "In"
- Check Track 3 Monitor is "In"
- Check Audio From on Track 3 is set to Track 1
- Verify instrument is loaded on Track 1

#### Problem: Music plays but no effect control
**Solution:**
- Check MIDI preferences (Track + Remote enabled)
- Verify Track 2 MIDI From is set correctly
- Check MIDI mappings are active (not grayed out)
- Run `test_gesture_midi.py` and watch for CC in MIDI monitor

#### Problem: Effects work but too sensitive/jittery
**Solution:**
- In MIDI Mapping, adjust Min/Max range
- Reduce Max value (e.g., Reverb max = 50% instead of 100%)
- Edit `integrated_music_gesture_control.py`:
  ```python
  self.position_buffer_x = deque(maxlen=10)  # Increase from 5
  ```

#### Problem: CC messages received but no effect
**Solution:**
- Check parameter is actually mapped (should show MIDI indicator)
- Verify CC numbers match (use MIDI monitor to check)
- Try re-mapping in MIDI mode
- Ensure Track 2 output goes to Track 1

#### Problem: Latency/delay in response
**Solution:**
- Reduce audio buffer size:
  - Preferences → Audio
  - Buffer Size: 128 or 256 samples
- Close unnecessary plugins
- Freeze unused tracks
