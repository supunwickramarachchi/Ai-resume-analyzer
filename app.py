from flask import Flask, render_template, request
from dotenv import load_dotenv
import pdfplumber
import google.generativeai as genai
import os 
import re

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf: 
        for page in pdf.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
                
    return text


def analyze_resume_with_gemini(resume_text, job_description):
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
You are an AI resume reviewer.

Here is a job description:

{job_description}

And here is a candidate's resume:

{resume_text}

🔍 Analyze how well the resume matches the job description.

✅ Provide a clear match percentage on a separate line, in the exact format:

Match percentage: XX%

📌 List missing or weak areas
📈 Suggest improvements to make the resume more aligned with the job
"""

    response = model.generate_content(prompt)
    return response.text

def extract_match_score(text):
    match = re.search(r"match percentage[:\s]*([0-9]{1,3})%", text, re.IGNORECASE)
    if match:
        score = int(match.group(1))
        return max(0, min(score,100))
    return None

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    resume = request.files['resume']
    job_desc = request.form['job_desc']
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], resume.filename)
    resume.save(file_path)
    
    # Extract resume text 
    resume_text = extract_text_from_pdf(file_path)
    
    # Analyze using gemini
    ai_feedback = analyze_resume_with_gemini(resume_text, job_desc)
    
    # Extract numeric match score from AI feedback
    match_score = extract_match_score(ai_feedback)
    
    return render_template(
        'result.html',
        ai_feedback=ai_feedback,
        resume_text=resume_text,
        job_desc=job_desc,
        match_score=match_score
    )



if __name__ == '__main__':
    app.run(debug=True)