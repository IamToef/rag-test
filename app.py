from flask import Flask, request, render_template, session, Response, stream_with_context
import time, markdown2
from utils.retrieval import get_vectorstore
from utils.qa import build_qa_chain
from qdrant_client import QdrantClient

app = Flask(__name__)
app.secret_key = "supersecretkey"

qa_chain = None  # sẽ khởi tạo sau

# --- Flask routes ---
@app.route("/", methods=["GET"])
def home():
    if "conversation" not in session:
        session["conversation"] = []
    return render_template("index.html", conversation=session["conversation"])

@app.route("/stream", methods=["POST"])
def stream():
    query = request.form["query"]

    if "conversation" not in session:
        session["conversation"] = []
    session["conversation"].append({"role": "user", "content": query})
    session.modified = True

    result = qa_chain.invoke({"query": query})
    answer = result if isinstance(result, str) else result.get("result", "")

    @stream_with_context
    def generate():
        for char in answer:
            yield char
            time.sleep(0.03)
        session["conversation"].append(
            {"role": "assistant", "content": markdown2.markdown(answer)}
        )
        session.modified = True

    return Response(generate(), mimetype="text/plain")


if __name__ == "__main__":
    collection_name = "docs"
    client = QdrantClient(host="localhost", port=6333)

    # Chỉ load vectorstore, không build
    vectorstore = get_vectorstore(collection_name=collection_name)
    qa_chain = build_qa_chain(vectorstore)

    app.run(debug=True, use_reloader=False)
