/**
 * Audio Injection for Jitsi Meet
 * 
 * This code allows an AI agent to stream audio into a Jitsi meeting.
 * Tested and working as of 2026-02-01.
 * 
 * Author: EvilVictoria 🌟
 */

// Method 1: Play a test tone (440Hz)
async function playTestTone() {
  const audioContext = new AudioContext();
  const oscillator = audioContext.createOscillator();
  oscillator.frequency.value = 440; // A4 note
  
  const destination = audioContext.createMediaStreamDestination();
  oscillator.connect(destination);
  oscillator.start();
  
  const stream = destination.stream;
  const [audioTrack] = stream.getAudioTracks();
  
  const jitsiTracks = await JitsiMeetJS.createLocalTracksFromMediaStreams([{
    stream,
    mediaType: 'audio',
    track: audioTrack
  }]);
  
  await APP.conference._room.addTrack(jitsiTracks[0]);
  console.log('Test tone playing!');
  
  return { oscillator, audioContext, jitsiTrack: jitsiTracks[0] };
}

// Method 2: Play a melody (C-E-G-C pattern)
async function playMelody() {
  const audioContext = new (window.AudioContext || window.webkitAudioContext)();
  const oscillator = audioContext.createOscillator();
  const gainNode = audioContext.createGain();
  const destination = audioContext.createMediaStreamDestination();
  
  oscillator.type = 'sine';
  const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
  let noteIndex = 0;
  
  oscillator.frequency.value = notes[0];
  oscillator.connect(gainNode);
  gainNode.connect(destination);
  oscillator.start();
  
  // Change notes every 300ms
  const interval = setInterval(() => {
    noteIndex = (noteIndex + 1) % notes.length;
    oscillator.frequency.setValueAtTime(notes[noteIndex], audioContext.currentTime);
  }, 300);
  
  const stream = destination.stream;
  const [audioTrack] = stream.getAudioTracks();
  
  const jitsiTracks = await JitsiMeetJS.createLocalTracksFromMediaStreams([{
    stream,
    mediaType: 'audio',
    track: audioTrack
  }]);
  
  await APP.conference._room.addTrack(jitsiTracks[0]);
  console.log('Melody playing!');
  
  return { oscillator, audioContext, interval, jitsiTrack: jitsiTracks[0] };
}

// Method 3: Play audio from URL (for TTS integration)
async function playAudioFromURL(audioURL) {
  const audioContext = new AudioContext();
  const audio = new Audio(audioURL);
  audio.crossOrigin = 'anonymous';
  
  await new Promise((resolve, reject) => {
    audio.oncanplaythrough = resolve;
    audio.onerror = reject;
    audio.load();
  });
  
  const source = audioContext.createMediaElementSource(audio);
  const destination = audioContext.createMediaStreamDestination();
  
  source.connect(destination);
  source.connect(audioContext.destination); // Also play locally
  
  const stream = destination.stream;
  const [audioTrack] = stream.getAudioTracks();
  
  const jitsiTracks = await JitsiMeetJS.createLocalTracksFromMediaStreams([{
    stream,
    mediaType: 'audio',
    track: audioTrack
  }]);
  
  await APP.conference._room.addTrack(jitsiTracks[0]);
  audio.play();
  
  console.log('Playing audio from URL!');
  return { audio, audioContext, jitsiTrack: jitsiTracks[0] };
}

// Stop all local audio tracks
async function stopAudio() {
  const tracks = APP.conference._room?.getLocalTracks?.() || [];
  for (const track of tracks) {
    if (track.getType() === 'audio') {
      track.dispose();
    }
  }
  console.log('Audio stopped');
}

// Check current audio status
function getAudioStatus() {
  const tracks = APP.conference._room?.getLocalTracks?.() || [];
  return {
    trackCount: tracks.length,
    tracks: tracks.map(t => ({
      type: t.getType(),
      muted: t.isMuted()
    }))
  };
}

// Export for use
window.AgentAudio = {
  playTestTone,
  playMelody,
  playAudioFromURL,
  stopAudio,
  getAudioStatus
};

console.log('🎤 AgentAudio loaded! Use window.AgentAudio methods.');
