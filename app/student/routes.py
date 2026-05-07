from flask import render_template, redirect, url_for, flash, request, session
from datetime import datetime
from . import student_bp
from app import db
from app.models import Exam, Student, Attempt, Question, ActivityLog

# Suspicion score weights
WEIGHTS = {
    "tab_switch":  5,
    "idle":        3,
    "fast_submit": 15,
}


# ── Exam entry ────────────────────────────────────────────────────────────────
@student_bp.route("/enter", methods=["GET", "POST"])
def enter_exam():
    # Only show scheduled exams in dropdown
    exams = Exam.query.filter_by(status="scheduled").all()

    if request.method == "POST":
        name        = request.form.get("name", "").strip()
        roll_number = request.form.get("roll_number", "").strip()
        exam_id     = request.form.get("exam_id")

        if not name or not roll_number or not exam_id:
            flash("All fields are required.", "danger")
            return redirect(url_for("student.enter_exam"))

        # Check if student already exists, if not create them
        student = Student.query.filter_by(roll_number=roll_number).first()
        if not student:
            student = Student(name=name, roll_number=roll_number)
            db.session.add(student)
            db.session.commit()

        # Create a new attempt record
        attempt = Attempt(
            student_id = student.id,
            exam_id    = int(exam_id),
            start_time = datetime.utcnow()
        )
        db.session.add(attempt)
        db.session.commit()

        # Store in session so student can access their exam page
        session["attempt_id"] = attempt.id
        session["student_id"] = student.id

        return redirect(url_for("student.take_exam", attempt_id=attempt.id))

    return render_template("student/enter.html", exams=exams)


# ── Take exam ─────────────────────────────────────────────────────────────────
@student_bp.route("/exam/<int:attempt_id>")
def take_exam(attempt_id):
    # Security check — only the student who started this attempt can access it
    if session.get("attempt_id") != attempt_id:
        flash("Unauthorised access.", "danger")
        return redirect(url_for("student.enter_exam"))

    attempt   = Attempt.query.get_or_404(attempt_id)
    exam      = attempt.exam
    questions = Question.query.filter_by(exam_id=exam.id).all()

    return render_template("student/exam.html",
                           attempt=attempt,
                           exam=exam,
                           questions=questions)


# ── Submit exam ───────────────────────────────────────────────────────────────
@student_bp.route("/exam/<int:attempt_id>/submit", methods=["POST"])
def submit_exam(attempt_id):
    if session.get("attempt_id") != attempt_id:
        flash("Unauthorised access.", "danger")
        return redirect(url_for("student.enter_exam"))

    attempt   = Attempt.query.get_or_404(attempt_id)
    exam      = attempt.exam
    questions = Question.query.filter_by(exam_id=exam.id).all()

    # Auto-grade MCQs
    score = 0
    for q in questions:
        submitted = request.form.get(f"q_{q.id}", "").upper()
        if submitted == q.correct_answer:
            score += 1

    # Check fast submission
    end_time  = datetime.utcnow()
    elapsed   = (end_time - attempt.start_time).total_seconds() / 60
    threshold = exam.duration * 0.20

    if elapsed < threshold:
        log = ActivityLog(
            attempt_id = attempt_id,
            event_type = "fast_submit",
            timestamp  = end_time
        )
        db.session.add(log)

    # Calculate suspicion score from all logged events
    logs      = ActivityLog.query.filter_by(attempt_id=attempt_id).all()
    suspicion = sum(WEIGHTS.get(log.event_type, 0) for log in logs)

    # Save everything
    attempt.end_time        = end_time
    attempt.score           = score
    attempt.suspicion_score = suspicion
    db.session.commit()

    # Clear session
    session.pop("attempt_id", None)
    session.pop("student_id", None)

    return redirect(url_for("student.result", attempt_id=attempt_id))


# ── Result ────────────────────────────────────────────────────────────────────
@student_bp.route("/result/<int:attempt_id>")
def result(attempt_id):
    attempt = Attempt.query.get_or_404(attempt_id)
    total   = Question.query.filter_by(exam_id=attempt.exam_id).count()
    return render_template("student/result.html",
                           attempt=attempt,
                           total=total)