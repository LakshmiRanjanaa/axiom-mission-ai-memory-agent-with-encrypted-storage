# AI Memory Agent with Encrypted Storage

A personal AI assistant that remembers conversations across sessions using encrypted SQLite storage.

## Features
- Encrypted conversation storage using SQLite + cryptography
- Persistent memory across browser sessions
- Simple web interface for chat interaction
- Secure data handling with Fernet encryption

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Set your OpenAI API key: `export OPENAI_API_KEY=your_api_key_here`
3. Run the server: `python app.py`
4. Open http://localhost:5000 in your browser

## Project Structure
- `app.py` - Main Flask server and API endpoints
- `memory_agent.py` - AI agent with encrypted memory capabilities
- `templates/index.html` - Simple chat interface
- `requirements.txt` - Python dependencies

## Security Note
The encryption key is generated automatically on first run. In production, use proper key management!