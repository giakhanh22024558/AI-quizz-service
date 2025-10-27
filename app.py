from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from flask_cors import CORS
import json
import markdown
import re
# Cấu hình API key
genai.configure(api_key="AIzaSyB2488wupzDawVwdwvV_ouxulguYhFXjao")  # Thay bằng key Gemini của bạn
app = Flask(__name__)

# Lưu đáp án trắc nghiệm
quiz_answers = {}

CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:3000"]}})

@app.route("/", methods=["GET", "POST"])
def index():
    quiz = {"mcq": [], "essay": []}
    if request.method == "POST":
        lesson = request.form["lesson"]
        level = request.form["level"]
        numMCQ = int(request.form["numMCQ"])
        numEssay = int(request.form["numEssay"])

        prompt = f"""
Bạn là giáo viên giỏi. Tạo đề kiểm tra Python:
- Bài học: {lesson}
- Trình độ: {level}
- {numMCQ} câu trắc nghiệm và {numEssay} câu tự luận
- Trả về **JSON chuẩn** theo cấu trúc:
{{
  "mcq": [
    {{"question": "...", "options": ["A","B","C","D"], "answer": "..." }},
    ...
  ],
  "essay": [
    {{"question": "..."}}
  ]
}}
**Chỉ trả JSON, không thêm chữ nào khác.**
        """

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)

        # Chuyển JSON AI trả về
        try:
            quiz = json.loads(response.text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", response.text, re.DOTALL)
            if match:
                quiz = json.loads(match.group(0))
            else:
                quiz = {"mcq": [], "essay": []}

        # Lưu đáp án trắc nghiệm
        global quiz_answers
        quiz_answers = {f"q{i+1}": q.get("answer") for i, q in enumerate(quiz.get("mcq", []))}

        # MCQ: gộp cả câu hỏi + đáp án vào 1 block LaTeX
        for q in quiz.get("mcq", []):
            options_text = "\n".join([f"({opt}) {opt}" for opt in q.get("options", [])])
            q["question_latex"] = f"{q['question']}\n{options_text}"

        # Tự luận dùng Markdown
        for q in quiz.get("essay", []):
            q["question_html"] = markdown.markdown(q["question"])

    return render_template("index.html", quiz=quiz)

@app.route("/submit_mcq", methods=["POST"])
def submit_mcq():
    user_answers = request.form.to_dict()
    score = sum(1 for q, ans in user_answers.items() if quiz_answers.get(q) == ans)
    return jsonify({"score": score})

@app.route("/submit_essay", methods=["POST"])
def submit_essay():
    user_essays = request.form.to_dict()
    prompt = "Đọc các câu tự luận sau và đưa ra gợi ý đáp án chuẩn xác:\n"
    for q, ans in user_essays.items():
        prompt += f"{q}: {ans}\n"

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    return jsonify({"ai_feedback": response.text})

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}
    lesson = data.get("lesson")
    level = data.get("level")
    try:
        numMCQ = int(data.get("numMCQ", 0))
        numEssay = int(data.get("numEssay", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "numMCQ and numEssay must be integers"}), 400

    if not all([lesson, level]) or (numMCQ < 0 or numEssay < 0):
        return jsonify({"error": "Invalid payload"}), 400

    prompt = f"""
Bạn là giáo viên giỏi. Tạo đề kiểm tra Python:
- Bài học: {lesson}
- Trình độ: {level}
- {numMCQ} câu trắc nghiệm và {numEssay} câu tự luận
- Trả về **JSON chuẩn** theo cấu trúc:
{{
  "mcq": [
    {{"question": "...", "options": ["A","B","C","D"], "answer": "..." }},
    ...
  ],
  "essay": [
    {{"question": "..."}}
  ]
}}
**Chỉ trả JSON, không thêm chữ nào khác.**
    """

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)

    try:
        quiz = json.loads(response.text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", response.text, re.DOTALL)
        if match:
            quiz = json.loads(match.group(0))
        else:
            quiz = {"mcq": [], "essay": []}

    # Optional: mirror existing processing (LaTeX/Markdown)
    for q in quiz.get("mcq", []):
        options_text = "\n".join([f"({opt}) {opt}" for opt in q.get("options", [])])
        q["question_latex"] = f"{q['question']}\n{options_text}"
    for q in quiz.get("essay", []):
        q["question_html"] = markdown.markdown(q["question"])

    # Refresh global answers for legacy form endpoint
    global quiz_answers
    quiz_answers = {f"q{i+1}": q.get("answer") for i, q in enumerate(quiz.get("mcq", []))}

    return jsonify(quiz)

if __name__ == "__main__":
    app.run(debug=True)
