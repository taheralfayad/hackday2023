//Change this domain to whatever your domain is:
var socket = new WebSocket('wss://d9e3-132-170-15-255.ngrok-free.app/ws/messaging/');

socket.onmessage = function(event) {
    var data = JSON.parse(event.data);
    console.log(data);

    let sendButton = document.querySelector('.chat-input button');
    sendButton.disabled = false;
    
    let chatHistory = document.getElementById('chat-history');
    let botMessageElem = document.createElement('div');
    botMessageElem.className = 'bot-message';
    botMessageElem.textContent = data.message;

    chatHistory.appendChild(botMessageElem);
};

socket.onclose = function(event) {
    if (event.wasClean) {
        alert(`Connection closed cleanly, code=${event.code}, reason=${event.reason}`);
    } else {
        alert('Connection died');
    }
};

function sendMessage() {
    let userInput = document.getElementById('user-input').value;
    let sendButton = document.querySelector('.chat-input button');

    if (userInput.trim() === '') return;

    userInput.disabled = true;
    sendButton.disabled = true;

    let chatHistory = document.getElementById('chat-history');
    let userMessageElem = document.createElement('div');
    userMessageElem.className = 'user-message';
    userMessageElem.textContent = userInput;

    chatHistory.appendChild(userMessageElem);
    
    fetch('/chatbot/message/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')  // For CSRF protection
        },
        body: 'message=' + encodeURIComponent(userInput)
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
    });

}

function getCookie(name) {
    let value = "; " + document.cookie;
    let parts = value.split("; " + name + "=");
    if (parts.length == 2) return parts.pop().split(";").shift();
}
