# JARVIS - Voice Assistant

A voice-enabled AI assistant inspired by Iron Man's JARVIS, powered by IBM Watson Text-to-Speech and Google's Gemini AI.

## Prerequisites

- Python 3.8 or higher
- Microphone and speakers
- IBM Watson Text-to-Speech API credentials
- Google Gemini API key

## Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd jarvis
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Add your API keys and credentials:
     - `IBM_WATSON_API_KEY`: Your IBM Watson API key
     - `IBM_WATSON_URL`: Your IBM Watson Text-to-Speech service URL
     - `GEMINI_API_KEY`: Your Google Gemini API key

4. Run JARVIS:
```bash
python jarvis.py
```

## Usage

- JARVIS starts listening automatically when launched
- Press 'v' to interrupt the current response
- Press Ctrl+C to exit

## Features

- Voice input/output interaction
- Natural language processing with Google Gemini
- High-quality text-to-speech with IBM Watson
- Context-aware conversations
- Quick responses for common queries

## Note

For macOS users, you might need to install portaudio before installing pyaudio:
```bash
brew install portaudio
``` 