# app/admin/routes.py

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime

from . import admin_bp
from app import db
from app.models import Exam, Question, Attempt, ActivityLog, Student, Admin
import csv, io



@admin_bp.route("/dashboard")
@login_required
def dashboard():
    total_exams    = Exam.query.count()
    # Count only students who have at least one attempt
    total_students = Student.query.filter(
        Student.attempts.any()
    ).count()
    total_attempts = Attempt.query.count()
    flagged        = Attempt.query.filter(
                         Attempt.suspicion_score >= 15
                     ).count()
    recent_attempts = (Attempt.query
                       .order_by(Attempt.start_time.desc())
                       .limit(10).all())
    return render_template("admin/dashboard.html",
                       total_exams=total_exams,
                       total_students=total_students,
                       total_attempts=total_attempts,
                       flagged=flagged,
                       recent_attempts=recent_attempts,
                       pending_admins=Admin.query.filter_by(is_approved=False).count())

@admin_bp.route("/exams")
@login_required
def exams():

    all_exams = Exam.query.order_by(
        Exam.created_at.desc()
    ).all()

    return render_template(
        "admin/exams.html",
        exams=all_exams
    )


@admin_bp.route("/exams/create", methods=["GET", "POST"])
@login_required
def create_exam():

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        duration = request.form.get("duration", 0)
        scheduled_at = request.form.get("scheduled_at", "")
        status = request.form.get("status", "draft")

        if not title or not duration:

            flash("Title and duration are required.", "danger")

            return redirect(
                url_for("admin.create_exam")
            )

        exam = Exam(
            admin_id=current_user.id,
            title=title,
            duration=int(duration),
            scheduled_at=datetime.strptime(
                scheduled_at,
                "%Y-%m-%dT%H:%M"
            ) if scheduled_at else None,
            status=status
        )

        db.session.add(exam)
        db.session.commit()

        flash("Exam created successfully", "success")

        return redirect(url_for("admin.exams"))

    return render_template(
    "admin/create_exam.html",
    exam=None
)


@admin_bp.route("/exams/<int:exam_id>/edit", methods=["GET", "POST"])
@login_required
def edit_exam(exam_id):

    exam = Exam.query.get_or_404(exam_id)

    if request.method == "POST":

        exam.title = request.form.get(
            "title",
            exam.title
        ).strip()

        exam.duration = int(
            request.form.get(
                "duration",
                exam.duration
            )
        )

        exam.status = request.form.get(
            "status",
            exam.status
        )

        scheduled_at = request.form.get(
            "scheduled_at",
            ""
        )

        exam.scheduled_at = datetime.strptime(
            scheduled_at,
            "%Y-%m-%dT%H:%M"
        ) if scheduled_at else None

        db.session.commit()

        flash("Exam updated", "success")

        return redirect(url_for("admin.exams"))

    return render_template(
        "admin/edit_exam.html",
        exam=exam
    )


@admin_bp.route("/exams/<int:exam_id>/delete", methods=["POST"])
@login_required
def delete_exam(exam_id):

    exam = Exam.query.get_or_404(exam_id)

    db.session.delete(exam)
    db.session.commit()

    flash("Exam deleted", "info")

    return redirect(url_for("admin.exams"))


@admin_bp.route("/exams/<int:exam_id>/questions")
@login_required
def questions(exam_id):

    exam = Exam.query.get_or_404(exam_id)

    return render_template(
        "admin/questions.html",
        exam=exam
    )


@admin_bp.route("/exams/<int:exam_id>/questions/add", methods=["GET", "POST"])
@login_required
def add_question(exam_id):

    exam = Exam.query.get_or_404(exam_id)

    if request.method == "POST":

        q = Question(
            exam_id=exam_id,
            question_text=request.form.get(
                "question_text",
                ""
            ).strip(),

            option_a=request.form.get(
                "option_a",
                ""
            ).strip(),

            option_b=request.form.get(
                "option_b",
                ""
            ).strip(),

            option_c=request.form.get(
                "option_c",
                ""
            ).strip(),

            option_d=request.form.get(
                "option_d",
                ""
            ).strip(),

            correct_answer=request.form.get(
                "correct_answer",
                "A"
            ).upper()
        )

        if not q.question_text:

            flash("Question text required", "danger")

            return redirect(
                url_for(
                    "admin.add_question",
                    exam_id=exam_id
                )
            )

        db.session.add(q)
        db.session.commit()

        flash("Question added", "success")

        return redirect(
            url_for(
                "admin.questions",
                exam_id=exam_id
            )
        )

    return render_template(
        "admin/add_question.html",
        exam=exam
    )


@admin_bp.route("/questions/<int:q_id>/delete", methods=["POST"])
@login_required
def delete_question(q_id):

    q = Question.query.get_or_404(q_id)

    exam_id = q.exam_id

    db.session.delete(q)
    db.session.commit()

    flash("Question deleted", "info")

    return redirect(
        url_for(
            "admin.questions",
            exam_id=exam_id
        )
    )


@admin_bp.route("/attempts/<int:attempt_id>")
@login_required
def attempt_detail(attempt_id):

    attempt = Attempt.query.get_or_404(attempt_id)

    logs = (
        ActivityLog.query
        .filter_by(attempt_id=attempt_id)
        .order_by(ActivityLog.timestamp.asc())
        .all()
    )

    return render_template(
        "admin/attempt_detail.html",
        attempt=attempt,
        logs=logs
    )


@admin_bp.route("/exams/<int:exam_id>/import-csv", methods=["GET", "POST"])
@login_required
def import_csv(exam_id):
    exam = Exam.query.get_or_404(exam_id)

    if request.method == "POST":
        file = request.files.get("csv_file")

        if not file or not file.filename.endswith(".csv"):
            flash("Please upload a valid .csv file.", "danger")
            return redirect(url_for("admin.import_csv", exam_id=exam_id))

        stream  = io.StringIO(file.stream.read().decode("utf-8"), newline=None)
        reader  = csv.DictReader(stream)
        added   = 0
        errors  = []

        for i, row in enumerate(reader, start=2):
            try:
                q = Question(
                    exam_id        = exam_id,
                    question_text  = row["question"].strip(),
                    option_a       = row["option_a"].strip(),
                    option_b       = row["option_b"].strip(),
                    option_c       = row["option_c"].strip(),
                    option_d       = row["option_d"].strip(),
                    correct_answer = row["correct_answer"].strip().upper()
                )
                if q.correct_answer not in ("A", "B", "C", "D"):
                    errors.append(f"Row {i}: correct_answer must be A/B/C/D")
                    continue
                db.session.add(q)
                added += 1
            except KeyError as e:
                errors.append(f"Row {i}: missing column {e}")

        db.session.commit()

        if added:
            flash(f"{added} question(s) imported successfully.", "success")
        for e in errors:
            flash(e, "warning")

        return redirect(url_for("admin.questions", exam_id=exam_id))

    return render_template("admin/import_csv.html", exam=exam)

@admin_bp.route("/questions/<int:q_id>/edit", methods=["GET", "POST"])
@login_required
def edit_question(q_id):
    q = Question.query.get_or_404(q_id)
    if request.method == "POST":
        q.question_text  = request.form.get("question_text", "").strip()
        q.option_a       = request.form.get("option_a", "").strip()
        q.option_b       = request.form.get("option_b", "").strip()
        q.option_c       = request.form.get("option_c", "").strip()
        q.option_d       = request.form.get("option_d", "").strip()
        q.correct_answer = request.form.get("correct_answer", "A").upper()
        db.session.commit()
        flash("Question updated", "success")
        return redirect(url_for("admin.questions", exam_id=q.exam_id))
    return render_template("admin/edit_question.html", q=q)