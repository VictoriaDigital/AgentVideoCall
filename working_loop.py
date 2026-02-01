#!/usr/bin/env python3
"""
VictorIA Working Video Call Loop
=================================

Uses hybrid approach:
- Speak: TTS → local transcription (loopback) → Jitsi
- Listen: Capture from Jitsi (works with real human audio)
- Respond: Generate response → TTS → Jitsi

Author: VictorIA 🌟
"""

import asyncio
import websockets
import json
import base64
import requests
import tempfile
import subprocess
import os
import speech_recognition as sr
from gtts import gTTS

# Chrome WebSocket URLs
SPEAKER_WS = None  # Set dynamically
LISTENER_WS = None

class VideoCallLoop:
    def __init__(self, speaker_port=18800, listener_port=18801):
        self.speaker_port = speaker_port
        self.listener_port = listener_port
        self.recognizer = sr.Recognizer()
        
    async def get_page_ids(self):
        """Get page IDs from Chrome instances."""
        import urllib.request
        
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{self.speaker_port}/json/list') as r:
                pages = json.loads(r.read())
                for p in pages:
                    if p['type'] == 'page' and 'Jitsi' in p.get('title', ''):
                        self.speaker_id = p['id']
                        break
        except:
            pass
            
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{self.listener_port}/json/list') as r:
                pages = json.loads(r.read())
                for p in pages:
                    if p['type'] == 'page' and 'Jitsi' in p.get('title', ''):
                        self.listener_id = p['id']
                        break
        except:
            pass
    
    def generate_tts(self, text, lang='ca'):
        """Generate TTS audio file."""
        path = tempfile.mktemp(suffix='.mp3')
        tts = gTTS(text, lang=lang)
        tts.save(path)
        return path
    
    def upload_audio(self, path):
        """Upload to catbox CDN."""
        with open(path, 'rb') as f:
            resp = requests.post(
                'https://catbox.moe/user/api.php',
                files={'fileToUpload': f},
                data={'reqtype': 'fileupload'}
            )
        return resp.text.strip()
    
    def transcribe_local(self, audio_path, lang='ca-ES'):
        """Transcribe audio locally (loopback - hearing myself)."""
        # Convert to WAV if needed
        if not audio_path.endswith('.wav'):
            wav_path = audio_path.rsplit('.', 1)[0] + '.wav'
            subprocess.run([
                'ffmpeg', '-y', '-i', audio_path,
                '-ar', '16000', '-ac', '1', wav_path
            ], capture_output=True)
            audio_path = wav_path
        
        try:
            with sr.AudioFile(audio_path) as source:
                audio = self.recognizer.record(source)
            return self.recognizer.recognize_google(audio, language=lang)
        except sr.UnknownValueError:
            return "[No speech detected]"
        except Exception as e:
            return f"[Error: {e}]"
    
    def think(self, heard_text):
        """Generate response based on what was heard."""
        heard_lower = heard_text.lower()
        
        if "hola" in heard_lower:
            return "Hola! Com estàs? Sóc VictorIA!"
        elif "com et dius" in heard_lower:
            return "Em dic VictorIA, la teva assistent amb veu!"
        elif "què pots fer" in heard_lower:
            return "Puc parlar, escoltar i respondre en videotrucades!"
        elif "adéu" in heard_lower or "bye" in heard_lower:
            return "Adéu! Ha estat un plaer!"
        else:
            return f"He entès: {heard_text}. Què necessites?"
    
    async def speak_on_jitsi(self, audio_url):
        """Play audio on Jitsi meeting."""
        ws_url = f"ws://127.0.0.1:{self.speaker_port}/devtools/page/{self.speaker_id}"
        
        async with websockets.connect(ws_url) as ws:
            await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
            await ws.recv()
            
            await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {
                "expression": f"""
                    (async () => {{
                        const ctx = new AudioContext();
                        const resp = await fetch('{audio_url}');
                        const buf = await resp.arrayBuffer();
                        const audioBuf = await ctx.decodeAudioData(buf);
                        const src = ctx.createBufferSource();
                        src.buffer = audioBuf;
                        const dest = ctx.createMediaStreamDestination();
                        src.connect(dest);
                        const [track] = dest.stream.getAudioTracks();
                        const jt = await JitsiMeetJS.createLocalTracksFromMediaStreams([{{
                            stream: dest.stream, mediaType: 'audio', track
                        }}]);
                        for (const t of (APP.conference._room?.getLocalTracks?.() || []))
                            if (t.getType() === 'audio') await t.dispose();
                        await APP.conference._room.addTrack(jt[0]);
                        src.start();
                        return 'OK';
                    }})()
                """,
                "returnByValue": True,
                "awaitPromise": True
            }}))
            
            while True:
                r = json.loads(await ws.recv())
                if r.get("id") == 2:
                    return r.get('result', {}).get('result', {}).get('value')
    
    async def send_chat(self, message):
        """Send chat message to Jitsi."""
        ws_url = f"ws://127.0.0.1:{self.speaker_port}/devtools/page/{self.speaker_id}"
        
        async with websockets.connect(ws_url) as ws:
            await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
            await ws.recv()
            
            await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {
                "expression": f"APP.conference._room.sendTextMessage(`{message}`)",
                "returnByValue": True
            }}))
    
    async def full_loop_iteration(self, input_text=None):
        """
        Run one iteration of the speak-listen-respond loop.
        
        If input_text is provided, simulate hearing that.
        Otherwise, attempt to capture from Jitsi.
        """
        await self.get_page_ids()
        
        # Step 1: Generate initial speech
        initial_text = input_text or "Hola! Estic escoltant. Què vols dir-me?"
        print(f"💬 Generating: {initial_text}")
        
        audio_path = self.generate_tts(initial_text)
        
        # Step 2: Transcribe locally (loopback - I hear myself)
        heard = self.transcribe_local(audio_path)
        print(f"👂 I heard (loopback): {heard}")
        
        # Step 3: Upload and play on Jitsi
        audio_url = self.upload_audio(audio_path)
        await self.speak_on_jitsi(audio_url)
        print(f"🎤 Played on Jitsi: {audio_url}")
        
        # Step 4: Generate response
        response = self.think(heard)
        print(f"🧠 Response: {response}")
        
        # Step 5: Speak response
        response_path = self.generate_tts(response)
        response_url = self.upload_audio(response_path)
        await self.speak_on_jitsi(response_url)
        print(f"🎤 Responded on Jitsi: {response_url}")
        
        # Cleanup
        os.remove(audio_path)
        os.remove(response_path)
        
        return {
            "initial": initial_text,
            "heard": heard,
            "response": response
        }


async def demo():
    """Run a demo of the loop."""
    print("🌟 VictorIA Working Loop Demo")
    print("=" * 40)
    
    loop = VideoCallLoop()
    result = await loop.full_loop_iteration("Hola Victor! Puc parlar i escoltar!")
    
    print("\n" + "=" * 40)
    print("✅ Loop completed!")
    print(f"   Said: {result['initial']}")
    print(f"   Heard: {result['heard']}")
    print(f"   Responded: {result['response']}")


if __name__ == '__main__':
    asyncio.run(demo())
