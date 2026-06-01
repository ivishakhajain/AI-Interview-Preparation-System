from reportlab.pdfgen import canvas
from pdfminer.high_level import extract_text
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
import os

from flask import session

import random
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
app = Flask(__name__)

app.secret_key = "ai_interview_secret"

app.config['UPLOAD_FOLDER'] = 'uploads'

os.makedirs('uploads', exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)

with app.app_context():
    db.create_all()

# Database Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    password = db.Column(db.String(100))

# Home Page
@app.route('/')
def home():
    return render_template('index.html')

# Register Page
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        user = User(
            name=name,
            email=email,
            password=password
        )

        db.session.add(user)
        db.session.commit()

        return redirect('/login')

    return render_template('register.html')

# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(
            email=email,
            password=password
        ).first()

        if user:
            session['user'] = user.name
            return redirect('/upload_resume')

    return render_template('login.html')

# Interview Page
@app.route('/interview')
def interview():

    if not session.get('resume_uploaded'):
        return redirect('/upload_resume')

    all_questions = [
        "Tell me about yourself",
        "Why should we hire you?",
        "What is Python?",
        "Explain OOP concepts",
        "What is Machine Learning?",
        "What is SQL?",
        "What is DBMS?",
        "What are APIs?",
        "What is Flask?",
        "Explain inheritance in OOP"
    ]

    questions = random.sample(all_questions, 5)

    return render_template(
    'interview.html',
    questions=questions,
    user=session.get('user')
)

def evaluate_answer(answer):

    answer = answer.lower()
    score = 0

    keywords = {
        "python": 10,
        "oop": 10,
        "class": 10,
        "object": 10,
        "inheritance": 10,
        "machine learning": 15,
        "sql": 10,
        "algorithm": 10
    }

    for key, value in keywords.items():
        if key in answer:
            score += value

    return min(score, 25)

# Resume Upload
@app.route('/upload_resume', methods=['GET', 'POST'])
def upload_resume():

    if request.method == 'POST':

        file = request.files['resume']

        if file:

            filename = secure_filename(file.filename)

            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)

            # resume text extract
            text = extract_text(path).lower()

            skills = []
            match_score = random.randint(70, 95)

            if "python" in text:
                skills.append("Python")

            if "java" in text:
                skills.append("Java")

            if "sql" in text:
                skills.append("SQL")

            if "machine learning" in text:
                skills.append("Machine Learning")


                session['resume_uploaded'] = True

            return render_template(
                "resume_result.html", 
                skills=skills,
                 match_score=match_score
                )

    return render_template('upload_resume.html')

# Result Page
# Evaluate Answer Function
def evaluate_answer(answer):

    if len(answer) > 50:
        return 10

    elif len(answer) > 20:
        return 5

    else:
        return 2


# Submit Answers Route
@app.route('/submit_answers', methods=['POST'])
def submit_answers():

    global user_answers
    user_answers = []

    for i in range(len(request.form)):

        ans = request.form.get(f'answer{i}')

        score = evaluate_answer(ans)

        user_answers.append(score)

    return redirect('/result')

@app.route('/result')
def result():

    total = sum(user_answers)

    all_results.append({

    "name": session.get('user'),

    "score": total

})

    try:
        sender = "jainvishakha33@gmail.com"
        password = "your_app_password"

        msg = MIMEText(f"Your Interview Score is {total}")

        msg['Subject'] = "AI Interview Result"
        msg['From'] = sender
        msg['To'] = "jainvishakha33@gmail.com"

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()

    except:
        print("Email not sent")

    if total > 80:
        feedback = "Excellent 🚀"
    elif total > 50:
        feedback = "Good 👍"
    else:
        feedback = "Needs Improvement 📚"

    return render_template('result.html', score=total, feedback=feedback)

@app.route('/download_pdf')
def download_pdf():

    total = sum(user_answers)

    pdf = canvas.Canvas("report.pdf")

    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(180, 800, "AI Interview Report")

    pdf.setFont("Helvetica", 14)

    pdf.drawString(
        100,
        740,
        f"Candidate Name: {session.get('user')}"
    )

    pdf.drawString(
        100,
        700,
        f"Final Score: {total}%"
    )

    pdf.drawString(
        100,
        660,
        "Generated By AI Interview System"
    )

    pdf.save()

    return send_file(
        "report.pdf",
        as_attachment=True
    )

@app.route('/certificate')
def certificate():

    total = sum(user_answers)

    name = session.get('user')

    today = datetime.now().strftime("%d-%m-%Y")

    c = canvas.Canvas("certificate.pdf")

    c.setFont("Helvetica-Bold", 24)
    c.drawString(150, 780, "AI Interview Certificate")

    c.setFont("Helvetica", 16)

    c.drawString(
        120,
        700,
        f"This certificate is awarded to:"
    )

    c.setFont("Helvetica-Bold", 18)

    c.drawString(
        220,
        660,
        name
    )

    c.setFont("Helvetica", 14)

    c.drawString(
        120,
        600,
        f"Interview Score: {total}%"
    )

    c.drawString(
        120,
        560,
        f"Date: {today}"
    )

    c.drawString(
        120,
        500,
        "Successfully completed AI Interview Assessment"
    )

    c.drawString(
        400,
        150,
        "Authorized Signature"
    )

    c.save()

    return send_file(
        "certificate.pdf",
        as_attachment=True
    )

@app.route('/chatbot', methods=['GET','POST'])
def chatbot():

    reply = ""

    if request.method == 'POST':

        user_msg = request.form['msg'].lower()

        qa = {

            "what is python":
            "Python is a high-level programming language used for web development, AI and data science.",

            "what is sql":
            "SQL is used to store, manage and retrieve data from databases.",

            "what is dbms":
            "DBMS stands for Database Management System.",

            "what is oop":
            "OOP stands for Object Oriented Programming. It is based on classes and objects.",

            "what is flask":
            "Flask is a lightweight Python web framework.",

            "what is api":
            "API allows two applications to communicate with each other.",

            "what is machine learning":
            "Machine Learning is a branch of AI that enables systems to learn from data.",

            "what is data science":
            "Data Science is the process of extracting insights from data."
        }

        reply = qa.get(
            user_msg,
            "Sorry, I don't know that answer yet."
        )

    return render_template(
        "chatbot.html",
        reply=reply
    )

@app.route('/history')
def history():

    return render_template(
        'history.html',
        results=all_results
    )

@app.route('/admin')
def admin():

    return render_template(
        'admin.html',
        results=all_results
    )


# Logout Feature
@app.route('/logout')
def logout():
     
    session.clear()
    return redirect('/')


if __name__ == "__main__":

    with app.app_context():
    
        db.create_all()

        all_results = []

    app.run(debug=True)

