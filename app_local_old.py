import os
import glob
from langchain.document_loaders import PyPDFLoader
from langchain.indexes import VectorstoreIndexCreator as VSICreator
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
import html2text
from chatbot import Chatbot

load_dotenv()

# Load the OpenAI environment
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
# BASE_API_ENDPOINT = os.environ['BASE_API_ENDPOINT']

app = Flask(__name__, static_url_path='', static_folder='static')

pdf_files = []

# Specify the parent directory
parent_directory = "documents"

pdf_files = []
# Walk through all directories and subdirectories
for root, dirs, files in os.walk(parent_directory):
    for file in files:
        if file.endswith(".pdf"):
            # Get the absolute file path
            file_path = os.path.join(root, file)
            pdf_files.append(file_path)

print(pdf_files)

loaders = [PyPDFLoader(pdf) for pdf in pdf_files]
vectorstore_index = VSICreator().from_loaders(loaders)
chatbot = Chatbot(vectorstore_index)

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

@app.route(f'/chat', methods=['POST'])
@authenticated_request  # Apply authentication to the chat endpoint
def chat():
    # Retrieve user input from the request
    user_input = request.form['user_input']

    # Process the user input using the chatbot
    response, sources = chatbot.ask(user_input)

    # Return the response to the user
    return jsonify({'response': response, 'sources': sources})


if __name__ == '__main__':
    app.debug = True
    app.run(port=5005)
