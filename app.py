# jos-reinvented-wheel-ui
# Copyright (C) 2025 Jothest2pid 
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from flask import Flask, render_template, request, Response, stream_with_context, jsonify
import json
import requests
import random
import re
from database import init_db, save_chat, get_saved_chats, get_saved_chat, delete_saved_chat, rename_saved_chat

app = Flask(__name__)

init_db()

chat_memory = []

functions = {
    'random_number': {
        'description': 'This generates a random number in a range, ex. usage: random_number(1,10)',
        'execute': lambda min_val, max_val: random.randint(int(min_val), int(max_val))
    },
    'check_description': {
        'description': 'Returns the description of any function',
        'execute': lambda func_name: functions[func_name]['description'] if func_name in functions else "Function not found"
    }
}

STATIC_PROMPT = """You are an AI who does exactly what they are told"""

def process_function_calls(response):
    check_desc_regex = r'check_description\(["\'](.+?)["\']\)'
    random_number_regex = r'random_number\((\d+),(\d+)\)'
    
    import re
    
    check_match = re.search(check_desc_regex, response)
    if check_match:
        func_name = check_match[1]
        result = functions['check_description']['execute'](func_name)
        response = re.sub(check_desc_regex, "FUNCTION RAN", response, count=1)
        return response, {'role': 'function', 'content': str(result)}
    
    random_match = re.search(random_number_regex, response)
    if random_match:
        min_val, max_val = random_match.groups()
        result = functions['random_number']['execute'](min_val, max_val)
        response = re.sub(random_number_regex, "FUNCTION RAN", response, count=1)
        return response, {'role': 'function', 'content': str(result)}
    
    return response, None

def format_markdown(text):
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    return text

def process_thought_brackets(content):
    pattern = r'<think>(.*?)</think>'
    
    def replace_thought(match):
        thought = match.group(1).strip()
        thought = format_markdown(thought)
        lines = thought.count('\n') + 1
        unique_id = f'thought_{hash(thought) & 0xFFFFFF}'
        return f'''<div class="thought-box">
    <div class="thought-header" onclick="toggleThought('{unique_id}')">
        <span class="toggle-icon">▶</span> THOUGHT FOR {lines} LINES
    </div>
    <div id="{unique_id}" class="thought-content collapsed">
        {thought}
    </div>
</div>'''
    
    processed = re.sub(pattern, replace_thought, content, flags=re.DOTALL)
    processed = re.sub(r'<think>.*$', '', processed, flags=re.DOTALL)
    
    return processed

@app.route('/save_chat', methods=['POST'])
def save_current_chat():
    global chat_memory
    data = request.json
    chat_name = data.get('name', 'Unnamed Chat')
    
    if chat_memory:
        chat_id = save_chat(chat_name, chat_memory)
        return jsonify({'id': chat_id, 'status': 'success'})
    return jsonify({'status': 'error', 'message': 'No chat to save'})

@app.route('/saved_chats', methods=['GET'])
def list_saved_chats():
    chats = get_saved_chats()
    return jsonify(chats)

@app.route('/saved_chats/<int:chat_id>', methods=['GET'])
def load_saved_chat(chat_id):
    global chat_memory
    saved_chat = get_saved_chat(chat_id)
    if saved_chat:
        chat_memory = saved_chat['messages']
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Chat not found'})

@app.route('/saved_chats/<int:chat_id>', methods=['DELETE'])
def remove_saved_chat(chat_id):
    delete_saved_chat(chat_id)
    return jsonify({'status': 'success'})

@app.route('/saved_chats/<int:chat_id>/rename', methods=['POST'])
def update_saved_chat_name(chat_id):
    data = request.json
    rename_saved_chat(chat_id, data['name'])
    return jsonify({'status': 'success'})

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    global chat_memory
    chat_memory = []
    return jsonify({'status': 'success'})

@app.route('/models', methods=['GET'])
def get_models():
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.ok:
            models = response.json()
            if not models.get('models'):
                return jsonify({'error': 'No models found. Please download a model using: ollama pull <model-name>'}), 400
            return jsonify(models)
        return jsonify({'error': 'Failed to fetch models'}), 500
    except Exception as e:
        return jsonify({'error': 'Failed to connect to Ollama. Is it running?'}), 500

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    global chat_memory
    data = request.json
    user_message = data.get('messages', [])[-1] if data.get('messages') else None
    additional_prompt = data.get('additional_prompt', '')

    if not data.get('model'):
        return jsonify({'error': 'No model selected. Please select a model to continue.'}), 400

    if not chat_memory:
        chat_memory = [{"role": "system", "content": STATIC_PROMPT}]
        if additional_prompt:
            chat_memory.append({"role": "system", "content": additional_prompt})
    
    if user_message:
        chat_memory.append(user_message)

    def generate():
        model = data.get('model')
        api_data = {
            "model": model,
            "messages": chat_memory,
            "stream": True
        }

        response = requests.post(
            "http://localhost:11434/api/chat",
            json=api_data,
            stream=True
        )

        accumulated_response = ""
        current_chunk = ""
        
        for line in response.iter_lines():
            if line:
                try:
                    line_data = json.loads(line)
                    if "message" in line_data:
                        content = line_data["message"]["content"]
                        accumulated_response += content
                        
                        processed_response, function_result = process_function_calls(accumulated_response)
                        if function_result:
                            chat_memory.append(function_result)
                            yield f"data: {json.dumps({'type': 'function', 'content': function_result['content']})}\n\n"
                            accumulated_response = processed_response
                        
                        current_chunk += content
                        yield f"data: {json.dumps({'type': 'generating'})}\n\n"
                except json.JSONDecodeError:
                    continue

        if accumulated_response:
            processed_response = process_thought_brackets(accumulated_response)
            formatted_response = format_markdown(processed_response)
            yield f"data: {json.dumps({'type': 'content', 'content': formatted_response})}\n\n"
            chat_memory.append({"role": "assistant", "content": formatted_response})

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)
