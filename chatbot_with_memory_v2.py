import os
import glob
import openai
from langchain.document_loaders import PyPDFLoader
from langchain.indexes import VectorstoreIndexCreator
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
import html2text

load_dotenv()

app = Flask(__name__, static_url_path='', static_folder='static')

chat_log = []

# Initialize the OpenAI GPT-3 API with your API Key
openai.api_key = os.getenv('OPENAI_API_KEY')

pages = []
loaders = []

pdf_files = glob.glob("*.pdf")

for pdf_file in pdf_files:
    loader = PyPDFLoader(pdf_file)
    loaders.append(loader)

vectorstore_index = VectorstoreIndexCreator().from_loaders(loaders)


class Chatbot:
    def __init__(self, vectorstore_index):
        self.vectorstore_index = vectorstore_index
        self.memory = {}
        self.context = []

    def query_vectorstore(self, query):
        return self.vectorstore_index.query(query)

    def update_context(self, user_input, bot_output):
        self.context = [user_input, bot_output]

    def reset_context(self):
        self.context = []
        self.memory = {}

    def ask(self, question):
        if question.lower() == "reset":
            self.reset_context()
            return "Context has been reset."

        if question in self.memory:
            return self.memory[question]

        context_with_question = self.context + [question]
        answer = self.query_vectorstore(' '.join(context_with_question))

        # If the vectorstore index cannot answer the question, use GPT-3
        if not answer:
            gpt_response = openai.Completion.create(
                engine="text-davinci-002",
                prompt=question,
                max_tokens=100,
                temperature=0.6
            )
            answer = gpt_response.choices[0].text.strip()
            answer = "Generic: " + answer

        self.memory[question] = answer
        return answer

# Authentication decorator
def authenticated_request(func):
    """Decorator for authenticated API calls"""
    def decorator(*args, **kwargs):
        try:
            # Get the access code from the environment variable
            access_code = os.getenv('ACCESS_CODE')
            if request.headers.get('Authorization') == access_code:
                return_val = func(*args, **kwargs)
                print(f"{func.__name__} returns: {return_val}")
                return return_val
            else:
                print("Error: Invalid Authentication")
                return "Error: Invalid Authentication"
        except Exception as e:
            print("Error: ", e)
            return f"Error: {e}"

    return decorator

chatbot = Chatbot(vectorstore_index)

@app.route(f'/health')
def health():
    return 'OK'

@app.route(f'/check_access_code', methods=['POST'])
def check_access_code():
    # Retrieve entered code from the request
    entered_code = request.form['code']
    
    # Check it against the one from the environment variable
    if entered_code == os.getenv('ACCESS_CODE'):
        return jsonify({'valid': True})
    else:
        return jsonify({'valid': False})

@app.route('/')
def index():
    return send_from_directory('static', 'index_local.html')


@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form['user_input']
    response = chatbot.ask(user_input)
    plain_text_response = html2text.html2text(response)
    cleaned_response = ' '.join(plain_text_response.strip().split())
    formatted_response = cleaned_response

    chat_log.append({'user_input': user_input, 'response': formatted_response})

    # Update the chatbot's context with the user input and bot's output
    if user_input.lower() != "reset":
        chatbot.update_context(user_input, formatted_response)

    return jsonify({'response': formatted_response})


if __name__ == '__main__':
    app.debug = True
    app.run(port=5003)
