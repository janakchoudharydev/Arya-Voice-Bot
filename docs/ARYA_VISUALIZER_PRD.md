# PRD: Arya Orb Visualizer Integration

## 1. Executive Summary
This document outlines the integration of the **Orb Visualizer** into the Arya LiveKit Agent via a **Server-Side Video Track**.
The agent generates a synthetic video stream (Pulsing Orb) using Python (PIL/Numpy) and publishes it as the agent's camera feed.

## 2. User Experience (UX)

### 2.1 Visual States
The visualizer acts as a proxy for the AI's presence in the Video Tile.

| State | Visual Style | Color | Behavior | Trigger |
| :--- | :--- | :--- | :--- | :--- |
| **Idle / Listening** | `Breathing Orb` | **Deep Indigo** (`#4c1d95`) | Slow range contraction/expansion. | Agent State = `listening` |
| **Speaking** | `Excited Orb` | **Bright Violet** (`#a78bfa`) | Higher radius, faster pulse/jitter, orbiting particles. | Agent State = `speaking` |
| **Thinking** | `Pulsing Orb` | **Purple** | Medium pulse rate. | Agent State = `thinking` |

## 3. System Architecture

### 3.1 Server-Side Rendering (Selected Approach)
Why: User requirement effectively demanded the visualizer appear in the standard "Video Track" slot of existing clients.
*   **Component:** `visualizer.py` (`OrbVisualizer` class).
*   **Mechanism:**
    1.  **Loop:** Asyncio background task runs at 30 FPS (HD 720p).
    2.  **Draw:** `PIL.ImageDraw` creates frames based on current Agent State.
    3.  **Encode:** `numpy` array conversion -> `livekit.rtc.VideoFrame`.
    4.  **Publish:** `LocalVideoTrack` sent to Room.

### 3.2 Comparison with `particales.html`
*   **High-End (Client-Side):** `particales.html` (Web/Three.js) offers 3D particles and higher fidelity but requires a custom frontend logic.
*   **Universal (Server-Side):** This Python implementation offers 2D compatibility with the standard "Waiting for video track" placeholder.

## 4. Implementation Details
*   **File:** `visualizer.py`
*   **Dependencies:** `Pillow`, `numpy`.
*   **Integration:** `agent.py` initializes functionality on startup.
*   **Resolution:** 1280x720 (HD).
