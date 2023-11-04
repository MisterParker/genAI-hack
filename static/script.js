// script.js
function showMessage(subject) {
    var chatContainer = document.getElementById('chat-container');
    var message = `Welcome to ${subject}! Here's what you need to work on today...`;
    chatContainer.innerHTML = `<div class="message">${message}</div>`;
}

function sendMessage() {
    var chatInput = document.getElementById('chat-input');
    var chatContainer = document.getElementById('chat-container');
    var userMessage = chatInput.value;
    chatContainer.innerHTML += `<div class="message user-message">${userMessage}</div>`;
    // You can add code here to send the message to the server and get a response
    chatInput.value = '';
}
