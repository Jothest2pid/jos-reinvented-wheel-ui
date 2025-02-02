# AI Chat Interface

A Flask-based web application that provides a chat interface for interacting with AI models through Ollama. Features include chat history management, model selection, and system prompt customization.

## Requirements

- Python 3.8+
- Flask
- Ollama (running locally)
- SQLite3

## Installation

1. Clone the repository:
```bash
git clone [your-repository-url]
cd [repository-name]
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Ensure Ollama is installed and running locally:
- Install Ollama from [https://ollama.com](https://ollama.com)
- Start the Ollama service
- Download at least one model using `ollama pull [model-name]`

## Usage

1. Start the Flask application:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

## Features

- Real-time chat interface with AI models
- Support for multiple Ollama models
- Chat history management (save, load, rename, delete)
- Custom system prompts
- Markdown formatting support
- Thought process visualization
- Function calling capabilities

## Project Structure

```
.
├── app.py              # Main Flask application
├── database.py         # Database operations
├── requirements.txt    # Python dependencies
├── static/
│   └── styles.css     # CSS styles
└── templates/
    └── index.html     # Main HTML template
```

## Database

The application uses SQLite for storing chat history. The database schema includes:
- `saved_chats`: Stores chat metadata
- `saved_messages`: Stores individual messages within chats

## Security Notes

- This application is designed to run locally
- Ensure Ollama is properly configured and secured
- Do not expose the application to the internet without proper security measures

## License

[Your License Here]
