from flask import Flask, request, render_template, session, Response, stream_with_context
import sys, time, markdown2
from utils.store import build_vectorstore
from utils.qa import build_qa_chain

app = Flask(__name__)
app.secret_key = "supersecretkey"

qa_chain = None

@app.route("/", methods=["GET"])
def home():
    if "conversation" not in session:
        session["conversation"] = []
    return render_template("index.html", conversation=session["conversation"])

@app.route("/stream", methods=["POST"])
def stream():
    query = request.form["query"]

    # Lưu tin nhắn người dùng vào session
    if "conversation" not in session:
        session["conversation"] = []
    session["conversation"].append({"role": "user", "content": query})
    session.modified = True

    # Lấy câu trả lời từ mô hình
    result = qa_chain.invoke({"query": query})
    answer = result if isinstance(result, str) else result.get("result", "")

    @stream_with_context
    def generate():
        # Gửi từng ký tự/word để giả lập typing
        for char in answer:
            yield char
            time.sleep(0.03)
        
        # Lưu câu trả lời vào session sau khi stream xong
        session["conversation"].append({"role": "assistant", "content": markdown2.markdown(answer)})
        session.modified = True

    return Response(generate(), mimetype="text/plain")

if __name__ == "__main__":
    refresh = "--refresh" in sys.argv
    folder_path = "data"
    vectorstore = build_vectorstore(folder_path, refresh=refresh)
    qa_chain = build_qa_chain(vectorstore)
    app.run(debug=True)
