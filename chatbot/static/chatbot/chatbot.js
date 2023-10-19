function sendMessage() {
    let userInput = document.getElementById('user-input').value;
    let sendButton = document.querySelector('.chat-input button');

    if (userInput.trim() === '') return;

    userInput.disabled = true;
    sendButton.disabled = true;
    document.getElementById('chatbot-working').style.display = 'block';

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
