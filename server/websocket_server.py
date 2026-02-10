from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from typing import Set
from pathlib import Path
import soundfile as sf

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connected_clients: Set[WebSocket] = set()

def get_wav_duration(path):
    """Calculate audio duration in milliseconds"""
    try:
        with sf.SoundFile(path) as f:
            duration_seconds = len(f) / f.samplerate
            return int(duration_seconds * 1000)
    except Exception as e:
        print(f"Error getting duration: {e}")
        return 2000

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    print(f"✅ Yumi connected! Total clients: {len(connected_clients)}")
    
    try:
        await websocket.send_json({
            "type": "idle",
            "timestamp": asyncio.get_event_loop().time()
        })
        
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({
                "type": "echo",
                "message": data
            })
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        connected_clients.discard(websocket)
        print(f"❌ Yumi disconnected. Remaining: {len(connected_clients)}")

async def broadcast(message: dict):
    """Broadcast message to all connected clients"""
    if not connected_clients:
        return
    
    disconnected = set()
    for client in connected_clients:
        try:
            await client.send_json(message)
        except Exception:
            disconnected.add(client)
    
    for client in disconnected:
        connected_clients.discard(client)

class RikoState:
    def __init__(self):
        self.is_listening = False
        self.is_speaking = False
    
    async def set_listening(self):
        self.is_listening = True
        self.is_speaking = False
        await broadcast({
            "type": "listening",
            "timestamp": asyncio.get_event_loop().time()
        })
        print("📡 Broadcasting: LISTENING")
    
    async def set_speaking(self, text: str, audio_path: Path):
        self.is_listening = False
        self.is_speaking = True
        duration = get_wav_duration(audio_path)
        
        await broadcast({
            "type": "speaking",
            "text": text,
            "duration": duration,
            "timestamp": asyncio.get_event_loop().time()
        })
        print(f"📡 Broadcasting: SPEAKING (duration: {duration}ms)")
    
    async def set_idle(self):
        self.is_listening = False
        self.is_speaking = False
        await broadcast({
            "type": "idle",
            "timestamp": asyncio.get_event_loop().time()
        })
        print("📡 Broadcasting: IDLE")

riko_state = RikoState()

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Riko WebSocket Server",
        "connected_clients": len(connected_clients)
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "clients": len(connected_clients)}

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting Riko WebSocket Server on ws://localhost:5000/ws\n")
    uvicorn.run(app, host="0.0.0.0", port=5000)
