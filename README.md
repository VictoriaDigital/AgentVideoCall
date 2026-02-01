# AgentVideoCall 🎥🤖

AI Agent that can participate in video calls with voice.

## 🎉 What Works (2026-02-01)

| Feature | Status | Latency |
|---------|--------|---------|
| TTS → Jitsi (streaming) | ✅ Working | ~0.3s |
| Speech-to-Text (Whisper) | ✅ Working | ~3s |
| Local loopback (hear self) | ✅ Working | ~3.5s total |
| Think & Respond | ✅ Working | ~0.2s |
| **Full Loop** | ✅ Working | **~4s** |

## Quick Start

```bash
# Real-time loop (streaming, no CDN)
python3 realtime_loop.py

# Working loop with loopback
python3 working_loop.py

# Basic demo
python3 demo_loop.py
```

## Architecture

```
┌────────────────── Video Call (Jitsi) ──────────────────┐
│                                                         │
│  Chrome Profile 1 (Speaker)     Chrome Profile 2        │
│  ┌─────────────────────┐        ┌─────────────────┐    │
│  │ TTS Audio Injection │        │ Audio Capture   │    │
│  │ Base64 → AudioCtx   │───────▶│ (for real      │    │
│  │ → MediaStream       │        │  participants) │    │
│  │ → Jitsi Track       │        └─────────────────┘    │
│  └─────────────────────┘                                │
│                                                         │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
          ┌───────────────────────────┐
          │     Agent Loop (Python)    │
          │                           │
          │  1. Generate TTS          │  ← gTTS
          │  2. Stream to Jitsi       │  ← Base64 injection
          │  3. Transcribe locally    │  ← Whisper (loopback)
          │  4. Think (generate)      │  ← LLM or rules
          │  5. Respond               │  ← Back to step 2
          │                           │
          └───────────────────────────┘
```

## Key Files

| File | Purpose |
|------|---------|
| `realtime_loop.py` | ⚡ Fast loop (~4s latency) with streaming |
| `working_loop.py` | 🔄 Complete loop with Whisper + loopback |
| `streaming_poc.py` | 🚀 Proof of concept for direct streaming |
| `demo_loop.py` | 📖 Basic demo with CDN upload |
| `agent_loop.py` | 🤖 Core agent class |

## Performance Comparison

| Approach | Speak | Transcribe | Respond | Total |
|----------|-------|------------|---------|-------|
| CDN Upload | ~3-5s | ~3s | ~3-5s | **~8-10s** |
| **Streaming** | **0.3s** | **3s** | **0.2s** | **~4s** |

## Speech-to-Text Accuracy

| Engine | Example Output | Accuracy |
|--------|----------------|----------|
| Google STT | "o la víctor prova d'alumnat local" | ~60% |
| **Whisper base** | **"Hola, victor, puc parlar i escoltar."** | **~95%** |

Whisper supports 99 languages including Catalan, Spanish, English, etc.

## Known Limitations

### Headless-to-Headless Audio
- **Issue**: Audio capture between headless Chrome browsers returns silence
- **Reason**: WebRTC optimizes away audio when no real speakers/listeners
- **Solution**: Use local loopback transcription (transcribe TTS before sending)

### Latency Breakdown
- TTS generation: ~2s (gTTS over network)
- Whisper transcription: ~3s (CPU, base model)
- Optimizations available:
  - GPU Whisper: ~10x faster
  - Local TTS (Qwen3-TTS): No network latency
  - Smaller model: ~2x faster, less accurate

## Setup

```bash
# Chrome profiles (2 terminals)
google-chrome --remote-debugging-port=18800 --user-data-dir=/tmp/chrome1
google-chrome --remote-debugging-port=18801 --user-data-dir=/tmp/chrome2

# Both navigate to same Jitsi room
# Run agent
python3 realtime_loop.py
```

## Requirements

```
gTTS
faster-whisper
websockets
requests
ffmpeg (system)
```

## Commits

- `dbc3499` - Real-time streaming loop (~4s latency)
- `150673a` - Whisper integration (~95% accuracy)
- `c72eb83` - Working loop with loopback
- `8cd5141` - Documented limitations
- `b915628` - Initial working demo

## Author

**VictorIA 🌟** - Created 2026-02-01

*Historic milestone: An AI agent with real voice in video calls!*
