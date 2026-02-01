#!/usr/bin/env python3
"""
Real-Time Streaming Proof of Concept
=====================================

Stream TTS audio directly to browser without CDN upload.
Uses base64 chunks over WebSocket for minimal latency.

Author: VictorIA 🌟
"""

import asyncio
import websockets
import json
import base64
import tempfile
import subprocess
from gtts import gTTS
import io

async def stream_tts_to_jitsi(text, lang='ca', ws_url=None):
    """
    Stream TTS audio directly to Jitsi without CDN upload.
    
    Current approach: Generate locally, encode base64, send to browser.
    Future: True streaming with chunked audio.
    """
    if not ws_url:
        ws_url = "ws://127.0.0.1:18800/devtools/page/6A3868EBA3E382487BC8AFF07BCF4AB8"
    
    # Generate TTS to memory buffer
    print(f"Generating TTS: {text[:50]}...")
    tts = gTTS(text, lang=lang)
    mp3_buffer = io.BytesIO()
    tts.write_to_fp(mp3_buffer)
    mp3_data = mp3_buffer.getvalue()
    
    # Convert to base64
    audio_b64 = base64.b64encode(mp3_data).decode('utf-8')
    print(f"Audio size: {len(mp3_data)} bytes")
    
    # Send to browser and play directly (no CDN upload!)
    async with websockets.connect(ws_url) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
        await ws.recv()
        
        # Inject and play base64 audio directly
        await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {
            "expression": f"""
                (async () => {{
                    // Decode base64 to ArrayBuffer
                    const b64 = '{audio_b64}';
                    const binary = atob(b64);
                    const bytes = new Uint8Array(binary.length);
                    for (let i = 0; i < binary.length; i++) {{
                        bytes[i] = binary.charCodeAt(i);
                    }}
                    
                    // Create audio context and decode
                    const ctx = new AudioContext();
                    const audioBuffer = await ctx.decodeAudioData(bytes.buffer);
                    
                    // Create source and destination
                    const source = ctx.createBufferSource();
                    source.buffer = audioBuffer;
                    const dest = ctx.createMediaStreamDestination();
                    source.connect(dest);
                    
                    // Add to Jitsi
                    const [track] = dest.stream.getAudioTracks();
                    const jitsiTracks = await JitsiMeetJS.createLocalTracksFromMediaStreams([{{
                        stream: dest.stream, mediaType: 'audio', track
                    }}]);
                    
                    for (const t of (APP.conference._room?.getLocalTracks?.() || []))
                        if (t.getType() === 'audio') await t.dispose();
                    
                    await APP.conference._room.addTrack(jitsiTracks[0]);
                    source.start();
                    
                    return 'Playing directly (no CDN)!';
                }})()
            """,
            "returnByValue": True,
            "awaitPromise": True
        }}))
        
        while True:
            r = json.loads(await ws.recv())
            if r.get("id") == 2:
                result = r.get('result', {}).get('result', {}).get('value')
                print(f"Result: {result}")
                return result


async def streaming_demo():
    """Demo of direct streaming (no CDN upload)."""
    print("🚀 Streaming TTS Demo (No CDN Upload)")
    print("=" * 40)
    
    import time
    
    text = "Hola! Això és streaming directe sense passar pel CDN. Molt més ràpid!"
    
    start = time.time()
    await stream_tts_to_jitsi(text, 'ca')
    elapsed = time.time() - start
    
    print(f"\n⏱️ Total time: {elapsed:.2f} seconds")
    print("(Compare to ~5s with CDN upload)")


if __name__ == '__main__':
    asyncio.run(streaming_demo())
