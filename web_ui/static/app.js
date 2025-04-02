// Connect to Socket.IO server
const socket = io();
let messageHistory = [];

// DOM elements
const messagesContainer = document.getElementById('messages');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const clearButton = document.getElementById('clear-button');
const statusDisplay = document.getElementById('status');
const memoryUsageDisplay = document.getElementById('memory-usage');
const useRagCheckbox = document.getElementById('use-rag');
const templateSelect = document.getElementById('template-select');
const systemPrompt = document.getElementById('system-prompt');
const updateSystemPromptButton = document.getElementById('update-system-prompt');
const temperatureSlider = document.getElementById('temperature');
const temperatureValue = document.getElementById('temperature-value');
const topPSlider = document.getElementById('top-p');
const topPValue = document.getElementById('top-p-value');
const documentsListContainer = document.getElementById('documents-list');
const fileUpload = document.getElementById('file-upload');
const uploadButton = document.getElementById('upload-button');

// Initialize UI
document.addEventListener('DOMContentLoaded', () => {
    statusDisplay.textContent = 'Connected';
    socket.emit('get_initial_data');
    
    // Set up event listeners
    temperatureSlider.addEventListener('input', () => {
        temperatureValue.textContent = temperatureSlider.value;
    });
    
    topPSlider.addEventListener('input', () => {
        topPValue.textContent = topPSlider.value;
    });
});

// Handle connection events
socket.on('connect', () => {
    statusDisplay.textContent = 'Connected';
});

socket.on('disconnect', () => {
    statusDisplay.textContent = 'Disconnected';
});

// Handle message submission
sendButton.addEventListener('click', sendMessage);
userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;
    
    // Add user message to UI
    addMessageToUI('user', message);
    
    // Clear input
    userInput.value = '';
    
    // Get parameters
    const useRag = useRagCheckbox.checked;
    const template = templateSelect.value;
    const temperature = parseFloat(temperatureSlider.value);
    const top_p = parseFloat(topPSlider.value);
    
    // Show typing indicator
    addMessageToUI('system', 'Thinking...');
    
    // Send to server
    socket.emit('user_message', {
        message,
        use_rag: useRag,
        template,
        temperature,
        top_p
    });
    
    // Save to history
    messageHistory.push({ role: 'user', content: message });
}

// Handle incoming messages
socket.on('message', (data) => {
    // Remove typing indicator (the last system message)
    const typingIndicators = document.querySelectorAll('.system-message');
    if (typingIndicators.length > 0) {
        typingIndicators[typingIndicators.length - 1].remove();
    }
    
    // Add response to UI
    addMessageToUI('assistant', data.message);
    
    // Add sources if available
    if (data.sources && data.sources.length > 0) {
        let sourcesHtml = '<div class="sources"><strong>Sources:</strong><ul>';
        data.sources.forEach(source => {
            sourcesHtml += `<li>${source}</li>`;
        });
        sourcesHtml += '</ul></div>';
        
        const lastMessage = messagesContainer.lastElementChild;
        lastMessage.innerHTML += sourcesHtml;
    }
    
    // Save to history
    messageHistory.push({ role: 'assistant', content: data.message });
});

// Memory updates
socket.on('memory_update', (data) => {
    memoryUsageDisplay.textContent = `${data.percent}% (${data.used_gb.toFixed(1)} GB)`;
    
    // Change color based on memory pressure
    if (data.percent > 85) {
        memoryUsageDisplay.style.color = 'red';
    } else if (data.percent > 70) {
        memoryUsageDisplay.style.color = 'orange';
    } else {
        memoryUsageDisplay.style.color = 'white';
    }
});

// Clear chat
clearButton.addEventListener('click', () => {
    socket.emit('clear_chat');
    messagesContainer.innerHTML = '';
    messageHistory = [];
    addMessageToUI('system', 'Chat history cleared');
});

// Update system prompt
updateSystemPromptButton.addEventListener('click', () => {
    const newPrompt = systemPrompt.value.trim();
    if (newPrompt) {
        socket.emit('update_system_prompt', { prompt: newPrompt });
        addMessageToUI('system', 'System prompt updated');
    }
});

// Utility functions
function addMessageToUI(role, content) {
    const messageElement = document.createElement('div');
    messageElement.className = `message ${role}-message`;
    
    // Process markdown-like formatting for code
    let formattedContent = content;
    
    // Handle code blocks with ```
    formattedContent = formattedContent.replace(/```([\s\S]*?)```/g, function(_match, code) {
        return `<pre><code>${escapeHtml(code.trim())}</code></pre>`;
    });
    
    // Handle inline code with `
    formattedContent = formattedContent.replace(/`([^`]+)`/g, function(_match, code) {
        return `<code>${escapeHtml(code)}</code>`;
    });
    
// Replace newlines with <br>
formattedContent = formattedContent.replace(/\n/g, '<br>');
    
    messageElement.innerHTML = formattedContent;
    messagesContainer.appendChild(messageElement);
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    return messageElement;
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
