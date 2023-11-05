from flask import Flask, request, jsonify, session, send_from_directory
from langchain.document_loaders import PyPDFLoader
from langchain.indexes import VectorstoreIndexCreator as VSICreator
import os
from glob import glob
import traceback
from flask_cors import CORS

app = Flask(__name__, static_url_path='', static_folder='static')
app.secret_key = 'ABCDEF45654'  # Change this to a random secret key
CORS(app)
app.config['SESSION_COOKIE_SECURE'] = False
os.environ['OPENAI_API_KEY'] = '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'

class Chatbot:
    def __init__(self):
        self.vectorstore_index = None
        self.memory = {}
        self.chat_log = []
        self.context = []

    def set_vectorstore_index(self, subject):
        # Dynamically select PDF files based on subject
        parent_directory = "documents"
        subject_directory = os.path.join(parent_directory, subject)
        pdf_files = []
        for root, dirs, files in os.walk(subject_directory):
            for file in files:
                if file.endswith(".pdf"):
                    file_path = os.path.join(root, file)
                    pdf_files.append(file_path)
        
        loaders = [PyPDFLoader(pdf) for pdf in pdf_files]
        self.vectorstore_index = VSICreator().from_loaders(loaders)

    def query_vectorstore(self, query):
        query_answer = self.vectorstore_index.query_with_sources(query)
        return query_answer['answer']

    def ask(self, question, chat_history):
        memory_key = f'{session["subject"]}_{question}'
        if question.lower() == "reset":
            self.reset_context()
            return {"response": "Context has been reset."}

        if memory_key in self.memory:
            response = self.memory[memory_key]
        else:
            answer = self.query_vectorstore(question)
            response = answer if answer else "I don't know the answer to that question."
            self.memory[memory_key] = response

        response_dict = {'user_input': question, 'response': response}
        chat_history.append(response_dict)
        return response_dict

chatbot = Chatbot()

@app.route('/')
def index():
    return send_from_directory('static', 'index_working.html')

@app.route('/select_subject', methods=['POST'])
def select_subject():
    subject = request.json['subject']
    session['chat_history'] = []
    session['subject'] = subject
    chatbot.set_vectorstore_index(subject)
    return jsonify({'message': f"Welcome to {subject}! Here's what you need to work on today..."})

@app.route('/set_subject', methods=['POST'])
def set_subject():
    subject = request.form['subject']
    session['subject'] = subject
    chatbot.set_vectorstore_index(subject)
    return jsonify({'success': True})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        print("Received request:", request.json)
        user_input = request.json.get('user_input')
        subject = session.get('subject')

        print("User input:", user_input)
        print("Subject:", subject)

        if not subject:
            print("Error: Subject not selected")
            return jsonify({'error': 'Subject not selected'}), 400

        chat_history_key = f'chat_history_{subject}'
        chat_history = session.get(chat_history_key, [])
        response = chatbot.ask(user_input, chat_history)
        session[chat_history_key] = chat_history
        return jsonify(response)
    except Exception as e:
        print("An error occurred: ", str(e))
        traceback.print_exc()
        return jsonify({'error': 'An unexpected error occurred'}), 500

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
    app.run(debug=True, port=5006)