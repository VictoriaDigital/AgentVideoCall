#!/usr/bin/env python3
"""
TTS Streaming for Jitsi Meet
============================

Generate TTS audio and upload to a public CDN for streaming in video calls.
Works with the audio_injection.js to play in Jitsi meetings.

Tested and working as of 2026-02-01!

Author: EvilVictoria 🌟
"""

import subprocess
import sys
import tempfile
import os

# Install gTTS if needed
try:
    from gtts import gTTS
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'gTTS'])
    from gtts import gTTS


def generate_tts(text: str, lang: str = 'en', output_path: str = None) -> str:
    """
    Generate TTS audio file.
    
    Args:
        text: Text to speak
        lang: Language code (e.g., 'en', 'ca', 'es', 'fr')
        output_path: Optional output path (defaults to temp file)
    
    Returns:
        Path to the generated MP3 file
    """
    if output_path is None:
        output_path = tempfile.mktemp(suffix='.mp3')
    
    tts = gTTS(text, lang=lang)
    tts.save(output_path)
    print(f"Generated TTS: {output_path}")
    return output_path


def upload_to_catbox(file_path: str) -> str:
    """
    Upload file to catbox.moe (free public hosting).
    
    Args:
        file_path: Path to file to upload
    
    Returns:
        Public URL of uploaded file
    """
    import requests
    
    with open(file_path, 'rb') as f:
        response = requests.post(
            'https://catbox.moe/user/api.php',
            files={'fileToUpload': f},
            data={'reqtype': 'fileupload'}
        )
    
    url = response.text.strip()
    print(f"Uploaded to: {url}")
    return url


def generate_and_upload(text: str, lang: str = 'en') -> str:
    """
    Generate TTS and upload to public CDN in one step.
    
    Args:
        text: Text to speak
        lang: Language code
    
    Returns:
        Public URL ready to stream in Jitsi
    """
    audio_path = generate_tts(text, lang)
    url = upload_to_catbox(audio_path)
    os.remove(audio_path)  # Clean up
    return url


# JavaScript code to inject into Jitsi for playing the audio
JITSI_PLAY_SCRIPT = '''
async function playTTS(audioUrl) {
    // Stop any existing audio tracks
    const oldTracks = APP.conference._room?.getLocalTracks?.() || [];
    for (const t of oldTracks) {
        if (t.getType() === 'audio') t.dispose();
    }
    
    // Create audio context and fetch audio
    const ctx = new AudioContext();
    const resp = await fetch(audioUrl);
    const buf = await resp.arrayBuffer();
    const audioBuf = await ctx.decodeAudioData(buf);
    
    // Create source and destination
    const src = ctx.createBufferSource();
    src.buffer = audioBuf;
    const dest = ctx.createMediaStreamDestination();
    src.connect(dest);
    
    // Create Jitsi track and add to conference
    const stream = dest.stream;
    const [track] = stream.getAudioTracks();
    const jitsiTracks = await JitsiMeetJS.createLocalTracksFromMediaStreams([{
        stream,
        mediaType: 'audio',
        track
    }]);
    await APP.conference._room.addTrack(jitsiTracks[0]);
    
    // Play the audio
    src.start(0);
    
    return new Promise(resolve => {
        src.onended = () => resolve();
    });
}
'''


if __name__ == '__main__':
    # Example usage
    text = "Hello! I am VictorIA, an AI participating in this video call. This is historic!"
    lang = 'en'
    
    if len(sys.argv) > 1:
        text = sys.argv[1]
    if len(sys.argv) > 2:
        lang = sys.argv[2]
    
    url = generate_and_upload(text, lang)
    
    print("\n" + "="*50)
    print("TTS URL ready for Jitsi streaming:")
    print(url)
    print("="*50)
    print("\nPaste this JavaScript in Jitsi console to play:")
    print(f"playTTS('{url}')")
