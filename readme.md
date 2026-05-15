app/admin/__init__.py

    exam = Exam.query.get_or_404(exam_id)

    if request.method == "POST":
        exam.title    = request.form.get("title", exam.title).strip()
        exam.duration = int(request.form.get("duration", exam.duration))
        exam.status   = request.form.get("status", exam.status)
        scheduled_at  = request.form.get("scheduled_at", "")
        exam.scheduled_at = datetime.strptime(
                                scheduled_at, "%Y-%m-%dT%H:%M"
                            ) if scheduled_at else None
        db.session.commit()
        flash("Exam updated.", "success")
        return redirect(url_for("admin.exams"))

    return render_template("admin/edit_exam.html", exam=exam)


@admin_bp.route("/exams/<int:exam_id>/delete", methods=["POST"])
@login_required
def delete_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    db.session.delete(exam)
    db.session.commit()
    flash("Exam deleted.", "info")
    return redirect(url_for("admin.exams"))


@admin_bp.route("/exams/<int:exam_id>/questions")
@login_required
def questions(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    return render_template("admin/questions.html", exam=exam)


@admin_bp.route("/exams/<int:exam_id>/questions/add", methods=["GET", "POST"])
@login_required
def add_question(exam_id):
    exam = Exam.query.get_or_404(exam_id)

    if request.method == "POST":
        q = Question(
            exam_id        = exam_id,
            question_text  = request.form.get("question_text", "").strip(),
            option_a       = request.form.get("option_a", "").strip(),
            option_b       = request.form.get("option_b", "").strip(),
            option_c       = request.form.get("option_c", "").strip(),
            option_d       = request.form.get("option_d", "").strip(),
            correct_answer = request.form.get("correct_answer", "A").upper(),
        )
        if not q.question_text:
            flash("Question text is required.", "danger")
            return redirect(url_for("admin.add_question", exam_id=exam_id))

        db.session.add(q)
        db.session.commit()
        flash("Question added."from flask import Blueprint

admin_bp = Blueprint("admin", __name__)

app/admin/routes.py
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from . import admin_bp
from app import db
from app.models import Exam, Question, Attempt, ActivityLog, Student


@admin_bp.route("/dashboard")
@login_required
def dashboard():
    total_exams    = Exam.query.count()
    total_students = Student.query.count()
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
                           recent_attempts=recent_attempts)


@admin_bp.route("/exams")
@login_required
def exams():
    all_exams = Exam.query.order_by(Exam.created_at.desc()).all()
    return render_template("admin/exams.html", exams=all_exams)


@admin_bp.route("/exams/create", methods=["GET", "POST"])
@login_required
def create_exam():
    if request.method == "POST":
        title        = request.form.get("title", "").strip()
        duration     = request.form.get("duration", 0)
        scheduled_at = request.form.get("scheduled_at", "")
        status       = request.form.get("status", "draft")

        if not title or not duration:
            flash("Title and duration are required.", "danger")
            return redirect(url_for("admin.create_exam"))

        exam = Exam(
            admin_id     = current_user.id,
            title        = title,
            duration     = int(duration),
            scheduled_at = datetime.strptime(
                               scheduled_at, "%Y-%m-%dT%H:%M"
                           ) if scheduled_at else None,
            status       = status
        )
        db.session.add(exam)
        db.session.commit()
        flash(f'Exam "{title}" created!', "success")
        return redirect(url_for("admin.exams"))

    return render_template("admin/create_exam.html")


@admin_bp.route("/exams/<int:exam_id>/edit", methods=["GET", "POST"])
@login_required
def edit_exam(exam_id):, "success")
        return redirect(url_for("admin.questions", exam_id=exam_id))

    return render_template("admin/add_question.html", exam=exam)


@admin_bp.route("/questions/<int:q_id>/delete", methods=["POST"])
@login_required
def delete_question(q_id):
    q = Question.query.get_or_404(q_id)
    exam_id = q.exam_id
    db.session.delete(q)
    db.session.commit()
    flash("Question deleted.", "info")
    return redirect(url_for("admin.questions", exam_id=exam_id))


@admin_bp.route("/attempts/<int:attempt_id>")
@login_required
def attempt_detail(attempt_id):
    attempt = Attempt.query.get_or_404(attempt_id)
    logs    = (ActivityLog.query
               .filter_by(attempt_id=attempt_id)
               .order_by(ActivityLog.timestamp.asc())
               .all())
    return render_template("admin/attempt_detail.html",
                           attempt=attempt, logs=logs)


app/auth/__init__.py
from flask import Blueprint

auth_bp = Blueprint("auth", __name__)

app/auth/routes.py
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from . import auth_bp
from app import db
from app.models import Admin


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password")
        admin    = Admin.query.filter_by(username=username).first()

        if admin and admin.check_password(password):
            login_user(admin)
            flash("Welcome back!", "success")
            return redirect(url_for("admin.dashboard"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("auth.login"))


app/proctoring/__init__.py
from flask import Blueprint

proctoring_bp = Blueprint("proctoring", __name__)


app/proctoring/routes.py
from flask import request, jsonify
from . import proctoring_bp
from app import db
from app.models import ActivityLog


@proctoring_bp.route("/log-event", methods=["POST"])
def log_event():
    """
    Receives suspicious activity events from JavaScript via AJAX.
    Expected JSON: { "attempt_id": 1, "event_type": "tab_switch" }
    """
    data = request.get_json()

    if not data:
        return jsonify({"status": "error", "message": "No data"}), 400

    attempt_id = data.get("attempt_id")
    event_type = data.get("event_type")

    # Only accept these three event types — nothing else
    allowed = {"tab_switch", "idle", "fast_submit"}
    if not attempt_id or event_type not in allowed:
        return jsonify({"status": "error", "message": "Invalid"}), 400

    log = ActivityLog(attempt_id=attempt_id, event_type=event_type)
    db.session.add(log)
    db.session.commit()

    return jsonify({"status": "ok", "event": event_type}), 200

app/static/css: empty
app/static/js:
/**
 * proctor.js
 * Runs silently during the student exam session.
 * Detects: tab switching, idle time.
 * Also handles the countdown timer and auto-submit.
 */

// Read attempt ID and exam duration from the hidden div in exam.html
const proctorData = document.getElementById("proctor-data");
const attemptId   = parseInt(proctorData.dataset.attemptId);
const examMins    = parseInt(proctorData.dataset.duration);

const LOG_URL = "/proctor/log-event";


// ── Send event to Flask backend ───────────────────────────────────────────────
function sendEvent(eventType) {
    fetch(LOG_URL, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({
            attempt_id: attemptId,
            event_type: eventType
        })
    })
    .then(res => res.json())
    .then(data => console.log("[Proctor] Logged:", data.event))
    .catch(err => console.warn("[Proctor] Failed:", err));
}


// ── Tab switch detection ──────────────────────────────────────────────────────
// visibilitychange fires when the user switches tabs or minimises the window
document.addEventListener("visibilitychange", function() {
    if (document.hidden) {
        sendEvent("tab_switch");
    }
});


// ── Idle detection ────────────────────────────────────────────────────────────
// If no mouse movement or keypress for 60 seconds — flag as idle
const IDLE_LIMIT = 60 * 1000;  // 60 seconds in milliseconds
let idleTimer = null;

function resetIdle() {
    clearTimeout(idleTimer);
    idleTimer = setTimeout(function() {
        sendEvent("idle");
    }, IDLE_LIMIT);
}

// Listen for any user activity to reset the idle timer
["mousemove", "keydown", "click", "scroll"].forEach(function(event) {
    document.addEventListener(event, resetIdle, { passive: true });
});

resetIdle();  // Start the idle timer immediately when exam loads


// ── Countdown timer ───────────────────────────────────────────────────────────
let totalSeconds   = examMins * 60;
const timerDisplay = document.getElementById("timer-display");
const examForm     = document.getElementById("exam-form");

function updateTimer() {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;

    // Format as MM:SS
    timerDisplay.textContent =
        String(mins).padStart(2, "0") + ":" +
        String(secs).padStart(2, "0");

    // Turn amber when 5 minutes left
    if (totalSeconds <= 300) {
        timerDisplay.style.color = "#856404";
    }

    // Turn red when 1 minute left
    if (totalSeconds <= 60) {
        timerDisplay.style.color = "#7B1A1A";
    }

    // Time is up — auto submit
    if (totalSeconds <= 0) {
        clearInterval(timerInterval);
        timerDisplay.textContent = "00:00";
        if (examForm) {
            examForm.submit();
        }
        return;
    }

    totalSeconds--;
}

// Run immediately so timer shows right away, then every 1 second
updateTimer();
const timerInterval = setInterval(updateTimer, 1000);

app/student/__init__.py
from flask import Blueprint

student_bp = Blueprint("student", __name__)

app/student/routes.py
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


app/templates/admin/add_question.html
{% extends "base.html" %}
{% block title %}Add Question — ExamProctor{% endblock %}

{% block body %}
<div class="container py-5" style="max-width:640px">
    <div class="card shadow-sm" style="border-top:4px solid #A06A00">
        <div class="card-body p-4">
            <h5 class="section-heading">Add Question to "{{ exam.title }}"</h5>
            <form method="POST">
                <div class="mb-3">
                    <label class="form-label fw-semibold">Question Text</label>
                    <textarea name="question_text" class="form-control" rows="3"
                              placeholder="Write the question here..." required></textarea>
                </div>
                {% for opt in ['A', 'B', 'C', 'D'] %}
                <div class="mb-3">
                    <label class="form-label fw-semibold">Option {{ opt }}</label>
                    <input type="text" name="option_{{ opt | lower }}"
                           class="form-control" placeholder="Option {{ opt }}" required>
                </div>
                {% endfor %}
                <div class="mb-4">
                    <label class="form-label fw-semibold">Correct Answer</label>
                    <select name="correct_answer" class="form-select" required>
                        {% for opt in ['A', 'B', 'C', 'D'] %}
                        <option value="{{ opt }}">Option {{ opt }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="d-flex gap-2">
                    <button type="submit" class="btn btn-teal px-4">Add Question</button>
                    <a href="{{ url_for('admin.questions', exam_id=exam.id) }}"
                       class="btn btn-outline-secondary px-4">Cancel</a>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}

app/templates/admin/attempt_detail.html
{% extends "base.html" %}
{% block title %}Attempt Detail — ExamProctor{% endblock %}

{% block body %}
<div class="container py-4" style="max-width:860px">

    <!-- Page header -->
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h5 class="section-heading mb-0">Attempt Detail</h5>
        <a href="{{ url_for('admin.dashboard') }}"
           class="btn btn-outline-secondary">← Dashboard</a>
    </div>

    <!-- Summary cards -->
    <div class="row g-3 mb-4">

        <!-- Student -->
        <div class="col-md-3">
            <div class="card text-center p-3 shadow-sm"
                 style="border-top:3px solid #1A5C52">
                <div class="fw-bold" style="color:#1A5C52">
                    {{ attempt.student.name }}
                </div>
                <div class="text-muted small">
                    {{ attempt.student.roll_number }}
                </div>
            </div>
        </div>

        <!-- Exam -->
        <div class="col-md-3">
            <div class="card text-center p-3 shadow-sm"
                 style="border-top:3px solid #B5451B">
                <div class="fw-bold" style="color:#B5451B">
                    {{ attempt.exam.title }}
                </div>
                <div class="text-muted small">
                    {{ attempt.exam.duration }} min exam
                </div>
            </div>
        </div>

        <!-- MCQ Score -->
        <div class="col-md-3">
            <div class="card text-center p-3 shadow-sm"
                 style="border-top:3px solid #1A5C52">
                <div class="fs-3 fw-bold" style="color:#1A5C52">
                    {{ attempt.score }}
                </div>
                <div class="text-muted small">MCQ Score</div>
            </div>
        </div>

        <!-- Suspicion Score -->
        <div class="col-md-3">
            {% if attempt.suspicion_score < 10 %}
                {% set sus = "Low" %}
                {% set sus_color = "#1A6B3C" %}
            {% elif attempt.suspicion_score < 25 %}
                {% set sus = "Medium" %}
                {% set sus_color = "#856404" %}
            {% else %}
                {% set sus = "High" %}
                {% set sus_color = "#7B1A1A" %}
            {% endif %}
            <div class="card text-center p-3 shadow-sm"
                 style="border-top:3px solid {{ sus_color }}">
                <div class="fs-3 fw-bold" style="color:{{ sus_color }}">
                    {{ attempt.suspicion_score }}
                </div>
                <div class="text-muted small">
                    Suspicion Score ({{ sus }})
                </div>
            </div>
        </div>

    </div>

    <!-- Timing info -->
    <div class="card shadow-sm mb-4">
        <div class="card-body">
            <div class="row text-center">

                <div class="col-md-4">
                    <div class="text-muted small">Started</div>
                    <div class="fw-semibold">
                        {{ attempt.start_time.strftime('%d %b %Y, %I:%M:%S %p') }}
                    </div>
                </div>

                <div class="col-md-4">
                    <div class="text-muted small">Submitted</div>
                    <div class="fw-semibold">
                        {% if attempt.end_time %}
                            {{ attempt.end_time.strftime('%d %b %Y, %I:%M:%S %p') }}
                        {% else %}
                            —
                        {% endif %}
                    </div>
                </div>

                <div class="col-md-4">
                    <div class="text-muted small">Time Taken</div>
                    <div class="fw-semibold">
                        {% if attempt.end_time %}
                            {{ ((attempt.end_time - attempt.start_time)
                                .total_seconds() / 60) | int }} min
                        {% else %}
                            —
                        {% endif %}
                    </div>
                </div>

            </div>
        </div>
    </div>

    <!-- Activity logs table -->
    <div class="card shadow-sm">
        <div class="card-header fw-bold text-white"
             style="background:#7B1A1A">
            Activity Logs — {{ logs | length }} event(s) recorded
        </div>
        <div class="card-body p-0">
            <table class="table mb-0">
                <thead class="table-light">
                    <tr>
                        <th>#</th>
                        <th>Event</th>
                        <th>Timestamp</th>
                    </tr>
                </thead>
                <tbody>
                    {% for log in logs %}
                    <tr>
                        <td class="text-muted small">{{ loop.index }}</td>
                        <td>
                            {% if log.event_type == "tab_switch" %}
                                <span class="badge px-2 py-1"
                                      style="background:#FDECEA;color:#7B1A1A">
                                    🔀 Tab Switch
                                </span>
                            {% elif log.event_type == "idle" %}
                                <span class="badge px-2 py-1"
                                      style="background:#FFF3CD;color:#856404">
                                    💤 Idle
                                </span>
                            {% else %}
                                <span class="badge px-2 py-1"
                                      style="background:#E8F0F8;color:#1E5C8A">
                                    ⚡ Fast Submit
                                </span>
                            {% endif %}
                        </td>
                        <td class="small text-muted">
                            {{ log.timestamp.strftime('%d %b %Y, %H:%M:%S') }}
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="3"
                            class="text-center text-muted py-3">
                            No suspicious activity recorded.
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

</div>
{% endblock %}

app/templates/admin/create_exam.html
{% extends "base.html" %}
{% block title %}Create Exam — ExamProctor{% endblock %}

{% block body %}
<div class="container py-5" style="max-width:600px">
    <div class="card shadow-sm" style="border-top:4px solid #1A5C52">
        <div class="card-body p-4">
            <h5 class="section-heading">Create New Exam</h5>
            <form method="POST">
                <div class="mb-3">
                    <label class="form-label fw-semibold">Exam Title</label>
                    <input type="text" name="title" class="form-control"
                           placeholder="e.g. Computer Networks Midterm" required>
                </div>
                <div class="mb-3">
                    <label class="form-label fw-semibold">Duration (minutes)</label>
                    <input type="number" name="duration" class="form-control"
                           placeholder="e.g. 60" min="5" max="300" required>
                </div>
                <div class="mb-3">
                    <label class="form-label fw-semibold">Scheduled Date & Time</label>
                    <input type="datetime-local" name="scheduled_at" class="form-control">
                </div>
                <div class="mb-4">
                    <label class="form-label fw-semibold">Status</label>
                    <select name="status" class="form-select">
                        <option value="draft">Draft</option>
                        <option value="scheduled">Scheduled</option>
                        <option value="active">Active</option>
                        <option value="closed">Closed</option>
                    </select>
                </div>
                <div class="d-flex gap-2">
                    <button type="submit" class="btn btn-teal px-4">Create Exam</button>
                    <a href="{{ url_for('admin.exams') }}"
                       class="btn btn-outline-secondary px-4">Cancel</a>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
app/templates/admin/dashboard.html
{% extends "base.html" %}
{% block title %}Dashboard — ExamProctor{% endblock %}

{% block body %}
<div class="container-fluid">
    <div class="row">

        <!-- Sidebar -->
        <nav class="col-md-2 sidebar py-3 d-none d-md-block">
            <div class="text-white fw-bold px-3 mb-4" style="font-size:1.1rem">
                ⬡ ExamProctor
            </div>
            <ul class="nav flex-column">
                <li><a href="{{ url_for('admin.dashboard') }}" class="nav-link active">⊞ Dashboard</a></li>
                <li><a href="{{ url_for('admin.exams') }}"     class="nav-link">📋 Exams</a></li>
                <li>
                    <a href="{{ url_for('auth.logout') }}"
                       class="nav-link text-danger mt-5">⏻ Logout</a>
                </li>
            </ul>
        </nav>

        <!-- Main content -->
        <main class="col-md-10 px-4 py-4">

            <div class="d-flex justify-content-between align-items-center mb-4">
                <h5 class="section-heading mb-0">Dashboard Overview</h5>
                <span class="text-muted small">
                    Welcome, <b>{{ current_user.username }}</b>
                </span>
            </div>

            <!-- Stat cards -->
            <div class="row g-3 mb-4">
                <div class="col-sm-6 col-xl-3">
                    <div class="card shadow-sm h-100"
                         style="border-left:5px solid #1A5C52">
                        <div class="card-body d-flex justify-content-between align-items-center">
                            <div>
                                <div class="fs-2 fw-bold" style="color:#1A5C52">
                                    {{ total_exams }}
                                </div>
                                <div class="text-muted small">Total Exams</div>
                            </div>
                            <span style="font-size:2rem">📋</span>
                        </div>
                    </div>
                </div>
                <div class="col-sm-6 col-xl-3">
                    <div class="card shadow-sm h-100"
                         style="border-left:5px solid #B5451B">
                        <div class="card-body d-flex justify-content-between align-items-center">
                            <div>
                                <div class="fs-2 fw-bold" style="color:#B5451B">
                                    {{ total_students }}
                                </div>
                                <div class="text-muted small">Total Students</div>
                            </div>
                            <span style="font-size:2rem">👤</span>
                        </div>
                    </div>
                </div>
                <div class="col-sm-6 col-xl-3">
                    <div class="card shadow-sm h-100"
                         style="border-left:5px solid #1A5C52">
                        <div class="card-body d-flex justify-content-between align-items-center">
                            <div>
                                <div class="fs-2 fw-bold" style="color:#1A5C52">
                                    {{ total_attempts }}
                                </div>
                                <div class="text-muted small">Total Attempts</div>
                            </div>
                            <span style="font-size:2rem">📊</span>
                        </div>
                    </div>
                </div>
                <div class="col-sm-6 col-xl-3">
                    <div class="card shadow-sm h-100"
                         style="border-left:5px solid #7B1A1A">
                        <div class="card-body d-flex justify-content-between align-items-center">
                            <div>
                                <div class="fs-2 fw-bold" style="color:#7B1A1A">
                                    {{ flagged }}
                                </div>
                                <div class="text-muted small">Flagged Attempts</div>
                            </div>
                            <span style="font-size:2rem">🚨</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Recent attempts -->
            <div class="card shadow-sm">
                <div class="card-header text-white fw-bold"
                     style="background:#1A5C52">
                    Recent Exam Attempts
                </div>
                <div class="card-body p-0">
                    <table class="table table-hover mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Student</th>
                                <th>Exam</th>
                                <th>Score</th>
                                <th>Suspicion</th>
                                <th>Date</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for a in recent_attempts %}
                            {% if a.suspicion_score < 10 %}
                                {% set sus = "Low" %}
                                {% set sus_bg = "#D4EDDA" %}
                                {% set sus_color = "#1A6B3C" %}
                            {% elif a.suspicion_score < 25 %}
                                {% set sus = "Medium" %}
                                {% set sus_bg = "#FFF3CD" %}
                                {% set sus_color = "#856404" %}
                            {% else %}
                                {% set sus = "High" %}
                                {% set sus_bg = "#FDECEA" %}
                                {% set sus_color = "#7B1A1A" %}
                            {% endif %}
                            <tr>
                                <td>{{ a.student.name }}</td>
                                <td>{{ a.exam.title }}</td>
                                <td>{{ a.score }}</td>
                                <td>
                                    <span class="badge px-2 py-1"
                                          style="background:{{ sus_bg }};color:{{ sus_color }}">
                                        {{ sus }}
                                    </span>
                                </td>
                                <td class="text-muted small">
                                    {{ a.start_time.strftime('%d %b %Y') }}
                                </td>
                                <td>
                                    <a href="{{ url_for('admin.attempt_detail', attempt_id=a.id) }}"
                                       class="btn btn-sm btn-outline-secondary">
                                        View
                                    </a>
                                </td>
                            </tr>
                            {% else %}
                            <tr>
                                <td colspan="6" class="text-center text-muted py-3">
                                    No attempts yet.
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

        </main>
    </div>
</div>
{% endblock %}
app/templates/admin/edit_exam.html
{% extends "base.html" %}
{% block title %}Edit Exam — ExamProctor{% endblock %}

{% block body %}
<div class="container py-5" style="max-width:600px">
    <div class="card shadow-sm" style="border-top:4px solid #B5451B">
        <div class="card-body p-4">
            <h5 class="section-heading">Edit Exam</h5>
            <form method="POST">
                <div class="mb-3">
                    <label class="form-label fw-semibold">Exam Title</label>
                    <input type="text" name="title" class="form-control"
                           value="{{ exam.title }}" required>
                </div>
                <div class="mb-3">
                    <label class="form-label fw-semibold">Duration (minutes)</label>
                    <input type="number" name="duration" class="form-control"
                           value="{{ exam.duration }}" min="5" max="300" required>
                </div>
                <div class="mb-3">
                    <label class="form-label fw-semibold">Scheduled Date & Time</label>
                    <input type="datetime-local" name="scheduled_at" class="form-control"
                           value="{{ exam.scheduled_at.strftime('%Y-%m-%dT%H:%M') if exam.scheduled_at else '' }}">
                </div>
                <div class="mb-4">
                    <label class="form-label fw-semibold">Status</label>
                    <select name="status" class="form-select">
                        {% for s in ['draft','scheduled','active','closed'] %}
                        <option value="{{ s }}" {{ 'selected' if exam.status == s }}>
                            {{ s | capitalize }}
                        </option>
                        {% endfor %}
                    </select>
                </div>
                <div class="d-flex gap-2">
                    <button type="submit" class="btn btn-rust px-4">Save Changes</button>
                    <a href="{{ url_for('admin.exams') }}"
                       class="btn btn-outline-secondary px-4">Cancel</a>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
app/templates/admin/exams.html
{% extends "base.html" %}
{% block title %}Exams — ExamProctor{% endblock %}

{% block body %}
<div class="container-fluid">
    <div class="row">
        <nav class="col-md-2 sidebar py-3 d-none d-md-block">
            <div class="text-white fw-bold px-3 mb-4" style="font-size:1.1rem">⬡ ExamProctor</div>
            <ul class="nav flex-column">
                <li><a href="{{ url_for('admin.dashboard') }}" class="nav-link">⊞ Dashboard</a></li>
                <li><a href="{{ url_for('admin.exams') }}"     class="nav-link active">📋 Exams</a></li>
                <li><a href="{{ url_for('auth.logout') }}"     class="nav-link text-danger mt-5">⏻ Logout</a></li>
            </ul>
        </nav>
        <main class="col-md-10 px-4 py-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h5 class="section-heading mb-0">All Exams</h5>
                <a href="{{ url_for('admin.create_exam') }}" class="btn btn-teal">+ Create Exam</a>
            </div>
            <div class="card shadow-sm">
                <div class="card-body p-0">
                    <table class="table table-hover mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Title</th><th>Duration</th><th>Scheduled</th>
                                <th>Questions</th><th>Status</th><th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for e in exams %}
                            <tr>
                                <td class="fw-semibold">{{ e.title }}</td>
                                <td>{{ e.duration }} min</td>
                                <td class="small text-muted">
                                    {{ e.scheduled_at.strftime('%d %b %Y, %I:%M %p') if e.scheduled_at else '—' }}
                                </td>
                                <td>{{ e.questions | length }}</td>
                                <td>
                                    <span class="badge
                                        {% if e.status == 'scheduled' %}bg-success
                                        {% elif e.status == 'active' %}bg-warning text-dark
                                        {% elif e.status == 'closed' %}bg-secondary
                                        {% else %}bg-light text-dark border{% endif %}">
                                        {{ e.status }}
                                    </span>
                                </td>
                                <td>
                                    <a href="{{ url_for('admin.questions', exam_id=e.id) }}"
                                       class="btn btn-sm btn-outline-secondary me-1">Questions</a>
                                    <a href="{{ url_for('admin.edit_exam', exam_id=e.id) }}"
                                       class="btn btn-sm btn-outline-primary me-1">Edit</a>
                                    <form method="POST"
                                          action="{{ url_for('admin.delete_exam', exam_id=e.id) }}"
                                          class="d-inline"
                                          onsubmit="return confirm('Delete this exam?')">
                                        <button class="btn btn-sm btn-outline-danger">Delete</button>
                                    </form>
                                </td>
                            </tr>
                            {% else %}
                            <tr>
                                <td colspan="6" class="text-center text-muted py-4">
                                    No exams yet.
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </main>
    </div>
</div>
{% endblock %}
app/templates/admin/questions.html
{% extends "base.html" %}
{% block title %}Questions — ExamProctor{% endblock %}

{% block body %}
<div class="container py-4" style="max-width:900px">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <h5 class="section-heading mb-0">Questions — {{ exam.title }}</h5>
            <span class="text-muted small">
                {{ exam.questions | length }} question(s) · {{ exam.duration }} min
            </span>
        </div>
        <div class="d-flex gap-2">
            <a href="{{ url_for('admin.add_question', exam_id=exam.id) }}"
               class="btn btn-teal">+ Add Question</a>
            <a href="{{ url_for('admin.exams') }}"
               class="btn btn-outline-secondary">← Back</a>
        </div>
    </div>

    {% for q in exam.questions %}
    <div class="card mb-3 shadow-sm">
        <div class="card-body">
            <div class="d-flex justify-content-between">
                <p class="fw-semibold mb-2">
                    <span style="color:#B5451B">Q{{ loop.index }}.</span>
                    {{ q.question_text }}
                </p>
                <form method="POST"
                      action="{{ url_for('admin.delete_question', q_id=q.id) }}"
                      onsubmit="return confirm('Delete this question?')">
                    <button class="btn btn-sm btn-outline-danger">Delete</button>
                </form>
            </div>
            <div class="row row-cols-2 g-2 mt-1">
                {% for opt, text in [('A', q.option_a), ('B', q.option_b),
                                     ('C', q.option_c), ('D', q.option_d)] %}
                <div class="col">
                    <span class="px-2 py-1 rounded small d-block
                        {% if opt == q.correct_answer %}fw-bold{% endif %}"
                        style="background:{{ '#E8F2F0' if opt == q.correct_answer else '#F7F3EE' }};
                               color:{{ '#1A5C52' if opt == q.correct_answer else '#555' }}">
                        {% if opt == q.correct_answer %}✓ {% endif %}
                        {{ opt }}. {{ text }}
                    </span>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
    {% else %}
    <div class="text-center text-muted py-5">
        <p>No questions yet.</p>
        <a href="{{ url_for('admin.add_question', exam_id=exam.id) }}"
           class="btn btn-teal">Add First Question</a>
    </div>
    {% endfor %}
</div>
{% endblock %}


## app/templates/auth/login.html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login — ExamProctor</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body style="background:#F7F3EE">

<div class="min-vh-100 d-flex align-items-center justify-content-center">
    <div class="card shadow-sm" style="width:100%;max-width:420px;border-top:4px solid #1A5C52">
        <div class="card-body p-4">

            <h4 class="fw-bold text-center mb-1" style="color:#1A5C52">ExamProctor</h4>
            <p class="text-center text-muted small mb-4">Admin Login</p>

            <!-- Flash messages -->
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }} py-2">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}

            <form method="POST">
                <div class="mb-3">
                    <label class="form-label fw-semibold">Username</label>
                    <input type="text" name="username" class="form-control"
                           placeholder="Enter username" required autofocus>
                </div>
                <div class="mb-4">
                    <label class="form-label fw-semibold">Password</label>
                    <input type="password" name="password" class="form-control"
                           placeholder="Enter password" required>
                </div>
                <button type="submit" class="btn w-100 py-2 fw-semibold text-white"
                        style="background:#1A5C52">Login</button>
            </form>

        </div>
    </div>
</div>

</body>
</html>

## app/templates/student/detail.html
{% extends "base.html" %}
{% block title %}Attempt Detail — ExamProctor{% endblock %}

{% block body %}
<div class="container py-4" style="max-width:860px">

    <div class="d-flex justify-content-between align-items-center mb-4">
        <h5 class="section-heading mb-0">Attempt Detail</h5>
        <a href="{{ url_for('admin.dashboard') }}"
           class="btn btn-outline-secondary">← Dashboard</a>
    </div>

    <!-- Summary -->
    <div class="row g-3 mb-4">
        <div class="col-md-3">
            <div class="card text-center p-3 shadow-sm"
                 style="border-top:3px solid #1A5C52">
                <div class="fw-bold" style="color:#1A5C52">
                    {{ attempt.student.name }}
                </div>
                <div class="text-muted small">
                    {{ attempt.student.roll_number }}
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card text-center p-3 shadow-sm"
                 style="border-top:3px solid #B5451B">
                <div class="fw-bold" style="color:#B5451B">
                    {{ attempt.exam.title }}
                </div>
                <div class="text-muted small">
                    {{ attempt.exam.duration }} min exam
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card text-center p-3 shadow-sm"
                 style="border-top:3px solid #1A5C52">
                <div class="fs-3 fw-bold" style="color:#1A5C52">
                    {{ attempt.score }}
                </div>
                <div class="text-muted small">MCQ Score</div>
            </div>
        </div>
        <div class="col-md-3">
            {% if attempt.suspicion_score < 10 %}
                {% set sus = "Low" %}
                {% set sus_color = "#1A6B3C" %}
            {% elif attempt.suspicion_score < 25 %}
                {% set sus = "Medium" %}
                {% set sus_color = "#856404" %}
            {% else %}
                {% set sus = "High" %}
                {% set sus_color = "#7B1A1A" %}
            {% endif %}
            <div class="card text-center p-3 shadow-sm"
                 style="border-top:3px solid {{ sus_color }}">
                <div class="fs-3 fw-bold" style="color:{{ sus_color }}">
                    {{ attempt.suspicion_score }}
                </div>
                <div class="text-muted small">
                    Suspicion Score ({{ sus }})
                </div>
            </div>
        </div>
    </div>

    <!-- Timing -->
    <div class="card shadow-sm mb-4">
        <div class="card-body">
            <div class="row text-center">
                <div class="col-md-4">
                    <div class="text-muted small">Started</div>
                    <div class="fw-semibold">
                        {{ attempt.start_time.strftime('%d %b %Y, %I:%M:%S %p') }}
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="text-muted small">Submitted</div>
                    <div class="fw-semibold">
                        {{ attempt.end_time.strftime('%d %b %Y, %I:%M:%S %p')
                           if attempt.end_time else '—' }}
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="text-muted small">Time Taken</div>
                    <div class="fw-semibold">
                        {% if attempt.end_time %}
                            {{ ((attempt.end_time - attempt.start_time)
                                .total_seconds() / 60) | int }} min
                        {% else %}—{% endif %}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Activity Logs -->
    <div class="card shadow-sm">
        <div class="card-header fw-bold text-white"
             style="background:#7B1A1A">
            Activity Logs ({{ logs | length }} events)
        </div>
        <div class="card-body p-0">
            <table class="table mb-0">
                <thead class="table-light">
                    <tr>
                        <th>#</th>
                        <th>Event</th>
                        <th>Time</th>
                    </tr>
                </thead>
                <tbody>
                    {% for log in logs %}
                    <tr>
                        <td class="text-muted small">{{ loop.index }}</td>
                        <td>
                            {% if log.event_type == "tab_switch" %}
                                <span class="badge px-2 py-1"
                                      style="background:#FDECEA;color:#7B1A1A">
                                    🔀 Tab Switch
                                </span>
                            {% elif log.event_type == "idle" %}
                                <span class="badge px-2 py-1"
                                      style="background:#FFF3CD;color:#856404">
                                    💤 Idle
                                </span>
                            {% else %}
                                <span class="badge px-2 py-1"
                                      style="background:#E8F0F8;color:#1E5C8A">
                                    ⚡ Fast Submit
                                </span>
                            {% endif %}
                        </td>
                        <td class="small text-muted">
                            {{ log.timestamp.strftime('%H:%M:%S') }}
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="3"
                            class="text-center text-muted py-3">
                            No suspicious activity recorded.
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

</div>
{% endblock %}
## app/templates/student/enter.html
{% extends "base.html" %}
{% block title %}Enter Exam — ExamProctor{% endblock %}

{% block body %}
<div class="min-vh-100 d-flex align-items-center justify-content-center"
     style="background:#F7F3EE">
    <div class="card shadow-sm"
         style="width:100%;max-width:480px;border-top:4px solid #1A5C52">
        <div class="card-body p-4">

            <h5 class="fw-bold mb-1" style="color:#1A5C52">Enter Exam</h5>
            <p class="text-muted small mb-4">
                Fill in your details and select the exam to begin.
            </p>

            <form method="POST">
                <div class="mb-3">
                    <label class="form-label fw-semibold">Full Name</label>
                    <input type="text" name="name" class="form-control"
                           placeholder="Your full name" required>
                </div>
                <div class="mb-3">
                    <label class="form-label fw-semibold">Roll Number</label>
                    <input type="text" name="roll_number" class="form-control"
                           placeholder="e.g. BCA2024001" required>
                </div>
                <div class="mb-4">
                    <label class="form-label fw-semibold">Select Exam</label>
                    <select name="exam_id" class="form-select" required>
                        <option value="">— Choose an exam —</option>
                        {% for exam in exams %}
                        <option value="{{ exam.id }}">
                            {{ exam.title }} ({{ exam.duration }} min)
                        </option>
                        {% endfor %}
                    </select>
                </div>
                <button type="submit"
                        class="btn btn-teal w-100 py-2 fw-semibold">
                    Start Exam →
                </button>
            </form>

        </div>
    </div>
</div>
{% endblock %}
## app/templates/student/exam.html
{% extends "base.html" %}
{% block title %}{{ exam.title }} — ExamProctor{% endblock %}

{% block body %}

<!-- Hidden div — proctor.js reads attempt_id and duration from here -->
<div id="proctor-data"
     data-attempt-id="{{ attempt.id }}"
     data-duration="{{ exam.duration }}"
     style="display:none">
</div>

<!-- Sticky top bar with timer -->
<div class="sticky-top bg-white border-bottom shadow-sm py-2 px-4
            d-flex justify-content-between align-items-center">
    <div>
        <span class="fw-bold" style="color:#1A5C52">{{ exam.title }}</span>
        <span class="text-muted small ms-2">
            {{ questions | length }} questions
        </span>
    </div>
    <div class="text-center">
        <div class="small text-muted">Time Remaining</div>
        <div id="timer-display"
             style="font-size:1.8rem;font-weight:700;
                    color:#1A5C52;letter-spacing:2px">
            --:--
        </div>
    </div>
    <div>
        <button type="submit" form="exam-form"
                class="btn btn-rust fw-semibold px-4">
            Submit Exam
        </button>
    </div>
</div>

<!-- Questions -->
<div class="container py-4" style="max-width:780px">
    <form id="exam-form" method="POST"
          action="{{ url_for('student.submit_exam', attempt_id=attempt.id) }}">

        {% for q in questions %}
        <div class="card mb-3 shadow-sm"
             style="border-radius:10px;border:1px solid #dee2e6">
            <div class="card-body p-4">

                <p class="fw-semibold mb-3">
                    <span style="color:#B5451B">Q{{ loop.index }}.</span>
                    {{ q.question_text }}
                </p>

                {% for opt, text in [('A', q.option_a), ('B', q.option_b),
                                     ('C', q.option_c), ('D', q.option_d)] %}
                <div class="mb-2">
                    <input type="radio"
                           name="q_{{ q.id }}"
                           id="q{{ q.id }}_{{ opt }}"
                           value="{{ opt }}"
                           class="d-none">
                    <label for="q{{ q.id }}_{{ opt }}"
                           class="d-block px-3 py-2 rounded"
                           style="border:1px solid #dee2e6;cursor:pointer;
                                  transition:background 0.15s">
                        <span class="fw-bold me-2" style="color:#1A5C52">
                            {{ opt }}.
                        </span>
                        {{ text }}
                    </label>
                </div>
                {% endfor %}

            </div>
        </div>
        {% endfor %}

        <div class="text-end mt-3 mb-5">
            <button type="submit" class="btn btn-rust fw-semibold px-5 py-2">
                Submit Exam
            </button>
        </div>

    </form>
</div>
{% endblock %}

{% block scripts %}
<script src="{{ url_for('static', filename='js/proctor.js') }}"></script>

<!-- Highlight selected option -->
<script>
document.querySelectorAll('input[type="radio"]').forEach(function(radio) {
    radio.addEventListener("change", function() {
        const name = this.name;
        document.querySelectorAll(`input[name="${name}"]`).forEach(function(r) {
            const label = document.querySelector(`label[for="${r.id}"]`);
            label.style.background = "";
            label.style.borderColor = "#dee2e6";
            label.style.fontWeight  = "";
        });
        const selected = document.querySelector(`label[for="${this.id}"]`);
        selected.style.background   = "#E8F2F0";
        selected.style.borderColor  = "#1A5C52";
        selected.style.fontWeight   = "600";
    });
});
</script>
{% endblock %}
## app/templates/student/result.html
{% extends "base.html" %}
{% block title %}Result — ExamProctor{% endblock %}

{% block body %}
<div class="min-vh-100 d-flex align-items-center justify-content-center"
     style="background:#F7F3EE">
    <div class="card shadow-sm text-center"
         style="width:100%;max-width:480px;border-top:4px solid #1A5C52">
        <div class="card-body p-5">

            <!-- Icon based on suspicion level -->
            <div style="font-size:3.5rem">
                {% if attempt.suspicion_score >= 25 %}🚨
                {% elif attempt.suspicion_score >= 10 %}⚠️
                {% else %}✅
                {% endif %}
            </div>

            <h4 class="fw-bold mt-3" style="color:#1A5C52">
                Exam Submitted!
            </h4>
            <p class="text-muted">{{ attempt.exam.title }}</p>

            <hr>

            <div class="row g-3 my-2">
                <!-- Score -->
                <div class="col-6">
                    <div class="p-3 rounded" style="background:#E8F2F0">
                        <div class="fs-2 fw-bold" style="color:#1A5C52">
                            {{ attempt.score }} / {{ total }}
                        </div>
                        <div class="small text-muted">Your Score</div>
                    </div>
                </div>

                <!-- Suspicion level -->
                <div class="col-6">
                    {% if attempt.suspicion_score < 10 %}
                        {% set sus = "Low" %}
                        {% set sus_bg = "#D4EDDA" %}
                        {% set sus_color = "#1A6B3C" %}
                    {% elif attempt.suspicion_score < 25 %}
                        {% set sus = "Medium" %}
                        {% set sus_bg = "#FFF3CD" %}
                        {% set sus_color = "#856404" %}
                    {% else %}
                        {% set sus = "High" %}
                        {% set sus_bg = "#FDECEA" %}
                        {% set sus_color = "#7B1A1A" %}
                    {% endif %}
                    <div class="p-3 rounded"
                         style="background:{{ sus_bg }}">
                        <div class="fs-2 fw-bold"
                             style="color:{{ sus_color }}">
                            {{ sus }}
                        </div>
                        <div class="small text-muted">Suspicion Level</div>
                    </div>
                </div>
            </div>

            <!-- Time taken -->
            <p class="text-muted small mt-3">
                Time taken:
                {% if attempt.end_time and attempt.start_time %}
                    {{ ((attempt.end_time - attempt.start_time)
                        .total_seconds() / 60) | int }} minutes
                {% else %}—
                {% endif %}
            </p>

            <a href="{{ url_for('student.enter_exam') }}"
               class="btn btn-teal mt-2 px-4">
                Back to Exam Entry
            </a>

        </div>
    </div>
</div>
{% endblock %}

## app/templates/base.html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}ExamProctor{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root {
            --teal: #1A5C52;
            --rust: #B5451B;
            --gray-bg: #F7F3EE;
        }
        body { background: var(--gray-bg); }
        .sidebar {
            min-height: 100vh;
            background: #12403A;
        }
        .sidebar .nav-link {
            color: rgba(255,255,255,0.75);
            padding: 0.7rem 1.2rem;
            border-radius: 6px;
            margin: 2px 8px;
        }
        .sidebar .nav-link:hover,
        .sidebar .nav-link.active {
            background: var(--teal);
            color: white;
            border-left: 3px solid var(--rust);
        }
        .section-heading {
            color: var(--teal);
            font-weight: 700;
            border-bottom: 2px solid #E8F2F0;
            padding-bottom: 0.4rem;
        }
        .btn-teal {
            background: var(--teal);
            color: white;
            border: none;
        }
        .btn-teal:hover { background: #144a41; color: white; }
        .btn-rust {
            background: var(--rust);
            color: white;
            border: none;
        }
        .btn-rust:hover { background: #8f3614; color: white; }
    </style>
</head>
<body>

{% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
        <div class="position-fixed top-0 end-0 p-3" style="z-index:9999">
            {% for category, message in messages %}
                <div class="alert alert-{{ category }} alert-dismissible shadow" role="alert">
                    {{ message }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            {% endfor %}
        </div>
    {% endif %}
{% endwith %}

{% block body %}{% endblock %}

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
{% block scripts %}{% endblock %}
</body>
</html>


##app/__init__.py
import os
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db            = SQLAlchemy()
login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    from app.models import Admin
    return Admin.query.get(int(user_id))


def create_app():
    app = Flask(__name__,
                template_folder=os.path.join(os.path.dirname(__file__), "templates"),
                static_folder=os.path.join(os.path.dirname(__file__), "static"))

    app.config.from_object("app.config.Config")

    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view            = "auth.login"
    login_manager.login_message         = "Please login first."
    login_manager.login_message_category = "warning"

    from app.auth.routes      import auth_bp
    from app.admin.routes     import admin_bp
    from app.student.routes   import student_bp
    from app.proctoring.routes import proctoring_bp

    app.register_blueprint(auth_bp,       url_prefix="/auth")
    app.register_blueprint(admin_bp,      url_prefix="/admin")
    app.register_blueprint(student_bp,    url_prefix="/student")
    app.register_blueprint(proctoring_bp, url_prefix="/proctor")

    @app.route("/")
    def home():
        return redirect(url_for("auth.login"))

    with app.app_context():
        from app.models import Admin
        db.create_all()

        if not Admin.query.first():
            admin = Admin(username="admin")
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
            print("Default admin created — username: admin | password: admin123")

    return app
## app/config.py
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "dev-secret-key"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "..", "exam_proctor.db")import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "dev-secret-key"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "..", "exam_proctor.db")
## app/models.py

from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class Admin(UserMixin, db.Model):
    __tablename__ = "admins"

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    exams = db.relationship("Exam", backref="creator", lazy=True,
                            cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Admin {self.username}>"


class Student(db.Model):
    __tablename__ = "students"

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(120), nullable=False)
    roll_number = db.Column(db.String(50), unique=True, nullable=False)
    email       = db.Column(db.String(120), nullable=True)

    attempts = db.relationship("Attempt", backref="student", lazy=True,
                               cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Student {self.name}>"


class Exam(db.Model):
    __tablename__ = "exams"

    id           = db.Column(db.Integer, primary_key=True)
    admin_id     = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=False)
    title        = db.Column(db.String(200), nullable=False)
    duration     = db.Column(db.Integer, nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=True)
    status       = db.Column(db.String(20), default="draft")
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    questions = db.relationship("Question", backref="exam", lazy=True,
                                cascade="all, delete-orphan")
    attempts  = db.relationship("Attempt", backref="exam", lazy=True,
                                cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Exam {self.title}>"


class Question(db.Model):
    __tablename__ = "questions"

    id             = db.Column(db.Integer, primary_key=True)
    exam_id        = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False)
    question_text  = db.Column(db.Text, nullable=False)
    option_a       = db.Column(db.String(300), nullable=False)
    option_b       = db.Column(db.String(300), nullable=False)
    option_c       = db.Column(db.String(300), nullable=False)
    option_d       = db.Column(db.String(300), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)

    def __repr__(self):
        return f"<Question {self.id}>"


class Attempt(db.Model):
    __tablename__ = "attempts"

    id              = db.Column(db.Integer, primary_key=True)
    student_id      = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    exam_id         = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False)
    start_time      = db.Column(db.DateTime, default=datetime.utcnow)
    end_time        = db.Column(db.DateTime, nullable=True)
    score           = db.Column(db.Integer, default=0)
    suspicion_score = db.Column(db.Integer, default=0)

    activity_logs = db.relationship("ActivityLog", backref="attempt", lazy=True,
                                    cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Attempt {self.id}>"


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id         = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("attempts.id"), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    timestamp  = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ActivityLog {self.event_type}>"

app/run.py
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

