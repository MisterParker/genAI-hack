from flask import Flask, request, jsonify, session, send_from_directory
import os

app = Flask(__name__, static_url_path='', static_folder='static')
app.secret_key = 'your_secret_key'  # Change this to a random secret key

DOCUMENTS = {
    'Mathematics': ["Math content 1", "Math content 2"],
    'Science': ["Science content 1", "Science content 2"],
    'History': ["History content 1", "History content 2"],
}

class Chatbot:
    def __init__(self):
        pass

    def query_vectorstore(self, query):
        # Simplified query to vector store
        return "Echo: " + query, "Sample Source"

    def ask(self, question, chat_history):
        answer, source = self.query_vectorstore(question)
        response = {'user_input': question, 'response': answer, 'source': source}
        chat_history.append(response)
        return response

chatbot = Chatbot()

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/select_subject', methods=['POST'])
def select_subject():
    subject = request.json['subject']
    if subject not in DOCUMENTS:
        return jsonify({'error': 'Invalid subject'}), 400
    session['chat_history'] = []
    session['subject'] = subject
    return jsonify({'message': f"Welcome to {subject}! Here's what you need to work on today..."})


@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json['user_input']
    subject = session.get('subject')
    if not subject:
        return jsonify({'error': 'Subject not selected'}), 400
    chat_history = session.get('chat_history', [])
    response = chatbot.ask(user_input, chat_history)
    session['chat_history'] = chat_history
    return jsonify(response)


@app.route('/generate_quiz', methods=['GET'])
def generate_quiz():
    subject = session.get('subject')
    if not subject:
        return jsonify({'error': 'Subject not selected'}), 400
    chat_history = session.get('chat_history', [])
    quiz_request = "Based on above progress, generate a 10 question MCQ quiz"
    response = chatbot.ask(quiz_request, chat_history)
    session['chat_history'] = chat_history
    return jsonify({'quiz': response['response']})

if __name__ == '__main__':
    app.run(debug=True)
