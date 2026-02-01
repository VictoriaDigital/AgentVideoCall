# Jitsi Voice Breakthrough - 2026-02-01

## What Works Now

### Speaking (Me → Jitsi → Human)
1. **gTTS** for quick multi-language TTS
2. **Catalan TTS (Olga balear)** via Docker on port 7860
3. **Audio injection** via base64 → AudioContext → JitsiTrack

### Listening (Human → Jitsi → Me)
1. **Capture from JitsiTrack directly** (not WebRTC receivers)
2. **Whisper transcription** with auto language detection
3. Works with Spanish, English, Catalan

## Key Discoveries

### Chrome Flags Required
```bash
google-chrome \
  --headless=new \
  --use-fake-device-for-media-stream \  # CRITICAL! Fake mic device
  --use-fake-ui-for-media-stream \      # Auto-allow permissions
  --autoplay-policy=no-user-gesture-required
```

Without `--use-fake-device-for-media-stream`, Jitsi stays permanently muted!

### Capture from Participant's JitsiTrack
```javascript
// DON'T use generic WebRTC receivers (gets silence)
const receivers = pc.getReceivers().filter(r => r.track?.kind === 'audio');

// DO use the participant's JitsiTrack directly
const victor = APP.conference._room.getParticipants().find(p => p.getDisplayName() === 'Victor');
const audioTrack = victor.getTracks().find(t => t.getType() === 'audio');
const stream = new MediaStream([audioTrack.track]);
```

### Catalan TTS Setup
```bash
docker run -d --name catalan-tts -p 7860:8000 --restart unless-stopped catalan-tts

curl -X POST http://localhost:7860/api/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hola!", "voice": "olga", "accent": "balear"}' \
  --output audio.wav
```

## Current Latency
- TTS generation: ~3-5s
- Audio injection: ~0.3s
- Capture: 6-8s (configurable)
- Whisper transcription: ~3s
- **Total loop: ~12-15s**

## TODO for Production
1. **Continuous listening** - always record in background
2. **Faster Whisper** - use tiny model or GPU
3. **Streaming TTS** - reduce generation time
4. **Smart VAD** - detect when human stops speaking

## Files
- `working_loop.py` - Basic working loop
- `realtime_loop.py` - Optimized streaming version
- `streaming_poc.py` - Direct base64 injection POC

## Session Stats
- First successful TTS → Jitsi: ✅
- First successful capture → transcription: ✅
- Full conversation loop: ✅
- Catalan voice working: ✅
- Spanish transcription: ✅
