from faster_whisper import WhisperModel
from process.asr_func.asr_push_to_talk import record_and_transcribe
from process.llm_funcs.llm_scr import llm_response
from process.tts_func.sovits_ping import sovits_gen, play_audio
from pathlib import Path
import uuid
import asyncio
import threading
from websocket_server import riko_state, app
import uvicorn
import soundfile as sf

def get_wav_duration(path):
    with sf.SoundFile(path) as f:
        return len(f) / f.samplerate

def run_websocket_server():
    """Run FastAPI server in background thread"""
    print("\n🌐 Starting WebSocket server on port 5000...")
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="warning")

async def main_chat_loop():
    """Main chat loop with WebSocket broadcasts"""
    print('\n========= Starting Chat with WebSocket... ================\n')
    whisper_model = WhisperModel("base.en", device="cpu", compute_type="float32")
    
    while True:
        await riko_state.set_listening()
        
        conversation_recording = Path("audio") / "conversation.wav"
        conversation_recording.parent.mkdir(parents=True, exist_ok=True)
        
        user_spoken_text = record_and_transcribe(whisper_model, conversation_recording)
        
        await riko_state.set_idle()
        
        llm_output = llm_response(user_spoken_text)
        tts_read_text = llm_output
        
        uid = uuid.uuid4().hex
        filename = f"output_{uid}.wav"
        output_wav_path = Path("audio") / filename
        output_wav_path.parent.mkdir(parents=True, exist_ok=True)
        
        gen_aud_path = sovits_gen(tts_read_text, output_wav_path)
        
        await riko_state.set_speaking(tts_read_text, output_wav_path)
        
        play_audio(output_wav_path)
        
        duration = get_wav_duration(output_wav_path)
        await asyncio.sleep(duration)
        
        await riko_state.set_idle()
        
        [fp.unlink() for fp in Path("audio").glob("*.wav") if fp.is_file()]

if __name__ == "__main__":
    ws_thread = threading.Thread(target=run_websocket_server, daemon=True)
    ws_thread.start()
    
    import time
    time.sleep(2)
    
    asyncio.run(main_chat_loop())
