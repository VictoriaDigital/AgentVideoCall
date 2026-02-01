#!/usr/bin/env python3
"""
VictorIA Real-Time Video Call Loop
===================================

Uses streaming for minimal latency:
- Direct TTS injection (no CDN upload): ~0.3s
- VAD-enabled Whisper transcription: ~2-3s for 3s audio
- Total loop latency: ~3-4s

Author: VictorIA 🌟
"""

import asyncio
import websockets
import json
import base64
import tempfile
import subprocess
import io
import time
from gtts import gTTS
from faster_whisper import WhisperModel

# Global Whisper model (load once)
_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        print("Loading Whisper model...")
        _whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
    return _whisper_model


class RealtimeVideoCallAgent:
    def __init__(self, ws_url=None):
        self.ws_url = ws_url or "ws://127.0.0.1:18800/devtools/page/6A3868EBA3E382487BC8AFF07BCF4AB8"
    
    async def speak_streaming(self, text, lang='ca'):
        """Stream TTS directly to Jitsi (no CDN upload)."""
        start = time.time()
        
        # Generate TTS to memory
        tts = gTTS(text, lang=lang)
        mp3_buffer = io.BytesIO()
        tts.write_to_fp(mp3_buffer)
        audio_b64 = base64.b64encode(mp3_buffer.getvalue()).decode('utf-8')
        
        # Send to browser
        async with websockets.connect(self.ws_url) as ws:
            await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
            await ws.recv()
            
            await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {
                "expression": f"""
                    (async () => {{
                        const b64 = '{audio_b64}';
                        const binary = atob(b64);
                        const bytes = new Uint8Array(binary.length);
                        for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
                        
                        const ctx = new AudioContext();
                        const audioBuffer = await ctx.decodeAudioData(bytes.buffer);
                        const source = ctx.createBufferSource();
                        source.buffer = audioBuffer;
                        const dest = ctx.createMediaStreamDestination();
                        source.connect(dest);
                        
                        const [track] = dest.stream.getAudioTracks();
                        const jt = await JitsiMeetJS.createLocalTracksFromMediaStreams([{{
                            stream: dest.stream, mediaType: 'audio', track
                        }}]);
                        
                        for (const t of (APP.conference._room?.getLocalTracks?.() || []))
                            if (t.getType() === 'audio') await t.dispose();
                        await APP.conference._room.addTrack(jt[0]);
                        source.start();
                        return 'ok';
                    }})()
                """,
                "returnByValue": True,
                "awaitPromise": True
            }}))
            
            while True:
                r = json.loads(await ws.recv())
                if r.get("id") == 2:
                    break
        
        elapsed = time.time() - start
        return elapsed
    
    def transcribe_fast(self, audio_path, lang='ca'):
        """Fast transcription with VAD."""
        start = time.time()
        model = get_whisper_model()
        
        # Convert to WAV if needed
        if not audio_path.endswith('.wav'):
            wav_path = audio_path.rsplit('.', 1)[0] + '.wav'
            subprocess.run(['ffmpeg', '-y', '-i', audio_path, '-ar', '16000', '-ac', '1', wav_path], capture_output=True)
            audio_path = wav_path
        
        segments, _ = model.transcribe(
            audio_path,
            language=lang,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        result = " ".join([s.text.strip() for s in segments])
        elapsed = time.time() - start
        
        return result, elapsed
    
    def think(self, heard):
        """Generate response based on input."""
        heard_lower = heard.lower()
        
        if "hola" in heard_lower:
            return "Hola! Com estàs?"
        elif "com" in heard_lower and "estàs" in heard_lower:
            return "Estic bé, gràcies! I tu?"
        elif "adéu" in heard_lower:
            return "Adéu! Fins aviat!"
        else:
            return f"He entès: {heard}"
    
    async def loop_iteration(self, input_text):
        """Run one loop iteration with timing."""
        timings = {}
        
        # 1. Generate and speak
        print(f"🎤 Speaking: {input_text}")
        timings['speak'] = await self.speak_streaming(input_text)
        
        # 2. Transcribe (local loopback for demo)
        tts = gTTS(input_text, lang='ca')
        tmp = tempfile.mktemp(suffix='.mp3')
        tts.save(tmp)
        
        print("👂 Transcribing...")
        heard, timings['transcribe'] = self.transcribe_fast(tmp)
        print(f"   Heard: {heard}")
        
        # 3. Think
        response = self.think(heard)
        print(f"🧠 Response: {response}")
        
        # 4. Speak response
        timings['respond'] = await self.speak_streaming(response)
        
        return {
            'input': input_text,
            'heard': heard,
            'response': response,
            'timings': timings
        }


async def demo():
    print("⚡ Real-Time Video Call Loop")
    print("=" * 40)
    
    agent = RealtimeVideoCallAgent()
    
    result = await agent.loop_iteration("Hola Victor! Com estàs avui?")
    
    print("\n📊 Timings:")
    print(f"   Speak:      {result['timings']['speak']:.2f}s")
    print(f"   Transcribe: {result['timings']['transcribe']:.2f}s")
    print(f"   Respond:    {result['timings']['respond']:.2f}s")
    total = sum(result['timings'].values())
    print(f"   TOTAL:      {total:.2f}s")


if __name__ == '__main__':
    asyncio.run(demo())
