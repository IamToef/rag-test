from flask import Flask, request, render_template, session, Response, stream_with_context
import time, markdown2, os, argparse
from dotenv import load_dotenv
from utils.retrieval import get_vectorstore
from utils.qa import build_qa_chain

# Load biến môi trường từ .env
load_dotenv()

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
    parser = argparse.ArgumentParser(description="Run Flask RAG App with Qdrant")
    parser.add_argument(
        "--cloud",
        action="store_true",
        help="Chạy ở chế độ Qdrant Cloud. Nếu không truyền thì mặc định local."
    )
    args = parser.parse_args()

    collection_name = os.getenv("QDRANT_COLLECTION", "docs")

    # Xác định chế độ Local/Cloud
    use_cloud = args.cloud

    # Load vectorstore từ Qdrant
    vectorstore = get_vectorstore(collection_name=collection_name, use_cloud=use_cloud)
    qa_chain = build_qa_chain(vectorstore)

    print(f"🚀 App running in {'CLOUD' if use_cloud else 'LOCAL'} mode")
    app.run(debug=True, use_reloader=False)

