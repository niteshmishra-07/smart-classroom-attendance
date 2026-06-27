"""
Smart Classroom Attendance System
Main Flask application
"""
import os
import io
import csv
import base64
from datetime import datetime, date, timedelta
from flask import (
    Flask, render_template, request, redirect, url_for,
    jsonify, send_file, flash, abort
)
from werkzeug.utils import secure_filename

from database import db, Student, ClassRoom, AttendanceSession, AttendanceRecord
from face_engine import FaceEngine

# ---------- App Configuration ----------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
STUDENTS_FOLDER = os.path.join(BASE_DIR, "students")
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STUDENTS_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-me-in-production"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'attendance.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024   # 16MB max upload
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["STUDENTS_FOLDER"] = STUDENTS_FOLDER

db.init_app(app)
face_engine = FaceEngine(students_folder=STUDENTS_FOLDER)

LOW_ATTENDANCE_THRESHOLD = 75.0   # percent


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


# ---------- Bootstrap ----------
@app.before_request
def _ensure_db():
    if not getattr(app, "_db_ready", False):
        with app.app_context():
            db.create_all()
            # seed a default class if none exist
            if ClassRoom.query.count() == 0:
                db.session.add(ClassRoom(name="AI Lab", description="Default class"))
                db.session.commit()
            face_engine.load_known_faces(Student.query.all())
        app._db_ready = True


# ---------- Helpers ----------
def current_class_id():
    cid = request.args.get("class_id", type=int)
    if cid:
        return cid
    first = ClassRoom.query.order_by(ClassRoom.id).first()
    return first.id if first else None


def attendance_stats_for_class(class_id: int):
    """Return list of dicts: student, present_count, total_sessions, percent."""
    students = Student.query.filter_by(class_id=class_id).all()
    sessions = AttendanceSession.query.filter_by(class_id=class_id).all()
    total = len(sessions)
    rows = []
    for s in students:
        present = AttendanceRecord.query.join(AttendanceSession).filter(
            AttendanceRecord.student_id == s.id,
            AttendanceRecord.status == "Present",
            AttendanceSession.class_id == class_id,
        ).count()
        pct = (present / total * 100.0) if total else 0.0
        rows.append({
            "student": s,
            "present": present,
            "total": total,
            "percent": round(pct, 1),
            "low": pct < LOW_ATTENDANCE_THRESHOLD and total > 0,
        })
    return rows, total


# ---------- Routes: pages ----------
@app.route("/")
def index():
    classes = ClassRoom.query.order_by(ClassRoom.name).all()
    cid = current_class_id()
    student_count = Student.query.filter_by(class_id=cid).count() if cid else 0
    session_count = AttendanceSession.query.filter_by(class_id=cid).count() if cid else 0
    recent = (AttendanceSession.query
              .filter_by(class_id=cid)
              .order_by(AttendanceSession.created_at.desc())
              .limit(5).all()) if cid else []
    rows, _ = attendance_stats_for_class(cid) if cid else ([], 0)
    low_count = sum(1 for r in rows if r["low"])
    return render_template(
        "index.html",
        classes=classes,
        current_class_id=cid,
        student_count=student_count,
        session_count=session_count,
        low_count=low_count,
        recent_sessions=recent,
    )


@app.route("/enroll", methods=["GET", "POST"])
def enroll():
    classes = ClassRoom.query.order_by(ClassRoom.name).all()
    cid = current_class_id()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        roll = request.form.get("roll", "").strip()
        class_id = request.form.get("class_id", type=int) or cid
        photos = request.files.getlist("photo")
        photo = photos[0] if photos else None

        if not name or not photo or not class_id:
            flash("Name, class and photo are required.", "error")
            return redirect(url_for("enroll", class_id=class_id))

        if not allowed_file(photo.filename):
            flash("Unsupported file type.", "error")
            return redirect(url_for("enroll", class_id=class_id))

        # Save main photo
        ext = photo.filename.rsplit(".", 1)[1].lower()
        safe = secure_filename(name).lower().replace(" ", "_")
        filename = f"{safe}_{int(datetime.utcnow().timestamp())}.{ext}"
        filepath = os.path.join(STUDENTS_FOLDER, filename)
        photo.save(filepath)

        # Save extra angle photos
        extra_paths = []
        for i, extra_photo in enumerate(photos[1:], 1):
            if extra_photo and allowed_file(extra_photo.filename):
                ext2 = extra_photo.filename.rsplit(".", 1)[1].lower()
                extra_fn = f"{safe}_{int(datetime.utcnow().timestamp())}_{i}.{ext2}"
                extra_path = os.path.join(STUDENTS_FOLDER, extra_fn)
                extra_photo.save(extra_path)
                extra_paths.append(extra_path)

        # Compute face encoding — multi-angle!
        all_paths = [filepath] + extra_paths
        encoding = face_engine.encode_face(all_paths)
        if encoding is None:
            os.remove(filepath)
            flash("No face detected in photo. Please use a clearer image.", "error")
            return redirect(url_for("enroll", class_id=class_id))

        student = Student(
            name=name,
            roll_number=roll or None,
            photo_filename=filename,
            class_id=class_id,
            encoding=Student.encode_array(encoding),
        )
        db.session.add(student)
        db.session.commit()
        face_engine.add_student(student)
        flash(f"Enrolled {name}.", "success")
        return redirect(url_for("students", class_id=class_id))

    return render_template("enroll.html", classes=classes, current_class_id=cid)


@app.route("/students")
def students():
    classes = ClassRoom.query.order_by(ClassRoom.name).all()
    cid = current_class_id()
    rows, total_sessions = attendance_stats_for_class(cid) if cid else ([], 0)
    return render_template(
        "students.html",
        classes=classes,
        current_class_id=cid,
        rows=rows,
        total_sessions=total_sessions,
    )


@app.route("/students/<int:student_id>/delete", methods=["POST"])
def delete_student(student_id):
    s = Student.query.get_or_404(student_id)
    cid = s.class_id
    # remove photo
    p = os.path.join(STUDENTS_FOLDER, s.photo_filename)
    if os.path.exists(p):
        try:
            os.remove(p)
        except OSError:
            pass
    db.session.delete(s)
    db.session.commit()
    face_engine.load_known_faces(Student.query.all())
    flash("Student removed.", "success")
    return redirect(url_for("students", class_id=cid))


@app.route("/attendance", methods=["GET"])
def attendance():
    classes = ClassRoom.query.order_by(ClassRoom.name).all()
    cid = current_class_id()
    return render_template(
        "attendance.html",
        classes=classes,
        current_class_id=cid,
    )


@app.route("/attendance/process", methods=["POST"])
def attendance_process():
    """Receive 1-3 photos, run face recognition, persist session + records."""
    class_id = request.form.get("class_id", type=int)
    if not class_id:
        return jsonify({"error": "class_id required"}), 400
    klass = ClassRoom.query.get_or_404(class_id)

    files = request.files.getlist("photos")
    files = [f for f in files if f and f.filename]
    if not files:
        return jsonify({"error": "No photos uploaded."}), 400
    if len(files) > 3:
        return jsonify({"error": "Maximum 3 photos per session."}), 400

    saved_paths = []
    for f in files:
        if not allowed_file(f.filename):
            return jsonify({"error": f"Unsupported file: {f.filename}"}), 400
        fn = secure_filename(f.filename)
        path = os.path.join(UPLOAD_FOLDER, f"{int(datetime.utcnow().timestamp()*1000)}_{fn}")
        f.save(path)
        saved_paths.append(path)

    # roster for this class
    roster = Student.query.filter_by(class_id=class_id).all()
    if not roster:
        return jsonify({"error": "No students enrolled in this class."}), 400
    face_engine.load_known_faces(roster)

    # Process each photo
    photo_results = []
    matched_student_ids = set()
    for path in saved_paths:
        result = face_engine.recognize_in_image(path)
        if result is None:
            photo_results.append({
                "filename": os.path.basename(path),
                "annotated": None,
                "faces": [],
                "error": "Could not read image."
            })
            continue
        for face in result["faces"]:
            if face["student_id"] is not None:
                matched_student_ids.add(face["student_id"])
        photo_results.append({
            "filename": os.path.basename(path),
            "annotated": result["annotated_b64"],
            "faces": result["faces"],
            "error": None,
        })

    # Persist session + records
    session = AttendanceSession(class_id=class_id)
    db.session.add(session)
    db.session.flush()
    present_list, absent_list = [], []
    for st in roster:
        status = "Present" if st.id in matched_student_ids else "Absent"
        rec = AttendanceRecord(
            session_id=session.id,
            student_id=st.id,
            status=status,
        )
        db.session.add(rec)
        info = {"id": st.id, "name": st.name, "roll": st.roll_number, "photo": st.photo_filename}
        (present_list if status == "Present" else absent_list).append(info)
    db.session.commit()

    return jsonify({
        "session_id": session.id,
        "class_name": klass.name,
        "date": session.created_at.strftime("%Y-%m-%d"),
        "time": session.created_at.strftime("%H:%M:%S"),
        "photos": photo_results,
        "present": present_list,
        "absent": absent_list,
        "total": len(roster),
    })


@app.route("/attendance/<int:session_id>/csv")
def attendance_csv(session_id):
    s = AttendanceSession.query.get_or_404(session_id)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Name", "Roll", "Status", "Date", "Time", "Class"])
    for rec in s.records:
        writer.writerow([
            rec.student.name,
            rec.student.roll_number or "",
            rec.status,
            s.created_at.strftime("%Y-%m-%d"),
            s.created_at.strftime("%H:%M:%S"),
            s.classroom.name,
        ])
    mem = io.BytesIO(buf.getvalue().encode("utf-8"))
    fname = f"attendance_{s.classroom.name}_{s.created_at.strftime('%Y%m%d_%H%M')}.csv"
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name=fname)


@app.route("/history")
def history():
    classes = ClassRoom.query.order_by(ClassRoom.name).all()
    cid = current_class_id()

    q_date = request.args.get("date")
    q_name = request.args.get("name", "").strip()

    sessions = AttendanceSession.query.filter_by(class_id=cid) if cid else AttendanceSession.query
    if q_date:
        try:
            d = datetime.strptime(q_date, "%Y-%m-%d").date()
            start = datetime.combine(d, datetime.min.time())
            end = datetime.combine(d, datetime.max.time())
            sessions = sessions.filter(AttendanceSession.created_at.between(start, end))
        except ValueError:
            pass

    sessions = sessions.order_by(AttendanceSession.created_at.desc()).all()

    # Optionally narrow by student name (filter records inside each session)
    history_rows = []
    for s in sessions:
        records = s.records
        if q_name:
            records = [r for r in records if q_name.lower() in r.student.name.lower()]
            if not records:
                continue
        present = sum(1 for r in records if r.status == "Present")
        total = len(records)
        history_rows.append({
            "session": s,
            "records": records,
            "present": present,
            "total": total,
        })

    return render_template(
        "history.html",
        classes=classes,
        current_class_id=cid,
        rows=history_rows,
        q_date=q_date or "",
        q_name=q_name,
    )


@app.route("/dashboard")
def dashboard():
    classes = ClassRoom.query.order_by(ClassRoom.name).all()
    cid = current_class_id()
    rows, total_sessions = attendance_stats_for_class(cid) if cid else ([], 0)

    # Trend over last 14 sessions
    sessions = (AttendanceSession.query
                .filter_by(class_id=cid)
                .order_by(AttendanceSession.created_at.asc())
                .all()) if cid else []
    trend_labels, trend_values = [], []
    for s in sessions[-14:]:
        present = sum(1 for r in s.records if r.status == "Present")
        total = len(s.records) or 1
        trend_labels.append(s.created_at.strftime("%m/%d %H:%M"))
        trend_values.append(round(present / total * 100, 1))

    bar_labels = [r["student"].name for r in rows]
    bar_values = [r["percent"] for r in rows]
    low_students = [r for r in rows if r["low"]]

    return render_template(
        "dashboard.html",
        classes=classes,
        current_class_id=cid,
        rows=rows,
        total_sessions=total_sessions,
        bar_labels=bar_labels,
        bar_values=bar_values,
        trend_labels=trend_labels,
        trend_values=trend_values,
        low_students=low_students,
        threshold=LOW_ATTENDANCE_THRESHOLD,
    )


# ---------- Routes: class management ----------
@app.route("/classes/new", methods=["POST"])
def class_new():
    name = request.form.get("name", "").strip()
    desc = request.form.get("description", "").strip()
    if not name:
        flash("Class name required.", "error")
        return redirect(request.referrer or url_for("index"))
    if ClassRoom.query.filter_by(name=name).first():
        flash("A class with that name already exists.", "error")
        return redirect(request.referrer or url_for("index"))
    c = ClassRoom(name=name, description=desc)
    db.session.add(c)
    db.session.commit()
    flash(f"Class '{name}' created.", "success")
    return redirect(url_for("index", class_id=c.id))


@app.route("/classes/<int:class_id>/delete", methods=["POST"])
def class_delete(class_id):
    c = ClassRoom.query.get_or_404(class_id)
    db.session.delete(c)
    db.session.commit()
    flash(f"Class '{c.name}' deleted.", "success")
    return redirect(url_for("index"))


# ---------- Static-ish file serving ----------
@app.route("/photo/<path:filename>")
def serve_student_photo(filename):
    path = os.path.join(STUDENTS_FOLDER, filename)
    if not os.path.exists(path):
        abort(404)
    return send_file(path)


# ---------- Errors ----------
@app.errorhandler(413)
def too_large(_):
    return jsonify({"error": "Upload too large (max 16MB)."}), 413


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if ClassRoom.query.count() == 0:
            db.session.add(ClassRoom(name="AI Lab", description="Default class"))
            db.session.commit()
        face_engine.load_known_faces(Student.query.all())
    app.run(host="0.0.0.0", port=5000, debug=True)