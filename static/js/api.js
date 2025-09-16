class API {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
    }

    async askQuestionStreaming(query, onData, onComplete, onError) {
        try {
            const formData = new FormData();
            formData.append('query', query);
            
            const response = await fetch(`${this.baseURL}/stream`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let accumulatedText = '';
            
            while (true) {
                const { done, value } = await reader.read();
                
                if (done) {
                    onComplete(accumulatedText);
                    break;
                }
                
                const textChunk = decoder.decode(value, { stream: true });
                accumulatedText += textChunk;
                
                if (onData) {
                    onData(accumulatedText);
                }
            }
        } catch (error) {
            console.error('Lỗi khi gửi câu hỏi:', error);
            if (onError) {
                onError(error);
            }
        }
    }
}