document.addEventListener('DOMContentLoaded', () => {
    // Khởi tạo các thành phần
    document
    const api = new API();
    const ui = new UI();
    
    // Thêm event listener cho các câu hỏi gợi ý
    ui.addSuggestedQuestionsListener();
    
    // Xử lý sự kiện gửi tin nhắn
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    
    // Tự động điều chỉnh chiều cao textarea
    userInput.addEventListener('input', () => {
        ui.adjustTextareaHeight();
    });
    
    function sendMessage() {
        const query = userInput.value.trim();
        
        if (query === '') return;
        
        // Ẩn welcome message nếu có
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.style.display = 'none';
        }
        
        // Hiển thị tin nhắn của người dùng
        ui.addMessage(query, true);
        ui.clearChatInput();
        ui.disableInput();
        
        // Hiển thị indicator đang nhập
        const typingIndicator = ui.showTypingIndicator();
        
        // Tạo phần tử tin nhắn bot trống để cập nhật dần
        const botMessageElement = ui.addMessage('', false);
        
        // Gửi câu hỏi đến API với streaming
        api.askQuestionStreaming(
            query,
            // onData callback - được gọi khi có dữ liệu mới
            (accumulatedText) => {
                ui.updateBotMessage(accumulatedText, botMessageElement);
            },
            // onComplete callback - được gọi khi hoàn thành
            (completeText) => {
                ui.removeTypingIndicator();
                ui.updateBotMessage(completeText, botMessageElement);
                ui.enableInput();
                ui.focusInput();
            },
            // onError callback - được gọi khi có lỗi
            (error) => {
                ui.removeTypingIndicator();
                ui.addMessage('Xin lỗi, đã xảy ra lỗi khi kết nối đến server. Vui lòng thử lại sau.', false);
                ui.enableInput();
                ui.focusInput();
                console.error('Lỗi:', error);
            }
        );
    }
    
    sendButton.addEventListener('click', sendMessage);
    
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Tự động focus vào ô input
    ui.focusInput();
});