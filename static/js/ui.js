class UI {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
    }
    
    addMessage(content, isUser = false) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        
        const icon = document.createElement('i');
        icon.className = isUser ? 'fas fa-user' : 'fas fa-robot';
        avatar.appendChild(icon);
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (isUser) {
            const messageText = document.createElement('p');
            messageText.textContent = content;
            messageContent.appendChild(messageText);
        } else {
            const markdownContent = document.createElement('div');
            markdownContent.className = 'markdown-content';
            markdownContent.innerHTML = this.renderMarkdown(content);
            messageContent.appendChild(markdownContent);
            
            // Áp dụng highlight cho code blocks
            setTimeout(() => {
                messageContent.querySelectorAll('pre code').forEach((block) => {
                    hljs.highlightElement(block);
                });
            }, 100);
        }
        
        messageElement.appendChild(avatar);
        messageElement.appendChild(messageContent);
        
        this.chatMessages.appendChild(messageElement);
        
        // Cuộn xuống tin nhắn mới nhất
        this.scrollToBottom();
        
        return messageElement;
    }
    
    updateBotMessage(content, messageElement) {
        if (messageElement) {
            const messageContent = messageElement.querySelector('.markdown-content');
            if (messageContent) {
                messageContent.innerHTML = this.renderMarkdown(content);
                
                // Áp dụng highlight cho code blocks
                setTimeout(() => {
                    messageContent.querySelectorAll('pre code').forEach((block) => {
                        hljs.highlightElement(block);
                    });
                }, 100);
            }
        }
        
        this.scrollToBottom();
    }
    
    renderMarkdown(content) {
        return marked.parse(content);
    }
    
    showTypingIndicator() {
        const messageElement = document.createElement('div');
        messageElement.className = 'message bot-message';
        
        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        
        const icon = document.createElement('i');
        icon.className = 'fas fa-robot';
        avatar.appendChild(icon);
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;
        
        messageContent.appendChild(indicator);
        
        messageElement.appendChild(avatar);
        messageElement.appendChild(messageContent);
        
        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
        
        return messageElement;
    }
    
    removeTypingIndicator() {
        const indicators = this.chatMessages.querySelectorAll('.typing-indicator');
        indicators.forEach(indicator => {
            indicator.closest('.message').remove();
        });
    }
    
    clearChatInput() {
        document.getElementById('userInput').value = '';
        this.adjustTextareaHeight();
    }
    
    enableInput() {
        document.getElementById('userInput').disabled = false;
        document.getElementById('sendButton').disabled = false;
    }
    
    disableInput() {
        document.getElementById('userInput').disabled = true;
        document.getElementById('sendButton').disabled = true;
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    focusInput() {
        document.getElementById('userInput').focus();
    }
    
    adjustTextareaHeight() {
        const textarea = document.getElementById('userInput');
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
    
    addSuggestedQuestionsListener() {
        const chips = document.querySelectorAll('.chip');
        chips.forEach(chip => {
            chip.addEventListener('click', () => {
                const question = chip.getAttribute('data-question');
                document.getElementById('userInput').value = question;
                this.adjustTextareaHeight();
                this.focusInput();
            });
        });
    }
}