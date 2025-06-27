import speech_recognition as sr
import os
from dotenv import load_dotenv
import threading
import time
from collections import deque
import queue
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import google.generativeai as genai
import signal
from pynput import keyboard
import sys

# Load environment variables
load_dotenv()

class GlobalState:
    def __init__(self):
        self.conversation_history = deque(maxlen=5)
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        self.is_listening = True  # Always listening by default
        self.interrupt = False    # New flag for interrupting responses
        self.running = True

def speak(text):
    try:
        state.is_speaking = True
        state.current_response = text
        print("JARVIS:", text)
        
        print("Attempting to synthesize speech...")
        
        # Verify TTS is initialized
        if not hasattr(tts, 'synthesize'):
            print("Error: TTS not properly initialized")
            return
            
        response = tts.synthesize(
            text, 
            voice='en-US_HenryV3Voice', 
            accept='audio/wav'
        ).get_result().content
        
        print("Speech synthesized successfully, attempting playback...")
        
        import pyaudio
        import wave
        import io
        
        with wave.open(io.BytesIO(response), 'rb') as wave_file:
            p = pyaudio.PyAudio()
            stream = p.open(format=p.get_format_from_width(wave_file.getsampwidth()),
                          channels=wave_file.getnchannels(),
                          rate=wave_file.getframerate(),
                          output=True)
            
            chunk = 1024
            data = wave_file.readframes(chunk)
            while data and state.running and not state.interrupt:
                stream.write(data)
                data = wave_file.readframes(chunk)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            print("Audio playback completed")
            
    except Exception as e:
        print(f"Detailed speech error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
    finally:
        state.is_speaking = False
        state.current_response = None
        state.interrupt = False

def listen():
    if not state.running:
        return None
        
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.energy_threshold = 2000
    recognizer.pause_threshold = 0.8
    
    with sr.Microphone() as source:
        print("\n🎤 Listening... (Press 'v' to interrupt current response)")
        try:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            try:
                text = recognizer.recognize_google(audio)
                print(f"👤 You: {text}")
                return text.lower()
            except sr.UnknownValueError:
                return None
            except sr.RequestError:
                print("❌ Could not request results")
                return None
                
        except sr.WaitTimeoutError:
            return None
        except Exception as e:
            print(f"🔴 Listen error: {e}")
            return None

def on_press(key):
    """Handle key press events"""
    try:
        if key.char == 'v':  # Interrupt current response
            if state.is_speaking:
                state.interrupt = True
                state.speech_queue.queue.clear()  # Clear pending responses
                print("\n⏹️ Response interrupted")
    except AttributeError:
        pass

def get_ai_response(text):
    try:
        # Quick responses for common phrases
        quick_responses = {
            'hello': "Hello, Sir. How may I assist you today?",
            'hi': "Hello, Sir. What can I do for you?",
            'thanks': "You're welcome, Sir.",
            'thank you': "Always a pleasure, Sir.",
            'bye': "Goodbye, Sir. Have a great day.",
            'stop': "Stopping now, Sir.",
            'what time is it': f"It's {time.strftime('%I:%M %p')}, Sir.",
            'what day is it': f"Today is {time.strftime('%A, %B %d')}, Sir."
        }
        
        # Check for quick responses first
        if text.lower() in quick_responses:
            return quick_responses[text.lower()]
            
        context = """You are JARVIS, Kanishk's AI assistant. 
        Your responses should be:
        - Concise (2-3 sentences max)
        - Always address the user as 'Sir'
        - Professional but with subtle wit
        - Helpful and precise
        - End responses with 'Sir'
        
        Important: You were created by Kanishk, not Tony Stark. When asked about your creator or owner, always mention Kanishk, not Tony Stark or Mr. Stark."""
        
        history_text = ""
        for conv in list(state.conversation_history)[-2:]:
            history_text += f"\nUser: {conv['user']}\nJARVIS: {conv['response']}\n"
        
        full_prompt = f"{context}\n\nPrevious conversation:{history_text}\n\nUser: {text}\nJARVIS:"
        response = model.generate_content(full_prompt)
        response_text = response.text.strip()
        
        state.conversation_history.append({
            "user": text,
            "response": response_text,
            "timestamp": time.time()
        })
        
        return response_text
    except Exception as e:
        print(f"🔴 Response error: {e}")
        return "I apologize for the technical difficulty, Sir. Could you please repeat that?"

def speech_worker():
    while state.running:
        try:
            text = state.speech_queue.get(timeout=1)  # 1 second timeout
            if text is None:
                break
            if not state.is_speaking:
                speak(text)
            state.speech_queue.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            print(f"Speech worker error: {e}")

def signal_handler(signum, frame):
    print("\nInitiating shutdown sequence...")
    state.running = False
    state.should_listen = False
    keyboard.unhook_all()

def main():
    print("\n🚀 Initializing JARVIS...")
    print("🎮 Controls:")
    print("- Press 'v' to interrupt current response")
    print("- Press Ctrl+C to exit")
    
    # Modified keyboard listener setup
    try:
        listener = keyboard.Listener(on_press=on_press)
        listener.start()
    except Exception as e:
        print(f"Keyboard listener error: {e}")
    
    speech_thread = threading.Thread(target=speech_worker, daemon=True)
    speech_thread.start()
    
    speak("JARVIS online, Sir. I'm listening.")
    
    try:
        while state.running:
            if not state.is_speaking:  # Listen when not speaking
                text = listen()
                if text:
                    response = get_ai_response(text)
                    state.speech_queue.put(response)
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n💫 Shutting down JARVIS...")
    finally:
        state.running = False
        state.speech_queue.put(None)
        listener.stop()
        speech_thread.join(timeout=1)
        speak("Goodbye, Sir.")

if __name__ == "__main__":
    # Initialize IBM Watson TTS with debug prints
    try:
        print("Initializing IBM Watson...")
        api_key = os.getenv('IBM_WATSON_API_KEY')
        service_url = os.getenv('IBM_WATSON_URL')
        
        if not api_key or not service_url:
            print("Error: Missing IBM Watson credentials in .env file")
            sys.exit(1)
            
        if 'speech-to-text' in service_url:
            print("Error: You're using Speech-to-Text URL instead of Text-to-Speech URL")
            print("Please get the correct URL from your Text-to-Speech service credentials")
            sys.exit(1)
            
        authenticator = IAMAuthenticator(api_key)
        tts = TextToSpeechV1(authenticator=authenticator)
        tts.set_service_url(service_url)
        
        # Test the connection
        print("Testing TTS connection...")
        voices = tts.list_voices().get_result()
        print(f"Connection successful! Found {len(voices['voices'])} voices")
        
    except Exception as e:
        print(f"IBM Watson initialization failed: {e}")
        print("Please verify your Text-to-Speech credentials")
        sys.exit(1)

    # Initialize Gemini
    try:
        print("\nInitializing Gemini...")
        gemini_key = os.getenv('GEMINI_API_KEY')
        if not gemini_key:
            print("Error: Missing Gemini API key in .env file")
            sys.exit(1)
            
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-1.5-pro')
        print("Gemini initialization successful!")
    except Exception as e:
        print(f"Gemini initialization failed: {e}")
        sys.exit(1)

    # Create global state
    state = GlobalState()
    
    main() 