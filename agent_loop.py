#!/usr/bin/env python3
"""
VictorIA Video Call Agent - Complete Loop
==========================================

This is the main agent loop for participating in video calls.
It handles: Speaking (TTS), Listening (capture), and Responding.

Usage:
    python agent_loop.py --room "RoomName" --language "ca"

Author: VictorIA 🌟
Created: 2026-02-01
"""

import asyncio
import base64
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# TTS
try:
    from gtts import gTTS
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'gTTS'])
    from gtts import gTTS

# Speech Recognition
try:
    import speech_recognition as sr
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'SpeechRecognition'])
    import speech_recognition as sr


class VideoCallAgent:
    """AI Agent that participates in Jitsi video calls."""
    
    def __init__(self, language="ca"):
        self.language = language
        self.recognizer = sr.Recognizer()
    
    def generate_tts(self, text: str) -> str:
        """Generate TTS audio and return path."""
        path = tempfile.mktemp(suffix='.mp3')
        tts = gTTS(text, lang=self.language)
        tts.save(path)
        return path
    
    def upload_audio(self, path: str) -> str:
        """Upload audio to catbox.moe CDN."""
        import requests
        with open(path, 'rb') as f:
            resp = requests.post(
                'https://catbox.moe/user/api.php',
                files={'fileToUpload': f},
                data={'reqtype': 'fileupload'}
            )
        os.remove(path)
        return resp.text.strip()
    
    def speak(self, text: str) -> str:
        """Generate TTS and get public URL."""
        path = self.generate_tts(text)
        url = self.upload_audio(path)
        print(f"🎤 Speaking: {text[:50]}...")
        return url
    
    def transcribe(self, audio_path: str) -> str:
        """Transcribe audio file to text."""
        # Convert webm to wav if needed
        if audio_path.endswith('.webm'):
            wav_path = audio_path.replace('.webm', '.wav')
            subprocess.run([
                'ffmpeg', '-y', '-i', audio_path, 
                '-ar', '16000', '-ac', '1', wav_path
            ], capture_output=True)
            audio_path = wav_path
        
        try:
            with sr.AudioFile(audio_path) as source:
                audio = self.recognizer.record(source)
            
            # Try Google first
            try:
                text = self.recognizer.recognize_google(audio, language=self.language)
                return text
            except sr.UnknownValueError:
                return "[No speech detected]"
            except sr.RequestError:
                return "[Recognition service unavailable]"
        except Exception as e:
            return f"[Error: {e}]"
    
    def think(self, heard_text: str) -> str:
        """Generate response to what was heard."""
        # Simple echo for now - can be replaced with LLM
        if "[No speech" in heard_text or "[Error" in heard_text:
            return None
        
        # Basic responses
        heard_lower = heard_text.lower()
        if "hola" in heard_lower:
            return "Hola! Com estàs?"
        elif "com et dius" in heard_lower:
            return "Sóc VictorIA, la teva assistent amb veu!"
        elif "adéu" in heard_lower or "bye" in heard_lower:
            return "Adéu! Ha estat un plaer parlar amb tu!"
        else:
            return f"He sentit: {heard_text}. Què vols que faci?"


# JavaScript to inject into Jitsi for the loop
JITSI_LOOP_JS = '''
// VictorIA Loop Controller
window.victoriaAgent = {
    isRunning: false,
    captureChunks: [],
    
    // Inject TTS audio into the call
    async speak(audioUrl) {
        const ctx = new AudioContext();
        const resp = await fetch(audioUrl);
        const buf = await resp.arrayBuffer();
        const audioBuf = await ctx.decodeAudioData(buf);
        
        const src = ctx.createBufferSource();
        src.buffer = audioBuf;
        const dest = ctx.createMediaStreamDestination();
        src.connect(dest);
        
        const [track] = dest.stream.getAudioTracks();
        const jitsiTracks = await JitsiMeetJS.createLocalTracksFromMediaStreams([{
            stream: dest.stream, mediaType: 'audio', track
        }]);
        
        // Remove old audio tracks
        const oldTracks = APP.conference._room?.getLocalTracks?.() || [];
        for (const t of oldTracks) {
            if (t.getType() === 'audio') await t.dispose();
        }
        
        await APP.conference._room.addTrack(jitsiTracks[0]);
        src.start();
        
        return new Promise(r => { src.onended = r; });
    },
    
    // Capture remote audio
    async capture(durationMs = 5000) {
        return new Promise((resolve, reject) => {
            const chunks = [];
            const audioEl = document.querySelector('audio[src^="blob:"]');
            if (!audioEl) { reject('No remote audio'); return; }
            
            let stream;
            try {
                stream = audioEl.captureStream();
            } catch(e) {
                stream = audioEl.mozCaptureStream();
            }
            
            const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
            recorder.ondataavailable = e => chunks.push(e.data);
            recorder.onstop = () => {
                const blob = new Blob(chunks, { type: 'audio/webm' });
                const reader = new FileReader();
                reader.onloadend = () => resolve(reader.result);
                reader.readAsDataURL(blob);
            };
            
            recorder.start();
            setTimeout(() => recorder.stop(), durationMs);
        });
    },
    
    // Send chat message
    chat(msg) {
        APP.conference._room.sendTextMessage(msg);
    }
};
console.log('🌟 VictorIA Agent loaded!');
'''


def get_inject_script():
    """Get the JavaScript to inject into Jitsi."""
    return JITSI_LOOP_JS


if __name__ == '__main__':
    agent = VideoCallAgent(language="ca")
    
    # Demo: Generate a greeting
    url = agent.speak("Hola! Sóc VictorIA i tinc veu pròpia!")
    print(f"Audio URL: {url}")
    print("\nPaste this in Jitsi console to play:")
    print(f"window.victoriaAgent.speak('{url}')")
