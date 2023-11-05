// Global variable to store the selected subject
let selectedSubject = null;

// Function to display a message in the chat area
function displayMessage(sender, message, subject) {
    // Create message element
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', `${sender}-message`);
    
    // Create content element
    const contentElement = document.createElement('div');
    contentElement.classList.add('message-content');
    contentElement.textContent = message;
    
    // Append content to message
    messageElement.appendChild(contentElement);
    
    // Append message to chat area
    document.getElementById(`chat-area-${subject}`).appendChild(messageElement);
}

// Function to set the subject and initialize chat
function setSubject(subject) {
    // Hide all chat areas
    const chatAreas = document.querySelectorAll('.chat-area');
    chatAreas.forEach(chatArea => {
        chatArea.style.display = 'none';
    });

    // Show the selected chat area
    document.getElementById(`chat-area-${subject}`).style.display = 'block';
    selectedSubject = subject;  // Set the selected subject globally

    // Display the default message
    displayMessage('bot', `Hello! Today, you need to work on ${subject}. How can I assist you?`, subject);
    
    // Set subject on server
    fetch('/set_subject', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `subject=${subject}`
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            alert('Failed to set subject.');
        }
    });
}

// Function to send a message
function sendMessage() {
    // Get user input
    const inputElement = document.getElementById('chat-input');
    const userMessage = inputElement.value;
    inputElement.value = '';

    // Display user message
    displayMessage('user', userMessage, selectedSubject);

    // Fetch response from server
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ user_input: userMessage })
    })
    .then(response => response.json())
    .then(data => {
        // Display bot response
        displayMessage('bot', data.response, selectedSubject);
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Function to generate quiz
function generateQuiz() {
    // Fetch quiz from server
    fetch('/generate_quiz_v2')
    .then(response => response.json())
    .then(data => {
        // Display quiz
        displayMessage('bot', data.quiz, selectedSubject);
        console.log(data);
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

