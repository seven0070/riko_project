"""
Run only the WebSocket server for testing with Yumi frontend.
Useful when you want to test the connection without running the full Riko chat loop.
"""
from websocket_server import app
import uvicorn

if __name__ == "__main__":
    print("\n🚀 Riko WebSocket Server - Testing Mode")
    print("=" * 50)
    print("WebSocket: ws://localhost:5000/ws")
    print("Health: http://localhost:5000/health")
    print("=" * 50)
    print("\nWaiting for Yumi to connect...\n")
    
    uvicorn.run(app, host="0.0.0.0", port=5000)
