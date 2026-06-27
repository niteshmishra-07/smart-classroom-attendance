"""
SQLAlchemy models for the attendance system.
"""
from datetime import datetime
import json
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class ClassRoom(db.Model):
    __tablename__ = "classrooms"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    students = db.relationship(
        "Student", backref="classroom",
        cascade="all, delete-orphan", lazy=True
    )
    sessions = db.relationship(
        "AttendanceSession", backref="classroom",
        cascade="all, delete-orphan", lazy=True
    )

    def __repr__(self):
        return f"<ClassRoom {self.name}>"


class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    roll_number = db.Column(db.String(40), nullable=True)
    photo_filename = db.Column(db.String(255), nullable=False)
    encoding = db.Column(db.Text, nullable=True)  # JSON-serialised 128-d vector
    class_id = db.Column(db.Integer, db.ForeignKey("classrooms.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    records = db.relationship(
        "AttendanceRecord", backref="student",
        cascade="all, delete-orphan", lazy=True
    )

    @staticmethod
    def encode_array(arr):
        """Serialize a numpy array (or list) of floats to JSON text."""
        if arr is None:
            return None
        if hasattr(arr, "tolist"):
            arr = arr.tolist()
        return json.dumps(arr)

    @staticmethod
    def decode_array(text):
        if not text:
            return None
        return json.loads(text)

    def __repr__(self):
        return f"<Student {self.name}>"


class AttendanceSession(db.Model):
    """A single 'class taken' event - one or more photos."""
    __tablename__ = "attendance_sessions"
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classrooms.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.String(255), default="")

    records = db.relationship(
        "AttendanceRecord", backref="session",
        cascade="all, delete-orphan", lazy=True
    )


class AttendanceRecord(db.Model):
    __tablename__ = "attendance_records"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("attendance_sessions.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    status = db.Column(db.String(16), nullable=False, default="Absent")  # Present|Absent
    confidence = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
