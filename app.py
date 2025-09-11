from flask import Flask, request, render_template, session, Response, stream_with_context
import sys, time, markdown2
from utils.ingest import build_vectorstore
from utils.retrieval import get_vectorstore   # thêm import retrieval
from utils.qa import build_qa_chain
from qdrant_client import QdrantClient

app = Flask(__name__)
app.secret_key = "supersecretkey"

qa_chain = None  # sẽ khởi tạo sau

@app.route("/", methods=["GET"])
def home():
    if "conversation" not in session:
        session["conversation"] = []
    return render_template("index.html", conversation=session["conversation"])

@app.route("/stream", methods=["POST"])
def stream():
    query = request.form["query"]

    # Lưu user message
    if "conversation" not in session:
        session["conversation"] = []
    session["conversation"].append({"role": "user", "content": query})
    session.modified = True

    # Gọi chain để lấy câu trả lời
    result = qa_chain.invoke({"query": query})
    answer = result if isinstance(result, str) else result.get("result", "")

    @stream_with_context
    def generate():
        # Stream từng ký tự cho giống typing
        for char in answer:
            yield char
            time.sleep(0.03)

        # Lưu assistant message (markdown render)
        session["conversation"].append(
            {"role": "assistant", "content": markdown2.markdown(answer)}
        )
        session.modified = True

    return Response(generate(), mimetype="text/plain")


if __name__ == "__main__":
    refresh = "--refresh" in sys.argv
    folder_path = "data"
    collection_name = "docs"

    client = QdrantClient(host="localhost", port=6333)

    if refresh:
        # Nếu chạy app với `python app.py --refresh` thì build lại
        vectorstore = build_vectorstore(folder_path, collection_name=collection_name)
    else:
        # Nếu collection đã tồn tại thì load lại, ngược lại thì build mới
        collections = client.get_collections().collections
        if any(c.name == collection_name for c in collections):
            vectorstore = get_vectorstore(collection_name=collection_name)
        else:
            vectorstore = build_vectorstore(folder_path, collection_name=collection_name)

    qa_chain = build_qa_chain(vectorstore)

    app.run(debug=True, use_reloader=False)
