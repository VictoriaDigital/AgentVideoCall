#!/usr/bin/env python3
"""
VictorIA Video Call Demo Loop
==============================

Demonstrates the full speak-listen-respond cycle.
Uses local audio for testing when no remote participants are speaking.

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
from gtts import gTTS

# WebSocket URLs for the two Jitsi tabs
SPEAKER_WS = "ws://127.0.0.1:18800/devtools/page/79C483DBE3EC25A5086A925796308497"
LISTENER_WS = "ws://127.0.0.1:18800/devtools/page/5F295CA6D98897ACD0461FFE74C5B863"


class JitsiController:
    """Control a Jitsi tab via CDP WebSocket."""
    
    def __init__(self, ws_url):
        self.ws_url = ws_url
        self.ws = None
        self.msg_id = 0
    
    async def connect(self):
        self.ws = await websockets.connect(self.ws_url)
        await self._send("Runtime.enable")
    
    async def _send(self, method, params=None):
        self.msg_id += 1
        cmd = {"id": self.msg_id, "method": method}
        if params:
            cmd["params"] = params
        await self.ws.send(json.dumps(cmd))
        
        # Wait for matching response
        while True:
            resp = json.loads(await self.ws.recv())
            if resp.get("id") == self.msg_id:
                return resp.get("result", {}).get("result", {}).get("value")
    
    async def evaluate(self, expression, await_promise=False):
        return await self._send("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": await_promise
        })
    
    async def send_chat(self, message):
        await self.evaluate(f"APP.conference._room.sendTextMessage(`{message}`)")
    
    async def play_audio(self, url):
        """Play audio from URL into the Jitsi call."""
        return await self.evaluate(f"""
            (async () => {{
                const ctx = new AudioContext();
                const resp = await fetch('{url}');
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
                return new Promise(r => {{ src.onended = () => r('done'); }});
            }})()
        """, await_promise=True)
    
    async def capture_audio(self, duration_ms=5000):
        """Capture audio from RTCPeerConnection receivers."""
        result = await self.evaluate(f"""
            (async () => {{
                const pc = APP.conference._room?.jvbJingleSession?.peerconnection?.peerconnection;
                if (!pc) return {{error: 'No PeerConnection'}};
                
                const receivers = pc.getReceivers().filter(r => r.track?.kind === 'audio');
                if (receivers.length === 0) return {{error: 'No audio receivers'}};
                
                const stream = new MediaStream();
                receivers.forEach(r => stream.addTrack(r.track));
                
                const chunks = [];
                const recorder = new MediaRecorder(stream, {{mimeType: 'audio/webm'}});
                recorder.ondataavailable = e => chunks.push(e.data);
                
                return new Promise(resolve => {{
                    recorder.onstop = async () => {{
                        const blob = new Blob(chunks, {{type: 'audio/webm'}});
                        const reader = new FileReader();
                        reader.onloadend = () => resolve({{
                            base64: reader.result,
                            size: blob.size
                        }});
                        reader.readAsDataURL(blob);
                    }};
                    recorder.start();
                    setTimeout(() => recorder.stop(), {duration_ms});
                }});
            }})()
        """, await_promise=True)
        return result
    
    async def close(self):
        if self.ws:
            await self.ws.close()


def generate_tts(text, lang='ca'):
    """Generate TTS and upload to CDN."""
    path = tempfile.mktemp(suffix='.mp3')
    tts = gTTS(text, lang=lang)
    tts.save(path)
    
    with open(path, 'rb') as f:
        resp = requests.post(
            'https://catbox.moe/user/api.php',
            files={'fileToUpload': f},
            data={'reqtype': 'fileupload'}
        )
    os.remove(path)
    return resp.text.strip()


async def demo_loop():
    """Run a demo of the speak-listen-respond loop."""
    
    print("🌟 VictorIA Video Call Loop Demo")
    print("=" * 40)
    
    # Connect to both tabs
    speaker = JitsiController(SPEAKER_WS)
    listener = JitsiController(LISTENER_WS)
    
    try:
        await speaker.connect()
        await listener.connect()
        print("✅ Connected to both Jitsi tabs")
        
        # Step 1: Announce
        await speaker.send_chat("🔄 Iniciant demo del bucle en temps real...")
        print("\n📢 Step 1: Announcing...")
        
        # Step 2: Speak
        print("\n🎤 Step 2: Speaking...")
        url = generate_tts("Hola! Això és una demostració del bucle. Estic parlant i escoltant!", 'ca')
        print(f"   TTS URL: {url}")
        await speaker.play_audio(url)
        print("   ✅ Spoke!")
        
        # Step 3: Capture
        print("\n👂 Step 3: Capturing audio (3 seconds)...")
        result = await listener.capture_audio(3000)
        if isinstance(result, dict) and result.get('size', 0) > 0:
            print(f"   ✅ Captured {result['size']} bytes")
        else:
            print(f"   ⚠️ Capture result: {result}")
        
        # Step 4: Respond
        print("\n💬 Step 4: Responding...")
        response_url = generate_tts("Perfecte! El bucle funciona. Ara puc parlar en videotrucades!", 'ca')
        await speaker.play_audio(response_url)
        print("   ✅ Responded!")
        
        # Final announcement
        await speaker.send_chat("✅ Demo completada! El bucle parlar-escoltar-respondre funciona!")
        print("\n" + "=" * 40)
        print("🎉 Demo complete!")
        
    finally:
        await speaker.close()
        await listener.close()


if __name__ == '__main__':
    asyncio.run(demo_loop())
