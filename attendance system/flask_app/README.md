# Smart Classroom Attendance System

Flask + SQLite + face_recognition. Dark-themed responsive UI.

## Quick start

```bash
cd flask_app
pip install -r requirements.txt
python app.py
```

Then open <http://localhost:5000>.

## Project layout

```
flask_app/
├── app.py                # Flask routes & glue
├── database.py           # SQLAlchemy models
├── face_engine.py        # All face_recognition / OpenCV logic
├── templates/            # Jinja2 templates
│   ├── base.html
│   ├── index.html        # Dashboard
│   ├── enroll.html
│   ├── students.html
│   ├── attendance.html   # Upload + recognition + results
│   ├── history.html
│   └── dashboard.html    # Analytics
├── static/
│   ├── css/style.css
│   └── js/main.js
├── uploads/              # Classroom photos (created on first run)
└── students/             # Enrolled-student photos (created on first run)
```

## Features

- **Take attendance** — drag & drop 1–3 classroom photos. The AI detects faces,
  matches them against enrolled students, draws green boxes with confidence,
  and stores a session.
- **Enrollment** — add students with photo + auto face-encoding.
- **Classes** — create separate classes (default: AI Lab). Each has its own
  roster and attendance history.
- **History** — date-wise records, filterable by date and student name.
- **Analytics** — bar chart of per-student attendance %, line chart of class
  attendance trend, low-attendance alerts (<75%) highlighted in red.
- **CSV export** — download any session as `Name, Roll, Status, Date, Time, Class`.

## Notes on the AI

- `face_engine.py` is the only file that touches `face_recognition` / OpenCV.
- Tolerance is `0.50` (in `face_engine.py`) — lower is stricter.
- If `face_recognition` / `opencv-python` are not installed, the engine falls
  back to a deterministic mock so the UI still runs end-to-end for demos.

## Common gotchas

- `face_recognition` requires `dlib`. On Linux you may need
  `cmake` + `build-essential` + `libboost-all-dev` first.
- On macOS: `brew install cmake` then `pip install dlib face_recognition`.
- Enrollment photos should be clear, front-facing. If no face is detected the
  upload is rejected.
