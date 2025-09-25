WORKFLOW:

create.py:
set class DataManager from indexing.py
smart_reload(): 
if changes detected: (!= the originated hash)
    reset and reload data to vectorstore
    -> load docs and chunk them (Semantic chunking, using the embedding model) -> save the hash.
else: do nothing

main.py:
chatbot setting up
after setting up:
    input questions.
    if "exit":
        break
    invoke from graphs (question & chat history)
    lấy question và chat_history
    in kết quả + thời gian respond + cập nhật lịch sử hội thoại

graph.py:
- add 3 nodes: (analyze_query + retrieve + generate)
- add edges: (begin -> analyze query -> retrieve -> generate)

pipeline.py:
- analyze_query:
* Phân tích câu hỏi người dùng → ép LLM trả về dạng Search (query + filters).
- retrieve:
* Tìm k docs liên quan từ vector store (Qdrant).

* In ra Top 3 (page, id, source, distance).
- generate:
* Ghép context + chat history → sinh câu trả lời.
* Cập nhật chat_history với Q/A mới.


PROBLEM mới:
* Chưa có lịch sử chat, 1 2 câu đầu chatbot không tìm ra thông tin hoặc có in ra kết quả đúng, nhưng khá khó hiểu, chưa tối ưu.