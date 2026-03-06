import sqlite3
import json
import os
from datetime import datetime
from cryptography.fernet import Fernet
from openai import OpenAI

class MemoryAgent:
    def __init__(self, db_path="conversations.db", key_path="encryption.key"):
        self.db_path = db_path
        self.key_path = key_path
        
        # Initialize encryption
        self.cipher = self._get_or_create_cipher()
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Create database if it doesn't exist
        self._init_database()
    
    def _get_or_create_cipher(self):
        """Get existing encryption key or create a new one"""
        if os.path.exists(self.key_path):
            with open(self.key_path, 'rb') as key_file:
                key = key_file.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_path, 'wb') as key_file:
                key_file.write(key)
        return Fernet(key)
    
    def _init_database(self):
        """Initialize the encrypted SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                encrypted_message BLOB,
                message_type TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _encrypt_data(self, data):
        """Encrypt data before storing"""
        return self.cipher.encrypt(json.dumps(data).encode())
    
    def _decrypt_data(self, encrypted_data):
        """Decrypt data after retrieving"""
        return json.loads(self.cipher.decrypt(encrypted_data).decode())
    
    def store_message(self, user_id, message, message_type):
        """Store encrypted message in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        encrypted_message = self._encrypt_data({
            'content': message,
            'metadata': {'length': len(message)}
        })
        
        cursor.execute('''
            INSERT INTO conversations (user_id, encrypted_message, message_type)
            VALUES (?, ?, ?)
        ''', (user_id, encrypted_message, message_type))
        
        conn.commit()
        conn.close()
    
    def get_conversation_history(self, user_id, limit=10):
        """Retrieve and decrypt conversation history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT encrypted_message, message_type, timestamp
            FROM conversations 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        history = []
        for row in cursor.fetchall():
            decrypted_data = self._decrypt_data(row[0])
            history.append({
                'content': decrypted_data['content'],
                'type': row[1],
                'timestamp': row[2]
            })
        
        conn.close()
        return list(reversed(history))  # Return in chronological order
    
    def generate_response(self, user_id, user_message):
        """Generate AI response with memory context"""
        # Store user message
        self.store_message(user_id, user_message, 'user')
        
        # Get conversation history for context
        history = self.get_conversation_history(user_id, limit=5)
        
        # Build context for AI
        messages = [{"role": "system", "content": "You are a helpful AI assistant with memory of past conversations. Reference previous context when relevant."}]
        
        for msg in history[:-1]:  # Exclude the current message
            role = "user" if msg['type'] == 'user' else "assistant"
            messages.append({"role": role, "content": msg['content']})
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        # Get AI response
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
            # Store AI response
            self.store_message(user_id, ai_response, 'assistant')
            
            return ai_response
            
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            self.store_message(user_id, error_msg, 'assistant')
            return error_msg