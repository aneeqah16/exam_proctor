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