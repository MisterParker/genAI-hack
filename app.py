from flask import Flask, request, jsonify, session, send_from_directory
from langchain.document_loaders import PyPDFLoader
from langchain.indexes import VectorstoreIndexCreator as VSICreator
import os
import traceback
from flask_cors import CORS
import pdfplumber
import openai
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__, static_url_path='', static_folder='static')
app.secret_key = 'ABCDEF45654'
CORS(app)
app.config['SESSION_COOKIE_SECURE'] = False
openai_api_key = os.getenv('OPENAI_API_KEY')
os.environ['OPENAI_API_KEY'] = openai_api_key

# Global variable to store the summary
generated_summary = ""

def call_gpt_model(prompt):
    # Simulate calling a GPT-based model to generate a quiz based on the prompt
    # Here we simply generate some mock questions based on the prompt
    # In a real-world scenario, you would replace this with an API call to a GPT-based model.

    # Extracting document text and chat history from the prompt
    doc_start = prompt.find("Based on the document text:\n\n") + len("Based on the document text:\n\n")
    chat_start = prompt.find("\n\nand the chat history:\n\n") + len("\n\nand the chat history:\n\n")
    document_text = prompt[doc_start:chat_start - len("\n\nand the chat history:\n\n")].strip()
    chat_history_text = prompt[chat_start:].strip()

    # Simulating the generation of quiz questions
    quiz_questions = []
    for i in range(10):
        question = f"Q{i+1}: What is the main idea of the text in document section {i+1}?"
        options = ["Option A", "Option B", "Option C", "Option D"]
        correct_option = "Option A"
        quiz_questions.append(f"{question}\nOptions:\n  A. {options[0]}\n  B. {options[1]}\n  C. {options[2]}\n  D. {options[3]}\nCorrect Option: {correct_option}\n")

    # Combining the quiz questions into a quiz
    quiz = "Here's your quiz:\n\n" + "\n".join(quiz_questions)
    return quiz


class Chatbot:
    def __init__(self):
        self.vectorstore_index = None
        self.memory = {}
        self.chat_log = []
        self.context = []

    def set_vectorstore_index(self, subject):
        parent_directory = "documents"
        subject_directory = os.path.join(parent_directory, subject)
        pdf_files = [os.path.join(root, file) for root, _, files in os.walk(subject_directory) for file in files if file.endswith(".pdf")]
        loaders = [PyPDFLoader(pdf) for pdf in pdf_files]
        self.vectorstore_index = VSICreator().from_loaders(loaders)

    def query_vectorstore(self, query):
        try:
            query_answer = self.vectorstore_index.query(query)
            print("Query Answer:", query_answer)
            
            return query_answer
        except Exception as e:
            print("Error querying vectorstore:", str(e))
            return None

    def ask(self, question, chat_history):
        memory_key = f'{session["subject"]}_{question}'
        if question.lower() == "reset":
            self.reset_context()
            return {"response": "Context has been reset."}
        
        if "generate a quiz" in question.lower():
            quiz = self.generate_quiz_based_on_history(chat_history)
            response_dict = {'user_input': question, 'response': quiz}
            chat_history.append(response_dict)
            return response_dict

        if memory_key in self.memory:
            response = self.memory[memory_key]
        else:
            try:
                # Query the vectorstore for an answer
                answer = self.query_vectorstore(question)
                response = answer if answer else "I'm sorry, I couldn't fetch the information you requested."
            except Exception as e:
                print("Error querying vectorstore:", str(e))
                response = "I'm sorry, I couldn't fetch the information you requested."

            self.memory[memory_key] = response

        response_dict = {'user_input': question, 'response': response}
        chat_history.append(response_dict)
        return response_dict
    
    def extract_text_from_pdfs(self, subject):
        parent_directory = "documents"
        subject_directory = os.path.join(parent_directory, subject)
        pdf_files = [os.path.join(root, file) for root, _, files in os.walk(subject_directory) for file in files if file.endswith(".pdf")]
        documents_text = []

        for pdf_path in pdf_files:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for i in range(len(pdf.pages)):
                    page = pdf.pages[i]
                    text += page.extract_text()
            documents_text.append(text)

        return documents_text
    
    def generate_quiz_based_on_history(self, chat_history):
        try:
            subject = session.get('subject')
            documents_text = self.extract_text_from_pdfs(subject)

            # Combine document text and chat history
            combined_text = "\n".join(documents_text + [chat['user_input'] + '\n' + chat['response'] for chat in chat_history])

            # Split combined text into chunks of a certain size
            chunk_size = 500  # You can adjust the chunk size
            chunks = [combined_text[i:i+chunk_size] for i in range(0, len(combined_text), chunk_size)]

            openai.api_key = openai_api_key
            
            # Summarize each chunk
            summarized_chunks = []
            for chunk in chunks:
                summary_response = openai.Completion.create(
                    engine="gpt-3.5-turbo-16k",
                    prompt=f"Please summarize the following text in 100 words or less:\n\n{chunk}",
                    max_tokens=200,  # Adjust as needed
                    temperature=0.5
                )
                summarized_chunks.append(summary_response.choices[0].text.strip())

            # Combine summarized chunks and generate quiz questions
            summarized_text = "\n".join(summarized_chunks)
            prompt = f"Based on the document text:\n\n{summarized_text}\n\nGenerate 10 multiple-choice quiz questions."

            # Call the OpenAI API to generate quiz questions
            # text-davinci-002 gpt-3.5-turbo-16k
            quiz_response = openai.completion.create(
                engine="text-davinci-002",
                prompt=prompt,
                max_tokens=100,  # Adjust as needed
                temperature=0.5
            )

            quiz = quiz_response.choices[0].text.strip()

            return f"Here's your quiz:\n\n{quiz}"
        except Exception as e:
            print("An error occurred while generating quiz: ", str(e))
            return "I'm sorry, I couldn't generate the quiz."


chatbot = Chatbot()

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/teacher')
def teacher_index():
    print("Teacher route hit")  # Add this line
    return send_from_directory('static', 'index_teacher.html')

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
        user_input = request.json.get('user_input')
        subject = session.get('subject')
        print('user_input: ', user_input)
        print('subject ', subject)
        if not subject:
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

@app.route('/get_summary', methods=['GET'])
def get_summary():
    global generated_summary
    return jsonify({'summary': generated_summary})

@app.route('/generate_quiz_v2', methods=['GET'])
def generate_quiz():
    subject = session.get('subject')
    if not subject:
        return jsonify({'error': 'Subject not selected'}), 400

    chat_history_key = f'chat_history_{subject}'
    chat_history = session.get(chat_history_key, [])
    quiz = chatbot.generate_quiz_based_on_history(chat_history)
    return jsonify({'quiz': quiz})

@app.route('/summarize', methods=['POST'])
def summarize_text():
    global generated_summary
    try:
        data = request.json
        text = data.get('text', '')
        subject = data.get('subject', '')
        print('text received for summarizing: ', text)
        print('subject received: ', subject)

        # Replace the following lines with actual summarization logic using OpenAI
        openai.api_key = openai_api_key  # Replace with your OpenAI API key

        # Call the OpenAI API to get the summary
        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=f"Please summarize the following text in a 50 words or less:\n\n{text}",
            max_tokens=100,  # You can adjust the length of the summary
            temperature=0.5
        )

        print('response received: ', response)
        summary = response.choices[0].text.strip()
        print("Generated summary:", summary)  # Debug print
        generated_summary = summary
        return jsonify({'subject': subject, 'summary': summary})
    except Exception as e:
        print("An error occurred: ", str(e))
        return jsonify({'error': 'An unexpected error occurred'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5006)
