# 🤖 ARYA Voice Bot

> **Artificial Reactive Youth Assistant (ARYA)** - A sophisticated, voice-activated AI assistant tailored for macOS (M1), powered by LiveKit and Gemini Realtime.

ARYA is a highly capable, context-aware voice agent designed to automate native macOS workflows, conduct deep web research, and manage communications—all while interacting through a dynamic, dual-personality conversational interface (featuring a casual Hinglish "Bro" mode and a professional persona).

---

## ✨ Key Features

- 🎙️ **Real-time Voice Engine:** Ultra-low latency conversational AI utilizing LiveKit AgentSession and Gemini Realtime.
- 💻 **Native macOS Automation:** Control system volume, brightness, and application lifecycle (launch/quit) natively via AppleScript.
- 💬 **WhatsApp Integration:** Deeply integrated tools for sending WhatsApp text messages and executing WhatsApp Voice/Video calls using UI accessibility automation.
- 🎵 **Spotify Control (API-Free):** Play music, shuffle liked songs, and control playback natively without needing Spotify developer keys.
- 🌐 **Web Browsing & Research:** Automated Chrome navigation, web scraping, and deep research capabilities.
- 🎨 **Dynamic Orb Visualizer:** A beautiful, real-time reactive UI orb that pulses and scales dynamically with the agent's speaking and thinking states.

---

## 🏗️ Project Architecture

The codebase follows a modular, enterprise-grade structure:

- `core/` - The main brain. Contains `agent.py` (orchestrator), `instructions.py` (persona definitions), and `visualizer.py` (UI renderer).
- `tools/` - ARYA's capabilities. Contains isolated modules for macOS control, WhatsApp, Spotify, and browser automation.
- `Root Files/` - Execution scripts (`start_arya.sh`), environment variables (`.env`), and python dependencies.
- `frontend/` - UI elements, web dashboards, and the high-res agent logo.
- `database/` - Firebase configurations and local data models (e.g., `Contact.json`).
- `docs/` - Comprehensive technical documentation and audit reports.

---

## 🚀 Setup & Installation

### 1. Prerequisites
- macOS (Optimized for Apple Silicon / M1)
- Python 3.10+
- Chrome Browser
- Logged into WhatsApp Desktop and Spotify Desktop apps.

### 2. Clone the Repository
```bash
git clone https://github.com/janakchoudharydev/Arya-Voice-Bot.git
cd Arya-Voice-Bot
```

### 3. Environment Setup
Create a virtual environment and install the required dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r "Root Files/requirements.txt"
```

### 4. Configuration
Create a `.env` file inside the `Root Files/` directory (`Root Files/.env`) with your API keys:
```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
GOOGLE_API_KEY=your_gemini_api_key
```

*(Note: The `.env` file is safely ignored by Git to prevent secret leaks.)*

### 5. Running ARYA
To boot ARYA with built-in macOS sleep-prevention (caffeinate), run the startup script:

```bash
cd "Root Files"
./start_arya.sh
```

To run with full system sleep prevention (keeps display awake):
```bash
cd "Root Files"
./start_arya.sh --full
```

---

## 🛡️ Security & Privacy
- **Local Execution:** AppleScript automation runs entirely locally on your Mac.
- **No API Keys for Desktop Apps:** Spotify and WhatsApp integrations use UI automation and deep-linking, meaning your personal accounts are not exposed via OAuth tokens.

---
*Built with ❤️ and powered by LiveKit & Gemini.*