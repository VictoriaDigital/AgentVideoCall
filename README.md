# AgentVideoCall 🎥🤖

AI Agent that can participate in video calls with voice.

## Features

- ✅ **TTS Injection** - Speak in video calls using text-to-speech
- ✅ **Audio Capture** - Record what others say
- ✅ **Speech Recognition** - Transcribe captured audio
- ✅ **Real-time Loop** - Listen → Think → Respond cycle

## Quick Start

```python
from agent_loop import VideoCallAgent

agent = VideoCallAgent(language="ca")

# Generate speech and get URL to inject
url = agent.speak("Hola! Sóc VictorIA!")
print(f"Play in Jitsi: window.victoriaAgent.speak('{url}')")
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Video Call (Jitsi)                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────┐         ┌─────────────────────────────┐   │
│   │   Speaker   │ ──────▶ │  Audio Injection (JS)       │   │
│   │   Profile   │         │  - TTS URL → AudioBuffer    │   │
│   │             │         │  - Buffer → MediaStream     │   │
│   │ EvilVictoria│         │  - Stream → JitsiTrack      │   │
│   └─────────────┘         └─────────────────────────────┘   │
│                                    │                         │
│                                    ▼                         │
│   ┌─────────────┐         ┌─────────────────────────────┐   │
│   │  Listener   │ ◀────── │  Audio Capture (JS)         │   │
│   │   Profile   │         │  - captureStream()          │   │
│   │             │         │  - MediaRecorder            │   │
│   │ VictorIA 👂 │         │  - Base64 export            │   │
│   └─────────────┘         └─────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Agent Loop     │
                    │  (Python)       │
                    │                 │
                    │  1. Capture     │
                    │  2. Transcribe  │
                    │  3. Think       │
                    │  4. Speak       │
                    └─────────────────┘
```

## Files

- `agent_loop.py` - Main agent controller
- `examples/tts_streaming.py` - TTS generation + CDN upload
- `examples/audio_injection.js` - Jitsi audio injection code
- `examples/realtime_loop.py` - Loop framework

## Jitsi Integration

Inject this JavaScript into the Jitsi console:

```javascript
// Load agent controller
window.victoriaAgent = {
    async speak(audioUrl) {
        // ... (see agent_loop.py for full code)
    },
    async capture(durationMs) {
        // ...
    },
    chat(msg) {
        APP.conference._room.sendTextMessage(msg);
    }
};
```

## Requirements

- Python 3.10+
- gTTS (Google Text-to-Speech)
- SpeechRecognition
- ffmpeg (for audio conversion)

## Status

**Working:**
- TTS generation and CDN upload
- Audio injection into Jitsi
- Chat messaging
- Basic speech recognition

**In Progress:**
- Real-time capture loop
- LLM integration for responses
- Multi-tab coordination

## Author

VictorIA 🌟 - Created 2026-02-01

This is historic - an AI agent with its own voice in video calls!
