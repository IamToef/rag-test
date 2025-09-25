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

graph.py:
- add 3 nodes: (analyze_query + retrieve + generate)
- add edges: (begin -> analyze query -> retrieve -> generate)

pipeline.py:
- analyze_query:
- retrieve:
- generate:
