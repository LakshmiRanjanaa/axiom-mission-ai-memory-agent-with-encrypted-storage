from flask import Flask, request, jsonify, render_template_string
import uuid
from memory_agent import MemoryAgent

app = Flask(__name__)
agent = MemoryAgent()

# Simple HTML template embedded in Python
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>AI Memory Agent</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .chat-container { border: 1px solid #ddd; height: 400px; overflow-y: scroll; padding: 10px; margin: 10px 0; }
        .message { margin: 10px 0; padding: 8px; border-radius: 5px; }
        .user { background: #e3f2fd; text-align: right; }
        .assistant { background: #f1f8e9; }
        .input-container { display: flex; gap: 10px; }
        input[type="text"] { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .info { background: #fff3cd; padding: 10px; border-radius: 4px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <h1>AI Memory Agent</h1>
    <div class="info">
        <strong>Features:</strong> This AI remembers our conversations across browser sessions using encrypted storage!
        <br><strong>User ID:</strong> <span id="userId"></span>
    </div>
    
    <div id="chatContainer" class="chat-container"></div>
    
    <div class="input-container">
        <input type="text" id="messageInput" placeholder="Type your message..." onkeypress="if(event.key==='Enter') sendMessage()">
        <button onclick="sendMessage()">Send</button>
        <button onclick="loadHistory()">Load History</button>
    </div>

    <script>
        // Generate or retrieve user ID
        let userId = localStorage.getItem('userId') || generateUserId();
        localStorage.setItem('userId', userId);
        document.getElementById('userId').textContent = userId;
        
        function generateUserId() {
            return 'user_' + Math.random().toString(36).substr(2, 9);
        }
        
        function addMessage(content, type) {
            const chatContainer = document.getElementById('chatContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            messageDiv.innerHTML = `<strong>${type === 'user' ? 'You' : 'AI'}:</strong> ${content}`;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Show user message immediately
            addMessage(message, 'user');
            input.value = '';
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({user_id: userId, message: message})
                });
                
                const data = await response.json();
                addMessage(data.response, 'assistant');
            } catch (error) {
                addMessage('Error: Could not connect to AI', 'assistant');
            }
        }
        
        async function loadHistory() {
            try {
                const response = await fetch(`/history/${userId}`);
                const data = await response.json();
                
                const chatContainer = document.getElementById('chatContainer');
                chatContainer.innerHTML = '';
                
                data.history.forEach(msg => {
                    addMessage(msg.content, msg.type);
                });
            } catch (error) {
                console.error('Could not load history:', error);
            }
        }
        
        // Load history on page load
        window.onload = loadHistory;
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    """Serve the chat interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    data = request.get_json()
    user_id = data.get('user_id')
    message = data.get('message')
    
    if not user_id or not message:
        return jsonify({'error': 'Missing user_id or message'}), 400
    
    # Generate AI response with memory
    response = agent.generate_response(user_id, message)
    
    return jsonify({'response': response})

@app.route('/history/<user_id>')
def get_history(user_id):
    """Get conversation history for a user"""
    history = agent.get_conversation_history(user_id, limit=20)
    return jsonify({'history': history})

if __name__ == '__main__':
    print("Starting AI Memory Agent...")
    print("Make sure to set your OPENAI_API_KEY environment variable!")
    app.run(debug=True, port=5000)