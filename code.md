## app/admin/__init__.py
from flask import Blueprint

admin_bp = Blueprint("admin", __name__)

from . import routes


<!-- app/admin/routes.py -->
# app/admin/routes.py

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
                           recent_attempts=recent_attempts)

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

    return render_template("admin/create_exam.html")


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


<!-- app/auth/__init__.py -->
# app/auth/__init__.py

from flask import Blueprint

auth_bp = Blueprint("auth", __name__)

from . import routes

<!-- app/auth/routes.py -->
# app/auth/routes.py

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required

from . import auth_bp
from app.models import Admin


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.check_password(password):

            login_user(admin)

            flash("Login successful", "success")

            return redirect(url_for("admin.dashboard"))

        flash("Invalid username or password", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Logged out successfully", "info")

    return redirect(url_for("auth.login"))

    # Secret code for admin registration
# Change this to something only you know
ADMIN_SECRET_CODE = "ICSC@2026"


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username   = request.form.get("username", "").strip()
        password   = request.form.get("password", "")
        secret     = request.form.get("secret_code", "")

        if secret != ADMIN_SECRET_CODE:
            flash("Invalid registration code.", "danger")
            return redirect(url_for("auth.register"))

        if Admin.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for("auth.register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return redirect(url_for("auth.register"))

        admin = Admin(username=username)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        flash("Admin account created. Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")

<!-- app/proctoring/__init__.py -->
from flask import Blueprint

proctoring_bp = Blueprint("proctoring", __name__)
<!-- app/proctoring/routes.py -->
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

<!-- app/static/js/proctor.js -->
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

<!-- app/static/js/ui.js -->
/* ============================================================
   ExamProctor — UI Enhancement Script
   Handles: sidebar toggle, tooltips, animations, mobile nav
   ============================================================ */

   document.addEventListener('DOMContentLoaded', function () {

    // ── Mobile Sidebar Toggle ──────────────────────────────────
    const sidebar  = document.querySelector('.sidebar');
    const overlay  = document.querySelector('.sidebar-overlay');
    const menuBtn  = document.getElementById('sidebar-toggle');
  
    if (menuBtn && sidebar && overlay) {
      menuBtn.addEventListener('click', function () {
        sidebar.classList.toggle('open');
        overlay.classList.toggle('active');
      });
      overlay.addEventListener('click', function () {
        sidebar.classList.remove('open');
        overlay.classList.remove('active');
      });
    }
  
    // ── Auto-dismiss Flash Alerts ──────────────────────────────
    document.querySelectorAll('.alert-dismissible').forEach(function (alert) {
      setTimeout(function () {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
        if (bsAlert) bsAlert.close();
      }, 4500);
    });
  
    // ── Animate Stat Cards on Scroll ──────────────────────────
    const observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-fade-up');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });
  
    document.querySelectorAll('.stat-card').forEach(function (card) {
      observer.observe(card);
    });
  
    // ── Animate Number Counters ────────────────────────────────
    document.querySelectorAll('.stat-value[data-count]').forEach(function (el) {
      const target   = parseInt(el.dataset.count, 10);
      const duration = 800;
      const step     = target / (duration / 16);
      let current    = 0;
  
      const timer = setInterval(function () {
        current += step;
        if (current >= target) {
          el.textContent = target;
          clearInterval(timer);
        } else {
          el.textContent = Math.floor(current);
        }
      }, 16);
    });
  
    // ── Confirm Delete Buttons ─────────────────────────────────
    document.querySelectorAll('[data-confirm]').forEach(function (el) {
      el.addEventListener('click', function (e) {
        if (!confirm(el.dataset.confirm)) {
          e.preventDefault();
          e.stopPropagation();
        }
      });
    });
  
    // ── Tooltip Initialisation (Bootstrap) ────────────────────
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(function (el) {
      new bootstrap.Tooltip(el, { placement: 'top' });
    });
  
    // ── Password Visibility Toggle ─────────────────────────────
    document.querySelectorAll('.toggle-password').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const target = document.getElementById(btn.dataset.target);
        if (!target) return;
        const isText  = target.type === 'text';
        target.type   = isText ? 'password' : 'text';
        btn.innerHTML = isText
          ? '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8M1.173 8a13 13 0 0 1 1.66-2.043C4.12 4.668 5.88 3.5 8 3.5s3.879 1.168 5.168 2.457A13 13 0 0 1 14.828 8q-.086.13-.195.288c-.335.48-.83 1.12-1.465 1.755C11.879 11.332 10.119 12.5 8 12.5s-3.879-1.168-5.168-2.457A13 13 0 0 1 1.172 8z"/><path d="M8 5.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5M4.5 8a3.5 3.5 0 1 1 7 0 3.5 3.5 0 0 1-7 0"/></svg>'
          : '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.359 11.238C15.06 9.72 16 8 16 8s-3-5.5-8-5.5a7 7 0 0 0-2.79.588l.77.771A6 6 0 0 1 8 3.5c2.12 0 3.879 1.168 5.168 2.457A13 13 0 0 1 14.828 8q-.086.13-.195.288c-.335.48-.83 1.12-1.465 1.755q-.247.248-.517.486z"/><path d="M11.297 9.176a3.5 3.5 0 0 0-4.474-4.474l.823.823a2.5 2.5 0 0 1 2.829 2.829zm-2.943 1.299.822.822a3.5 3.5 0 0 1-4.474-4.474l.823.823a2.5 2.5 0 0 0 2.829 2.829"/><path d="M3.35 5.47q-.27.24-.518.487A13 13 0 0 0 1.172 8l.195.288c.335.48.83 1.12 1.465 1.755C4.121 11.332 5.881 12.5 8 12.5c.716 0 1.39-.133 2.02-.36l.77.772A7 7 0 0 1 8 13.5C3 13.5 0 8 0 8s.939-1.721 2.641-3.238l.708.709zm10.296 8.884-12-12 .708-.708 12 12z"/></svg>';
      });
    });
  
    // ── Exam option highlight (replaces inline JS) ─────────────
    document.querySelectorAll('input[type="radio"].option-radio').forEach(function (radio) {
      radio.addEventListener('change', function () {
        const name = this.name;
        // Reset all labels in this group
        document.querySelectorAll(`input[name="${name}"].option-radio`).forEach(function (r) {
          const lbl = r.closest('.option-label');
          if (lbl) lbl.classList.remove('selected');
        });
        // Activate chosen label
        const chosenLbl = this.closest('.option-label');
        if (chosenLbl) chosenLbl.classList.add('selected');
      });
    });
  
  });

app/student/__init__.py
# app/student/__init__.py

from flask import Blueprint

student_bp = Blueprint("student", __name__)

from . import routes

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

app/__init__.py
# app/__init__.py

from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    from app.models import Admin
    return Admin.query.get(int(user_id))


def create_app():

    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please login first."
    login_manager.login_message_category = "warning"

    # Register blueprints
    from app.auth import auth_bp
    from app.admin import admin_bp
    from app.student import student_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(student_bp, url_prefix="/student")

    @app.route("/")
    def home():
        return redirect(url_for("auth.login"))

    with app.app_context():

        from app.models import Admin

        db.create_all()

        # Create default admin
        if not Admin.query.first():

            admin = Admin(username="admin")
            admin.set_password("admin123")

            db.session.add(admin)
            db.session.commit()

            print("Default admin created")
            print("Username: admin")
            print("Password: admin123")

    return app                         

app/models.py
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

app/templates/admin/add_question.html
{% extends "base.html" %}
{% block title %}Add Question — ExamProctor{% endblock %}

{% block body %}
<div class="app-wrapper">

    <aside class="sidebar">
        <div class="sidebar-brand">
            <div class="brand-name">
                <i class="bi bi-shield-check me-2"></i>ExamProctor
            </div>
            <div class="brand-sub">Admin Panel</div>
        </div>
        <nav class="sidebar-nav">
            <div class="nav-label">Main</div>
            <a href="{{ url_for('admin.dashboard') }}" class="nav-link">
                <i class="bi bi-grid-1x2"></i> Dashboard
            </a>
            <a href="{{ url_for('admin.exams') }}" class="nav-link active">
                <i class="bi bi-journal-text"></i> Exams
            </a>
            <div class="nav-label mt-2">Students</div>
            <a href="{{ url_for('student.enter_exam') }}" class="nav-link">
                <i class="bi bi-person-badge"></i> Student Entry
            </a>
        </nav>
        <div class="sidebar-footer">
            <a href="{{ url_for('auth.logout') }}" class="nav-link">
                <i class="bi bi-box-arrow-left"></i> Logout
            </a>
        </div>
    </aside>

    <div class="main-content">
        <div class="topbar">
            <span class="topbar-title">
                <a href="{{ url_for('admin.questions', exam_id=exam.id) }}"
                   style="color:#1A5C52;text-decoration:none">
                    <i class="bi bi-chevron-left me-1"></i>Questions
                </a>
                &nbsp;/&nbsp; Add Question
            </span>
        </div>

        <div class="page-body">
            <div class="page-header">
                <h4>Add Question</h4>
                <p>Adding to: <strong>{{ exam.title }}</strong></p>
            </div>

            <div class="ep-card" style="max-width:680px">
                <div class="ep-card-header">
                    <h6>
                        <i class="bi bi-plus-circle"></i>
                        New MCQ Question
                    </h6>
                </div>
                <div class="p-4">
                    <form method="POST">

                        <div class="mb-4">
                            <label class="form-label">Question Text</label>
                            <textarea name="question_text"
                                      class="form-control" rows="3"
                                      placeholder="Write your question here..."
                                      required></textarea>
                        </div>

                        <div class="row g-3 mb-4">
                            {% for opt in ['A', 'B', 'C', 'D'] %}
                            <div class="col-md-6">
                                <label class="form-label">
                                    <span style="background:#E8F2F0;color:#1A5C52;
                                                 padding:1px 7px;border-radius:4px;
                                                 font-size:0.78rem;font-weight:700">
                                        {{ opt }}
                                    </span>
                                    &nbsp;Option {{ opt }}
                                </label>
                                <input type="text"
                                       name="option_{{ opt | lower }}"
                                       class="form-control"
                                       placeholder="Option {{ opt }}"
                                       required>
                            </div>
                            {% endfor %}
                        </div>

                        <div class="mb-4">
                            <label class="form-label">Correct Answer</label>
                            <select name="correct_answer" class="form-select" required>
                                {% for opt in ['A', 'B', 'C', 'D'] %}
                                <option value="{{ opt }}">Option {{ opt }}</option>
                                {% endfor %}
                            </select>
                        </div>

                        <div class="d-flex gap-2">
                            <button type="submit" class="btn-ep-primary">
                                <i class="bi bi-check-lg"></i>
                                Save Question
                            </button>
                            <a href="{{ url_for('admin.questions', exam_id=exam.id) }}"
                               class="btn-ep-secondary">
                                <i class="bi bi-x-lg"></i>
                                Cancel
                            </a>
                        </div>

                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
admin/attempt_detail.html
{% extends "base.html" %}
{% block title %}Attempt Detail — ExamProctor{% endblock %}

{% block body %}
<div class="app-wrapper">

    <aside class="sidebar">
        <div class="sidebar-brand">
            <div class="brand-name">
                <i class="bi bi-shield-check me-2"></i>ExamProctor
            </div>
            <div class="brand-sub">Admin Panel</div>
        </div>
        <nav class="sidebar-nav">
            <div class="nav-label">Main</div>
            <a href="{{ url_for('admin.dashboard') }}" class="nav-link active">
                <i class="bi bi-grid-1x2"></i> Dashboard
            </a>
            <a href="{{ url_for('admin.exams') }}" class="nav-link">
                <i class="bi bi-journal-text"></i> Exams
            </a>
        </nav>
        <div class="sidebar-footer">
            <a href="{{ url_for('auth.logout') }}" class="nav-link">
                <i class="bi bi-box-arrow-left"></i> Logout
            </a>
        </div>
    </aside>

    <div class="main-content">
        <div class="topbar">
            <span class="topbar-title">
                <a href="{{ url_for('admin.dashboard') }}"
                   style="color:#1A5C52;text-decoration:none">
                    <i class="bi bi-chevron-left me-1"></i>Dashboard
                </a>
                &nbsp;/&nbsp; Attempt Detail
            </span>
        </div>

        <div class="page-body">

            <div class="page-header">
                <h4>Attempt Detail</h4>
                <p>Full report for this exam session</p>
            </div>

            <!-- Summary cards -->
            <div class="row g-3 mb-4">
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="stat-icon teal">
                            <i class="bi bi-person"></i>
                        </div>
                        <div class="stat-info">
                            <div class="stat-value"
                                 style="color:#1A5C52;font-size:1rem">
                                {{ attempt.student.name }}
                            </div>
                            <div class="stat-label">
                                {{ attempt.student.roll_number }}
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="stat-icon rust">
                            <i class="bi bi-journal-text"></i>
                        </div>
                        <div class="stat-info">
                            <div class="stat-value"
                                 style="color:#B5451B;font-size:1rem">
                                {{ attempt.exam.title }}
                            </div>
                            <div class="stat-label">
                                {{ attempt.exam.duration }} min
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="stat-icon purple">
                            <i class="bi bi-bar-chart"></i>
                        </div>
                        <div class="stat-info">
                            <div class="stat-value" style="color:#5B3FA0">
                                {{ attempt.score }}
                            </div>
                            <div class="stat-label">MCQ Score</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    {% if attempt.suspicion_score < 10 %}
                        {% set sus = "Low" %}
                        {% set sus_class = "low" %}
                        {% set sus_color = "#1A6B3C" %}
                    {% elif attempt.suspicion_score < 25 %}
                        {% set sus = "Medium" %}
                        {% set sus_class = "medium" %}
                        {% set sus_color = "#856404" %}
                    {% else %}
                        {% set sus = "High" %}
                        {% set sus_class = "high" %}
                        {% set sus_color = "#7B1A1A" %}
                    {% endif %}
                    <div class="stat-card">
                        <div class="stat-icon maroon">
                            <i class="bi bi-shield-exclamation"></i>
                        </div>
                        <div class="stat-info">
                            <div class="stat-value"
                                 style="color:{{ sus_color }}">
                                {{ attempt.suspicion_score }}
                            </div>
                            <div class="stat-label">
                                Suspicion
                                <span class="sus-badge {{ sus_class }} ms-1">
                                    {{ sus }}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Timing -->
            <div class="ep-card mb-4">
                <div class="ep-card-header">
                    <h6>
                        <i class="bi bi-clock-history"></i>
                        Session Timing
                    </h6>
                </div>
                <div class="p-4">
                    <div class="row text-center g-3">
                        <div class="col-md-4">
                            <div style="background:#F4F6F8;padding:1rem;
                                        border-radius:10px">
                                <div class="text-muted"
                                     style="font-size:0.75rem;
                                            font-weight:600;
                                            text-transform:uppercase;
                                            letter-spacing:0.5px;
                                            margin-bottom:0.4rem">
                                    Started
                                </div>
                                <div style="font-weight:600;font-size:0.9rem">
                                    {{ attempt.start_time.strftime('%d %b %Y') }}
                                </div>
                                <div class="text-muted" style="font-size:0.82rem">
                                    {{ attempt.start_time.strftime('%I:%M:%S %p') }}
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div style="background:#F4F6F8;padding:1rem;
                                        border-radius:10px">
                                <div class="text-muted"
                                     style="font-size:0.75rem;
                                            font-weight:600;
                                            text-transform:uppercase;
                                            letter-spacing:0.5px;
                                            margin-bottom:0.4rem">
                                    Submitted
                                </div>
                                <div style="font-weight:600;font-size:0.9rem">
                                    {% if attempt.end_time %}
                                        {{ attempt.end_time.strftime('%d %b %Y') }}
                                    {% else %}—{% endif %}
                                </div>
                                <div class="text-muted" style="font-size:0.82rem">
                                    {% if attempt.end_time %}
                                        {{ attempt.end_time.strftime('%I:%M:%S %p') }}
                                    {% else %}—{% endif %}
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div style="background:#E8F2F0;padding:1rem;
                                        border-radius:10px">
                                <div class="text-muted"
                                     style="font-size:0.75rem;
                                            font-weight:600;
                                            text-transform:uppercase;
                                            letter-spacing:0.5px;
                                            margin-bottom:0.4rem">
                                    Time Taken
                                </div>
                                <div style="font-weight:700;font-size:1.3rem;
                                            color:#1A5C52">
                                    {% if attempt.end_time %}
                                        {{ ((attempt.end_time - attempt.start_time)
                                            .total_seconds() / 60) | int }}
                                        <span style="font-size:0.8rem;
                                                     font-weight:500">min</span>
                                    {% else %}—{% endif %}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Activity logs -->
            <div class="ep-card">
                <div class="ep-card-header">
                    <h6>
                        <i class="bi bi-activity"></i>
                        Activity Logs
                    </h6>
                    <span class="sus-badge medium">
                        {{ logs | length }} event(s)
                    </span>
                </div>
                <div class="table-responsive">
                    <table class="ep-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Event Type</th>
                                <th>Points</th>
                                <th>Timestamp</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for log in logs %}
                            <tr>
                                <td class="text-muted">{{ loop.index }}</td>
                                <td>
                                    {% if log.event_type == "tab_switch" %}
                                        <span class="sus-badge high">
                                            <i class="bi bi-arrow-left-right"></i>
                                            Tab Switch
                                        </span>
                                    {% elif log.event_type == "idle" %}
                                        <span class="sus-badge medium">
                                            <i class="bi bi-pause-circle"></i>
                                            Idle
                                        </span>
                                    {% else %}
                                        <span class="sus-badge low">
                                            <i class="bi bi-lightning-charge"></i>
                                            Fast Submit
                                        </span>
                                    {% endif %}
                                </td>
                                <td>
                                    {% if log.event_type == "tab_switch" %}+5
                                    {% elif log.event_type == "idle" %}+3
                                    {% else %}+15{% endif %}
                                </td>
                                <td class="text-muted">
                                    {{ log.timestamp.strftime('%d %b %Y, %H:%M:%S') }}
                                </td>
                            </tr>
                            {% else %}
                            <tr>
                                <td colspan="4"
                                    class="text-center text-muted py-4">
                                    <i class="bi bi-check-circle me-2"
                                       style="color:#1A6B3C"></i>
                                    No suspicious activity recorded
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

        </div>
    </div>
</div>
{% endblock %}
app/templates/admin/create_exam.html
{% extends "base.html" %}

{% block title %}{{ 'Edit' if exam else 'Create' }} Exam - ExamProctor AI{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-lg-8">
        <div class="d-flex align-items-center mb-4">
            <a href="{{ url_for('admin.exams') }}" class="btn btn-sm btn-outline-light border-secondary me-3">
                <i class="bi bi-arrow-left"></i>
            </a>
            <h2 class="fw-bold text-white mb-0">{{ 'Edit' if exam else 'Create New' }} Exam</h2>
        </div>

        <div class="glass-card p-4 p-md-5">
            <form action="{{ url_for('admin.edit_exam', exam_id=exam.id) if exam else url_for('admin.create_exam') }}" method="POST">
                
                <!-- Basic Info -->
                <div class="mb-4">
                    <label class="form-label text-muted small text-uppercase fw-bold">Exam Title</label>
                    <input type="text" name="title" class="form-control bg-transparent border-secondary-subtle text-white p-3" 
                           placeholder="e.g., Final Term: Computer Architecture" 
                           value="{{ exam.title if exam else '' }}" required>
                </div>

                <div class="row mb-4">
                    <div class="col-md-6">
                        <label class="form-label text-muted small text-uppercase fw-bold">Duration (Minutes)</label>
                        <div class="input-group">
                            <span class="input-group-text bg-transparent border-secondary-subtle text-muted">
                                <i class="bi bi-clock"></i>
                            </span>
                            <input type="number" name="duration" class="form-control bg-transparent border-secondary-subtle text-white p-3" 
                                   placeholder="60" value="{{ exam.duration if exam else '60' }}" required>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label text-muted small text-uppercase fw-bold">Exam Key</label>
                        <div class="input-group">
                            <span class="input-group-text bg-transparent border-secondary-subtle text-muted">
                                <i class="bi bi-key"></i>
                            </span>
                            <input type="text" name="exam_key" class="form-control bg-transparent border-secondary-subtle text-white p-3" 
                                   placeholder="unique-key-123" value="{{ exam.exam_key if exam else '' }}" required>
                        </div>
                        <div class="form-text text-muted">Students use this key to join the exam.</div>
                    </div>
                </div>

                <!-- Status Toggle -->
                <div class="glass-card p-3 mb-5 border-secondary-subtle">
                    <div class="form-check form-switch d-flex justify-content-between align-items-center ps-0">
                        <div>
                            <label class="form-check-label fw-bold text-white" for="isActive">Active Status</label>
                            <p class="text-muted small mb-0">Allow students to attempt this exam immediately.</p>
                        </div>
                        <input class="form-check-input" type="checkbox" name="is_active" id="isActive" 
                               style="width: 3em; height: 1.5em; cursor: pointer;"
                               {{ 'checked' if exam and exam.is_active else '' }}>
                    </div>
                </div>

                <div class="d-flex gap-3">
                    <button type="submit" class="btn-primary-custom flex-grow-1 py-3">
                        <i class="bi bi-save me-2"></i> {{ 'Update Exam Settings' if exam else 'Create Exam' }}
                    </button>
                    <a href="{{ url_for('admin.exams') }}" class="btn btn-outline-light border-secondary py-3 px-4">
                        Cancel
                    </a>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}

admin/dashboard.html
{% extends "base.html" %}
{% block title %}Dashboard — ExamProctor{% endblock %}

{% block body %}
<div class="app-wrapper">

    <!-- Sidebar -->
    <aside class="sidebar">
        <div class="sidebar-brand">
            <div class="brand-name">
                <i class="bi bi-shield-check me-2"></i>ExamProctor
            </div>
            <div class="brand-sub">Admin Panel</div>
        </div>

        <nav class="sidebar-nav">
            <div class="nav-label">Main</div>
            <a href="{{ url_for('admin.dashboard') }}"
               class="nav-link active">
                <i class="bi bi-grid-1x2"></i> Dashboard
            </a>
            <a href="{{ url_for('admin.exams') }}"
               class="nav-link">
                <i class="bi bi-journal-text"></i> Exams
            </a>

            <div class="nav-label mt-2">Students</div>
            <a href="{{ url_for('student.enter_exam') }}"
               class="nav-link">
                <i class="bi bi-person-badge"></i> Student Entry
            </a>
        </nav>

        <div class="sidebar-footer">
            <a href="{{ url_for('auth.logout') }}" class="nav-link">
                <i class="bi bi-box-arrow-left"></i> Logout
            </a>
        </div>
    </aside>

    <!-- Main -->
    <div class="main-content">

        <!-- Topbar -->
        <div class="topbar">
            <div class="d-flex align-items-center gap-3">
                <button id="sidebarToggle" class="sidebar-toggle">
                    <i class="bi bi-list"></i>
                </button>
                <span class="topbar-title">Dashboard</span>
            </div>
        </div>

        <!-- Page body -->
        <div class="page-body">

            <div class="page-header">
                <h4>Overview</h4>
                <p>Monitor exams, students, and suspicious activity</p>
            </div>

            <!-- Stat cards -->
            <div class="row g-3 mb-4">
                <div class="col-sm-6 col-xl-3">
                    <div class="stat-card">
                        <div class="stat-icon teal">
                            <i class="bi bi-journal-text"></i>
                        </div>
                        <div class="stat-info">
                            <div class="stat-value" style="color:#1A5C52">
                                {{ total_exams }}
                            </div>
                            <div class="stat-label">Total Exams</div>
                        </div>
                    </div>
                </div>
                <div class="col-sm-6 col-xl-3">
                    <div class="stat-card">
                        <div class="stat-icon rust">
                            <i class="bi bi-people"></i>
                        </div>
                        <div class="stat-info">
                            <div class="stat-value" style="color:#B5451B">
                                {{ total_students }}
                            </div>
                            <div class="stat-label">Total Students</div>
                        </div>
                    </div>
                </div>
                <div class="col-sm-6 col-xl-3">
                    <div class="stat-card">
                        <div class="stat-icon purple">
                            <i class="bi bi-bar-chart-line"></i>
                        </div>
                        <div class="stat-info">
                            <div class="stat-value" style="color:#5B3FA0">
                                {{ total_attempts }}
                            </div>
                            <div class="stat-label">Total Attempts</div>
                        </div>
                    </div>
                </div>
                <div class="col-sm-6 col-xl-3">
                    <div class="stat-card">
                        <div class="stat-icon maroon">
                            <i class="bi bi-exclamation-triangle"></i>
                        </div>
                        <div class="stat-info">
                            <div class="stat-value" style="color:#7B1A1A">
                                {{ flagged }}
                            </div>
                            <div class="stat-label">Flagged Attempts</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Recent attempts -->
            <div class="ep-card">
                <div class="ep-card-header">
                    <h6>
                        <i class="bi bi-clock-history"></i>
                        Recent Attempts
                    </h6>
                </div>
                <div class="table-responsive">
                    <table class="ep-table">
                        <thead>
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
                                {% set sus = "low" %}
                                {% set sus_label = "Low" %}
                            {% elif a.suspicion_score < 25 %}
                                {% set sus = "medium" %}
                                {% set sus_label = "Medium" %}
                            {% else %}
                                {% set sus = "high" %}
                                {% set sus_label = "High" %}
                            {% endif %}
                            <tr>
                                <td>
                                    <div class="fw-500">{{ a.student.name }}</div>
                                    <div class="text-muted" style="font-size:0.75rem">
                                        {{ a.student.roll_number }}
                                    </div>
                                </td>
                                <td>{{ a.exam.title }}</td>
                                <td class="fw-600">{{ a.score }}</td>
                                <td>
                                    <span class="sus-badge {{ sus }}">
                                        <i class="bi bi-circle-fill"
                                           style="font-size:0.5rem"></i>
                                        {{ sus_label }}
                                    </span>
                                </td>
                                <td class="text-muted">
                                    {{ a.start_time.strftime('%d %b %Y') }}
                                </td>
                                <td>
                                    <a href="{{ url_for('admin.attempt_detail', attempt_id=a.id) }}"
                                       class="btn-ep-secondary">
                                        <i class="bi bi-eye"></i> View
                                    </a>
                                </td>
                            </tr>
                            {% else %}
                            <tr>
                                <td colspan="6"
                                    class="text-center text-muted py-4">
                                    <i class="bi bi-inbox me-2"></i>
                                    No attempts yet
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

        </div>
    </div>
</div>
{% endblock %}

admin/edit_exam.html
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
questions.html
{% extends "base.html" %}
{% block title %}Questions — ExamProctor{% endblock %}

{% block body %}
<div class="app-wrapper">

    <aside class="sidebar">
        <div class="sidebar-brand">
            <div class="brand-name">
                <i class="bi bi-shield-check me-2"></i>ExamProctor
            </div>
            <div class="brand-sub">Admin Panel</div>
        </div>
        <nav class="sidebar-nav">
            <div class="nav-label">Main</div>
            <a href="{{ url_for('admin.dashboard') }}" class="nav-link">
                <i class="bi bi-grid-1x2"></i> Dashboard
            </a>
            <a href="{{ url_for('admin.exams') }}" class="nav-link active">
                <i class="bi bi-journal-text"></i> Exams
            </a>
            <div class="nav-label mt-2">Students</div>
            <a href="{{ url_for('student.enter_exam') }}" class="nav-link">
                <i class="bi bi-person-badge"></i> Student Entry
            </a>
        </nav>
        <div class="sidebar-footer">
            <a href="{{ url_for('auth.logout') }}" class="nav-link">
                <i class="bi bi-box-arrow-left"></i> Logout
            </a>
        </div>
    </aside>

    <div class="main-content">
        <div class="topbar">
            <span class="topbar-title">
                <a href="{{ url_for('admin.exams') }}"
                   style="color:#1A5C52;text-decoration:none">
                    <i class="bi bi-chevron-left me-1"></i>Exams
                </a>
                &nbsp;/&nbsp; {{ exam.title }}
            </span>
            <div class="topbar-right">
                <a href="{{ url_for('admin.add_question', exam_id=exam.id) }}"
                   class="btn-ep-primary">
                    <i class="bi bi-plus-lg"></i> Add Question
                </a>
            </div>
        </div>

        <div class="page-body">
            <div class="page-header">
                <h4>Question Bank</h4>
                <p>
                    {{ exam.title }} &nbsp;·&nbsp;
                    {{ exam.questions | length }} question(s) &nbsp;·&nbsp;
                    {{ exam.duration }} min
                </p>
            </div>

            {% if exam.questions %}
                {% for q in exam.questions %}
                <div class="ep-card mb-3">
                    <div class="ep-card-header">
                        <h6>
                            <i class="bi bi-question-circle"></i>
                            Question {{ loop.index }}
                        </h6>
                        <form method="POST"
                              action="{{ url_for('admin.delete_question', q_id=q.id) }}"
                              onsubmit="return confirm('Delete this question?')">
                            <button class="btn-ep-danger">
                                <i class="bi bi-trash"></i> Delete
                            </button>
                        </form>
                    </div>
                    <div class="p-4">
                        <p class="fw-500 mb-3" style="font-size:0.95rem">
                            {{ q.question_text }}
                        </p>
                        <div class="row g-2">
                            {% for opt, text in [
                                ('A', q.option_a),
                                ('B', q.option_b),
                                ('C', q.option_c),
                                ('D', q.option_d)
                            ] %}
                            <div class="col-md-6">
                                <div class="d-flex align-items-center gap-2 p-2 rounded"
                                     style="background:{{ '#E8F2F0' if opt == q.correct_answer else '#F4F6F8' }};
                                            border:1.5px solid {{ '#1A5C52' if opt == q.correct_answer else '#E2E8F0' }}">
                                    <span style="width:24px;height:24px;border-radius:50%;
                                                 background:{{ '#1A5C52' if opt == q.correct_answer else '#E2E8F0' }};
                                                 color:{{ 'white' if opt == q.correct_answer else '#555' }};
                                                 display:flex;align-items:center;justify-content:center;
                                                 font-size:0.75rem;font-weight:700;flex-shrink:0">
                                        {{ opt }}
                                    </span>
                                    <span style="font-size:0.875rem;
                                                 color:{{ '#1A5C52' if opt == q.correct_answer else '#3D3D3D' }};
                                                 font-weight:{{ '600' if opt == q.correct_answer else '400' }}">
                                        {{ text }}
                                        {% if opt == q.correct_answer %}
                                        <i class="bi bi-check-circle-fill ms-1"
                                           style="color:#1A5C52;font-size:0.8rem"></i>
                                        {% endif %}
                                    </span>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <div class="ep-card">
                    <div class="p-5 text-center text-muted">
                        <i class="bi bi-inbox d-block mb-2"
                           style="font-size:2.5rem;color:#C5D5D2"></i>
                        <p class="mb-3">No questions added yet.</p>
                        <a href="{{ url_for('admin.add_question', exam_id=exam.id) }}"
                           class="btn-ep-primary">
                            <i class="bi bi-plus-lg"></i> Add First Question
                        </a>
                    </div>
                </div>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}

exams.html
{% extends "base.html" %}
{% block title %}Exams — ExamProctor{% endblock %}

{% block body %}
<div class="app-wrapper">

    <aside class="sidebar">
        <div class="sidebar-brand">
            <div class="brand-name">
                <i class="bi bi-shield-check me-2"></i>ExamProctor
            </div>
            <div class="brand-sub">Admin Panel</div>
        </div>
        <nav class="sidebar-nav">
            <div class="nav-label">Main</div>
            <a href="{{ url_for('admin.dashboard') }}" class="nav-link">
                <i class="bi bi-grid-1x2"></i> Dashboard
            </a>
            <a href="{{ url_for('admin.exams') }}" class="nav-link active">
                <i class="bi bi-journal-text"></i> Exams
            </a>
            <div class="nav-label mt-2">Students</div>
            <a href="{{ url_for('student.enter_exam') }}" class="nav-link">
                <i class="bi bi-person-badge"></i> Student Entry
            </a>
        </nav>
        <div class="sidebar-footer">
            <a href="{{ url_for('auth.logout') }}" class="nav-link">
                <i class="bi bi-box-arrow-left"></i> Logout
            </a>
        </div>
    </aside>

    <div class="main-content">
        <div class="topbar">
            <span class="topbar-title">Exams</span>
            <div class="topbar-right">
                <a href="{{ url_for('admin.create_exam') }}"
                   class="btn-ep-primary">
                    <i class="bi bi-plus-lg"></i> Create Exam
                </a>
            </div>
        </div>

        <div class="page-body">
            <div class="page-header">
                <h4>All Exams</h4>
                <p>Create and manage your examination schedule</p>
            </div>

            <div class="ep-card">
                <div class="table-responsive">
                    <table class="ep-table">
                        <thead>
                            <tr>
                                <th>Title</th>
                                <th>Duration</th>
                                <th>Scheduled</th>
                                <th>Questions</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for e in exams %}
                            <tr>
                                <td class="fw-600">{{ e.title }}</td>
                                <td>
                                    <i class="bi bi-clock text-muted me-1"></i>
                                    {{ e.duration }} min
                                </td>
                                <td class="text-muted">
                                    {{ e.scheduled_at.strftime('%d %b %Y, %I:%M %p')
                                       if e.scheduled_at else '—' }}
                                </td>
                                <td>
                                    <span class="sus-badge low">
                                        {{ e.questions | length }} Qs
                                    </span>
                                </td>
                                <td>
                                    <span class="status-badge {{ e.status }}">
                                        {{ e.status | capitalize }}
                                    </span>
                                </td>
                                <td>
                                    <div class="d-flex gap-2">
                                        <a href="{{ url_for('admin.questions', exam_id=e.id) }}"
                                           class="btn-ep-secondary">
                                            <i class="bi bi-list-ul"></i>
                                        </a>
                                        <a href="{{ url_for('admin.edit_exam', exam_id=e.id) }}"
                                           class="btn-ep-secondary">
                                            <i class="bi bi-pencil"></i>
                                        </a>
                                        <form method="POST"
                                              action="{{ url_for('admin.delete_exam', exam_id=e.id) }}"
                                              class="d-inline"
                                              onsubmit="return confirm('Delete this exam?')">
                                            <button class="btn-ep-danger">
                                                <i class="bi bi-trash"></i>
                                            </button>
                                        </form>
                                    </div>
                                </td>
                            </tr>
                            {% else %}
                            <tr>
                                <td colspan="6"
                                    class="text-center text-muted py-5">
                                    <i class="bi bi-journal-x d-block mb-2"
                                       style="font-size:2rem"></i>
                                    No exams yet. Create your first exam.
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

templates/auth
login.html
{% extends "base.html" %}
{% block title %}Login — ExamProctor{% endblock %}

{% block body %}
<div class="login-page">
    <div class="login-card">

        <!-- Logo -->
        <div class="login-logo">
            <i class="bi bi-shield-check"></i>
        </div>

        <h4>ExamProctor</h4>
        <p>Sign in to your admin account</p>

        <form method="POST" autocomplete="off">

            <div class="mb-3">
                <label class="form-label">Username</label>
                <div class="input-icon-wrap">
                    <i class="bi bi-person"></i>
                    <input type="text" name="username" class="form-control"
                           placeholder="Enter your username" required autofocus>
                </div>
            </div>

            <div class="mb-3">
                <label class="form-label">Password</label>
                <div class="input-icon-wrap">
                    <i class="bi bi-lock"></i>
                    <input type="password" name="password" class="form-control"
                           placeholder="Enter your password" required>
                </div>
            </div>

            <button type="submit" class="btn-login">
                <i class="bi bi-box-arrow-in-right"></i>
                Sign In
            </button>

        </form>

        <p style="color:rgba(255,255,255,0.3);text-align:center;
                  font-size:0.75rem;margin-top:1.5rem;margin-bottom:0">
            Islamia College of Science and Commerce
        </p>
        <p style="color:rgba(255,255,255,0.3);text-align:center;
          font-size:0.75rem;margin-top:0.8rem;margin-bottom:0">
            Need an account?
        <a href="{{ url_for('auth.register') }}"
            style="color:rgba(255,255,255,0.6)">Register</a>
        </p>

    </div>
</div>
{% endblock %}

register.html
{% extends "base.html" %}
{% block title %}Register Admin — ExamProctor{% endblock %}

{% block body %}
<div class="login-page">
    <div class="login-card">

        <div class="login-logo">
            <i class="bi bi-person-plus"></i>
        </div>

        <h4>Create Admin Account</h4>
        <p>You need a registration code to proceed</p>

        <form method="POST" autocomplete="off">

            <div class="mb-3">
                <label class="form-label">Username</label>
                <div class="input-icon-wrap">
                    <i class="bi bi-person"></i>
                    <input type="text" name="username"
                           class="form-control"
                           placeholder="Choose a username" required>
                </div>
            </div>

            <div class="mb-3">
                <label class="form-label">Password</label>
                <div class="input-icon-wrap">
                    <i class="bi bi-lock"></i>
                    <input type="password" name="password"
                           class="form-control"
                           placeholder="Min 6 characters" required>
                </div>
            </div>

            <div class="mb-3">
                <label class="form-label">Registration Code</label>
                <div class="input-icon-wrap">
                    <i class="bi bi-key"></i>
                    <input type="password" name="secret_code"
                           class="form-control"
                           placeholder="Enter secret code" required>
                </div>
            </div>

            <button type="submit" class="btn-login">
                <i class="bi bi-person-check"></i>
                Create Account
            </button>

        </form>

        <p style="color:rgba(255,255,255,0.4);text-align:center;
                  font-size:0.78rem;margin-top:1.2rem;margin-bottom:0">
            Already have an account?
            <a href="{{ url_for('auth.login') }}"
               style="color:rgba(255,255,255,0.7)">Sign in</a>
        </p>

    </div>
</div>
{% endblock %}

templates/student
detail.html
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
enter.html
{% extends "base.html" %}
{% block title %}Enter Exam — ExamProctor{% endblock %}

{% block body %}
<div class="student-page">
    <div class="student-card">

        <div class="student-card-header">
            <div class="d-flex align-items-center gap-3">
                <div style="width:44px;height:44px;background:rgba(255,255,255,0.15);
                            border-radius:10px;display:flex;align-items:center;
                            justify-content:center;font-size:1.3rem;color:white">
                    <i class="bi bi-pencil-square"></i>
                </div>
                <div>
                    <h5 class="mb-0">Enter Exam</h5>
                    <p class="mb-0">Fill in your details to begin</p>
                </div>
            </div>
        </div>

        <div class="student-card-body">
            <form method="POST">

                <div class="mb-3">
                    <label class="form-label">
                        <i class="bi bi-person me-1" style="color:#1A5C52"></i>
                        Full Name
                    </label>
                    <input type="text" name="name" class="form-control"
                           placeholder="Enter your full name" required>
                </div>

                <div class="mb-3">
                    <label class="form-label">
                        <i class="bi bi-credit-card me-1"
                           style="color:#1A5C52"></i>
                        Roll Number
                    </label>
                    <input type="text" name="roll_number" class="form-control"
                           placeholder="e.g. BCA2024001" required>
                </div>

                <div class="mb-4">
                    <label class="form-label">
                        <i class="bi bi-journal-text me-1"
                           style="color:#1A5C52"></i>
                        Select Exam
                    </label>
                    <select name="exam_id" class="form-select" required>
                        <option value="">— Choose an exam —</option>
                        {% for exam in exams %}
                        <option value="{{ exam.id }}">
                            {{ exam.title }} &nbsp;·&nbsp; {{ exam.duration }} min
                        </option>
                        {% endfor %}
                    </select>
                </div>

                <button type="submit" class="btn-ep-primary w-100 justify-content-center py-2">
                    <i class="bi bi-arrow-right-circle"></i>
                    Start Exam
                </button>

            </form>
        </div>

    </div>
</div>
{% endblock %}
exam.html
{% extends "base.html" %}
{% block title %}{{ exam.title }} — ExamProctor{% endblock %}

{% block body %}

<div id="proctor-data"
     data-attempt-id="{{ attempt.id }}"
     data-duration="{{ exam.duration }}"
     style="display:none">
</div>

<!-- Exam topbar -->
<div class="exam-topbar">
    <div>
        <div class="exam-title">{{ exam.title }}</div>
        <div class="text-muted" style="font-size:0.75rem">
            <i class="bi bi-question-circle me-1"></i>
            {{ questions | length }} questions
        </div>
    </div>

    <div class="timer-box">
        <div class="timer-label">Time Remaining</div>
        <div id="timer-display">--:--</div>
    </div>

    <button type="submit" form="exam-form" class="btn-ep-rust">
        <i class="bi bi-send-check"></i>
        Submit Exam
    </button>
</div>

<!-- Questions -->
<div class="container py-4" style="max-width:760px">
    <form id="exam-form" method="POST"
          action="{{ url_for('student.submit_exam', attempt_id=attempt.id) }}">

        {% for q in questions %}
        <div class="question-card">
            <div class="question-num">Question {{ loop.index }}</div>
            <div class="question-text">{{ q.question_text }}</div>

            {% for opt, text in [('A', q.option_a), ('B', q.option_b),
                                 ('C', q.option_c), ('D', q.option_d)] %}
            <div class="option-item">
                <input type="radio"
                       name="q_{{ q.id }}"
                       id="q{{ q.id }}_{{ opt }}"
                       value="{{ opt }}">
                <label class="option-label" for="q{{ q.id }}_{{ opt }}">
                    <span class="option-letter">{{ opt }}</span>
                    {{ text }}
                </label>
            </div>
            {% endfor %}
        </div>
        {% endfor %}

        <div class="text-end mt-3 mb-5">
            <button type="submit" class="btn-ep-rust">
                <i class="bi bi-send-check"></i>
                Submit Exam
            </button>
        </div>

    </form>
</div>
{% endblock %}

{% block scripts %}
<script src="{{ url_for('static', filename='js/proctor.js') }}"></script>
{% endblock %}

result.html
{% extends "base.html" %}
{% block title %}Result — ExamProctor{% endblock %}

{% block body %}
<div class="result-page">
    <div class="result-card">

        <div class="result-header">
            {% if attempt.suspicion_score >= 25 %}
                <div class="result-icon danger">
                    <i class="bi bi-exclamation-triangle-fill"></i>
                </div>
            {% elif attempt.suspicion_score >= 10 %}
                <div class="result-icon warning">
                    <i class="bi bi-exclamation-circle-fill"></i>
                </div>
            {% else %}
                <div class="result-icon success">
                    <i class="bi bi-check-circle-fill"></i>
                </div>
            {% endif %}

            <h5 style="font-weight:700;margin-bottom:0.2rem">
                Exam Submitted
            </h5>
            <p class="text-muted" style="font-size:0.85rem;margin:0">
                {{ attempt.exam.title }}
            </p>
        </div>

        <div class="p-4">
            <div class="row g-3 mb-3">
                <div class="col-6">
                    <div class="score-box" style="background:#E8F2F0">
                        <div class="score-value" style="color:#1A5C52">
                            {{ attempt.score }}/{{ total }}
                        </div>
                        <div class="score-label" style="color:#1A5C52">
                            Your Score
                        </div>
                    </div>
                </div>
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
                    <div class="score-box"
                         style="background:{{ sus_bg }}">
                        <div class="score-value"
                             style="color:{{ sus_color }}">
                            {{ sus }}
                        </div>
                        <div class="score-label"
                             style="color:{{ sus_color }}">
                            Suspicion
                        </div>
                    </div>
                </div>
            </div>

            <div class="text-center text-muted mb-4"
                 style="font-size:0.82rem">
                <i class="bi bi-clock me-1"></i>
                Time taken:
                {% if attempt.end_time %}
                    {{ ((attempt.end_time - attempt.start_time)
                        .total_seconds() / 60) | int }} minutes
                {% else %}—{% endif %}
            </div>

            <a href="{{ url_for('student.enter_exam') }}"
               class="btn-ep-primary w-100 justify-content-center py-2">
                <i class="bi bi-arrow-left-circle"></i>
                Back to Exam Entry
            </a>
        </div>

    </div>
</div>
{% endblock %}

templates/base.html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}ExamProctor{% endblock %}</title>

    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Bootstrap Icons -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <!-- Custom CSS -->
    <link href="{{ url_for('static', filename='css/style.css') }}" rel="stylesheet">

    {% block head %}{% endblock %}
</head>
<body>

<!-- Flash messages -->
{% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
        <div class="toast-container position-fixed top-0 end-0 p-3"
             style="z-index:9999">
            {% for category, message in messages %}
                <div class="toast align-items-center border-0 show mb-2
                            {% if category == 'success' %}bg-success text-white
                            {% elif category == 'danger' %}bg-danger text-white
                            {% elif category == 'warning' %}bg-warning text-dark
                            {% else %}bg-info text-white{% endif %}"
                     role="alert">
                    <div class="d-flex">
                        <div class="toast-body fw-500">
                            {% if category == 'success' %}
                                <i class="bi bi-check-circle-fill me-2"></i>
                            {% elif category == 'danger' %}
                                <i class="bi bi-x-circle-fill me-2"></i>
                            {% elif category == 'warning' %}
                                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                            {% else %}
                                <i class="bi bi-info-circle-fill me-2"></i>
                            {% endif %}
                            {{ message }}
                        </div>
                        <button type="button"
                                class="btn-close btn-close-white me-2 m-auto"
                                data-bs-dismiss="toast">
                        </button>
                    </div>
                </div>
            {% endfor %}
        </div>
    {% endif %}
{% endwith %}

{% block body %}{% endblock %}

<!-- Bootstrap JS -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

<!-- Auto dismiss toasts -->
<script>
    document.querySelectorAll('.toast').forEach(function(toast) {
        setTimeout(function() {
            toast.classList.remove('show');
        }, 4000);
    });
</script>
<script>
    // Mobile sidebar toggle
    const toggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    if (toggle && sidebar) {
        toggle.addEventListener('click', function() {
            sidebar.classList.toggle('open');
        });
        document.addEventListener('click', function(e) {
            if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
                sidebar.classList.remove('open');
            }
        });
    }
    </script>

{% block scripts %}{% endblock %}
</body>
</html>

app/config.py
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "dev-secret-key"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "..", "exam_proctor.db")
