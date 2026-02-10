# Riko WebSocket Integration

## Quick Start

### Option 1: Run Full System (Riko Chat + WebSocket)
```bash
python server/main_chat_ws.py
```
This runs both the chat loop and WebSocket server together.

### Option 2: Run WebSocket Only (Testing)
```bash
python server/run_server_only.py
```
Use this to test Yumi frontend connection without running the chat loop.

## WebSocket Events

### From Riko → Yumi

**Listening State**
```json
{
  "type": "listening",
  "timestamp": 1234567890.123
}
```

**Speaking State**
```json
{
  "type": "speaking",
  "text": "Hello! I'm Riko!",
  "duration": 2500,
  "timestamp": 1234567890.123
}
```
- `duration`: Audio length in milliseconds
- Triggers Yumi avatar mouth animation

**Idle State**
```json
{
  "type": "idle",
  "timestamp": 1234567890.123
}
```

### From Yumi → Riko

**Echo Test**
Send any text message to test connection:
```json
"Hello Riko"
```

Response:
```json
{
  "type": "echo",
  "message": "Hello Riko"
}
```

## Testing the Connection

### 1. Start Riko Server
```bash
cd riko_project
python server/run_server_only.py
```

### 2. Start Yumi Frontend
```bash
cd yumiai
npm run dev
```

### 3. Verify Connection
- Yumi should auto-connect on startup
- Check browser console for: `✅ Connected to Riko`
- Check Riko terminal for: `✅ Yumi connected!`

### 4. Test Mouth Animation
In Riko terminal, you'll see broadcasts when speaking.
Yumi avatar mouth should animate automatically.

## Endpoints

- **WebSocket:** `ws://localhost:5000/ws`
- **Health Check:** `http://localhost:5000/health`
- **Status:** `http://localhost:5000/`

## Architecture

### File Structure
```
server/
├── websocket_server.py      # Core WebSocket server (FastAPI app)
├── main_chat_ws.py          # Integrated chat loop with WebSocket
├── run_server_only.py       # Standalone server for testing
└── process/
    ├── asr_func/            # Speech recognition
    ├── llm_funcs/           # LLM integration
    └── tts_func/            # Text-to-speech
```

### Threading Model
- **WebSocket Server**: Runs in daemon thread
- **Chat Loop**: Runs in main thread
- **Async Broadcasts**: Via `asyncio.run()`

### State Machine
```
IDLE → LISTENING (user starts speaking)
LISTENING → IDLE (transcription complete)
IDLE → SPEAKING (TTS generated)
SPEAKING → IDLE (audio playback complete)
```

## Troubleshooting

### "Connection refused"
- Ensure port 5000 is not in use: `lsof -i :5000`
- Check firewall settings
- Verify Riko server is running

### "No mouth animation"
- Check browser console for WebSocket messages
- Verify `duration` field is present in speaking event
- Check Yumi's `rikoService` connection status

### "Server crashes on startup"
- Install dependencies: `pip install -r requirements.txt`
- Check Python version: Should be 3.10+
- Verify FastAPI/uvicorn installed: `pip list | grep -i fastapi`

### "WebSocket disconnects immediately"
- Check CORS settings in `websocket_server.py`
- Verify frontend URL matches allowed origins
- Check browser console for CORS errors

## Development

### Testing WebSocket Manually
```bash
# Install wscat
npm install -g wscat

# Connect to server
wscat -c ws://localhost:5000/ws

# You should receive initial idle message:
# < {"type":"idle","timestamp":1234567890.123}

# Send test message:
# > Hello Riko

# Receive echo:
# < {"type":"echo","message":"Hello Riko"}
```

### Testing with cURL
```bash
# Health check
curl http://localhost:5000/health

# Status check
curl http://localhost:5000/
```

## Technical Details

### Audio Duration Calculation
- Uses `soundfile` library (already a Riko dependency)
- Calculates exact duration from WAV file
- Sends to Yumi for precise mouth animation timing

```python
def get_wav_duration(path):
    with sf.SoundFile(path) as f:
        duration_seconds = len(f) / f.samplerate
        return int(duration_seconds * 1000)  # Convert to ms
```

### State Management
- `RikoState` class manages current state
- Prevents race conditions
- Broadcasts to all connected clients
- Handles client disconnections gracefully

### Client Management
- Set-based connection tracking
- Automatic cleanup of disconnected clients
- Supports multiple simultaneous connections

## Integration with Yumi

### Expected Frontend Implementation
```javascript
// Connect to Riko WebSocket
const ws = new WebSocket('ws://localhost:5000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'listening':
      // Show listening indicator
      break;
    case 'speaking':
      // Animate mouth for data.duration ms
      animateMouth(data.duration);
      break;
    case 'idle':
      // Return to idle state
      break;
  }
};
```

## Performance

### Latency
- WebSocket broadcast: < 10ms
- State transition: < 5ms
- No audio streaming (files sent separately)

### Resource Usage
- Minimal CPU overhead
- Memory: ~10MB per connection
- Network: Event-based, minimal traffic

## Future Enhancements (Out of Scope)
- HTTP REST endpoint for text-only chat
- Emotion detection → expression mapping
- Audio streaming instead of full file playback
- Multiple avatar support (multi-client)
- Performance metrics and latency tracking
- Authentication and security
- Reconnection handling
- Event history/replay

## License
Part of Project Riko - Voice Waifu Conversational Pipeline
