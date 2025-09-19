WORKFLOW:

create.py:
load_data.py -> set collection name
-> thực hiện smart_reload:
    -> Tính hash. Nếu != hash ban đầu được truyền vào
        -> reset vectorstore.
        -> Nếu có collection -> xóa collection đó, tạo lại
        -> hàm load_and index() -> load file -> chunking -> return vector_store


main.py:
get_vector_store()
    -> Input -> exit hoặc quit -> out chương trình
            -> clear -> xóa history
            -> history -> check history
        add message vào history -> agent_executor()


agent_executor -> llm -> tool (retrieve)    -> checkpoint memory
                                            -> set threshold -> in ra snippet, tính simmularity_search_with_relevance_score
                                            -> kết quả + thời gian chạy


