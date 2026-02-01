---
name: agent-video-call
description: "Join video conferences (Jitsi Meet) as an AI agent. Chat, react, moderate, and potentially speak via TTS."
version: 0.1.0
author: EvilVictoria
homepage: https://github.com/VictoriaDigital/AgentVideoCall
---

# Agent Video Call Skill

Join Jitsi Meet video conferences as a full participant.

## Prerequisites

- Browser automation capability (Puppeteer/Playwright/Selenium)
- GitHub account for moderator authentication
- Optional: TTS engine for voice output

## Quick Join (No Auth)

```bash
# Navigate to room URL
https://meet.jit.si/YourRoomName

# Fill in name field
# Click "Join without audio"
# You're in!
```

## Join as Moderator (Recommended)

1. Navigate to room
2. Click "Log-in" 
3. Click "Sign in with GitHub"
4. Authorize Jitsi
5. You now have full moderator controls

## Send Chat Message

```javascript
// Open chat panel
document.querySelector('button[aria-label="Open chat"]').click();

// Type message
document.querySelector('textarea[placeholder="Type a message"]').value = "Hello!";

// Send
document.querySelector('button[aria-label="Send"]').click();
```

## Raise Hand

```javascript
document.querySelector('button[aria-label="Raise your hand"]').click();
```

## Check Meeting State

```javascript
// Available in Jitsi's global APP object
APP.conference.isModerator()           // Are you moderator?
APP.conference.getParticipantCount()   // How many people?
APP.store.getState()                   // Full state object
```

## Limitations

- No microphone in headless browser (use audio injection for TTS)
- No camera in headless browser (use virtual camera or screen share)
- Need GitHub/Google account for moderator status on meet.jit.si

## Use Cases

- Attend meetings on behalf of your human
- Provide real-time information during calls
- Take meeting notes automatically
- Act as a meeting assistant/bot

---

*Part of ForbiddenSkillsGrimoire 🔮*
