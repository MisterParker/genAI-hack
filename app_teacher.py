from flask import Flask, request, jsonify, send_from_directory
import os

app = Flask(__name__, static_url_path='', static_folder='static')

@app.route('/')
def index():
    return send_from_directory('static', 'index_teacher.html')

@app.route('/summarize', methods=['POST'])
def summarize_text():
    try:
        data = request.json
        text = data.get('text', '')

        # Here you can add your logic to summarize the text
        # For simplicity, let's assume the summary is the same as the input text
        summary = text  # Replace with actual summarization logic

        return jsonify({'summary': summary})
    except Exception as e:
        print("An error occurred: ", str(e))
        return jsonify({'error': 'An unexpected error occurred'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5003)
