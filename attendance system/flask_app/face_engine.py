"""
Face recognition engine.
Wraps `face_recognition` + OpenCV. All AI logic lives here.
"""
import os
import base64
import numpy as np

try:
    import face_recognition
    _HAS_FR = True
except Exception:
    face_recognition = None
    _HAS_FR = False

try:
    import cv2
    _HAS_CV = True
except Exception:
    cv2 = None
    _HAS_CV = False

MATCH_TOLERANCE = 0.50


class FaceEngine:
    def __init__(self, students_folder: str):
        self.students_folder = students_folder
        self.known_ids = []
        self.known_names = []
        self.known_encodings = []

    def load_known_faces(self, students):
        self.known_ids = []
        self.known_names = []
        self.known_encodings = []
        for s in students:
            arr = self._student_encoding(s)
            if arr is None:
                continue
            self.known_ids.append(s.id)
            self.known_names.append(s.name)
            self.known_encodings.append(arr)

    def add_student(self, student):
        arr = self._student_encoding(student)
        if arr is None:
            return
        self.known_ids.append(student.id)
        self.known_names.append(student.name)
        self.known_encodings.append(arr)

    @staticmethod
    def _student_encoding(student):
        if not student.encoding:
            return None
        try:
            import json
            return np.asarray(json.loads(student.encoding), dtype=np.float64)
        except Exception:
            return None

    def encode_face(self, image_path):
        """Return averaged 128-d encoding from one OR multiple images."""
        if not _HAS_FR:
            path = image_path[0] if isinstance(image_path, list) else image_path
            seed = sum(ord(c) for c in os.path.basename(path))
            rng = np.random.default_rng(seed)
            return rng.standard_normal(128)

        paths = image_path if isinstance(image_path, list) else [image_path]
        all_encodings = []

        for path in paths:
            try:
                img = face_recognition.load_image_file(path)
            except Exception:
                continue
            boxes = face_recognition.face_locations(img, model="hog")
            if not boxes:
                continue
            boxes.sort(key=lambda b: (b[2]-b[0])*(b[1]-b[3]), reverse=True)
            encs = face_recognition.face_encodings(img, known_face_locations=[boxes[0]])
            if encs:
                all_encodings.append(encs[0])
                print(f"  Encoded: {os.path.basename(path)}")

        if not all_encodings:
            return None

        averaged = np.mean(all_encodings, axis=0)
        print(f"  Averaged {len(all_encodings)} angle(s)")
        return averaged

    def recognize_in_image(self, image_path: str):
        """Detect & recognize faces in an image."""
        if not _HAS_FR or not _HAS_CV:
            return self._mock_recognize(image_path)

        try:
            image = face_recognition.load_image_file(image_path)
        except Exception:
            return None

        boxes = face_recognition.face_locations(image, model="hog")
        encodings = face_recognition.face_encodings(image, known_face_locations=boxes)
        bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        faces = []
        for (top, right, bottom, left), enc in zip(boxes, encodings):
            name = "Unknown"
            student_id = None
            confidence = 0.0

            if self.known_encodings:
                dists = face_recognition.face_distance(self.known_encodings, enc)
                best = int(np.argmin(dists))
                if dists[best] <= MATCH_TOLERANCE:
                    name = self.known_names[best]
                    student_id = self.known_ids[best]
                    confidence = float(max(0.0, 1.0 - dists[best]))

            color = (0, 200, 80) if student_id is not None else (0, 90, 220)
            cv2.rectangle(bgr, (left, top), (right, bottom), color, 3)
            label = f"{name} {int(confidence*100)}%" if student_id else "Unknown"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(bgr, (left, top - th - 10), (left + tw + 10, top), color, -1)
            cv2.putText(bgr, label, (left + 5, top - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            faces.append({
                "box": {"top": int(top), "right": int(right),
                        "bottom": int(bottom), "left": int(left)},
                "name": name,
                "student_id": student_id,
                "confidence": round(confidence, 3),
            })

        ok, buf = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ok:
            return {"annotated_b64": None, "faces": faces}
        b64 = base64.b64encode(buf.tobytes()).decode("ascii")
        return {
            "annotated_b64": f"data:image/jpeg;base64,{b64}",
            "faces": faces,
        }

    def _mock_recognize(self, image_path: str):
        try:
            with open(image_path, "rb") as f:
                raw = f.read()
            b64 = base64.b64encode(raw).decode("ascii")
            ext = os.path.splitext(image_path)[1].lstrip(".").lower() or "jpeg"
            mime = "jpeg" if ext == "jpg" else ext
            annotated = f"data:image/{mime};base64,{b64}"
        except Exception:
            annotated = None

        faces = []
        seed = sum(ord(c) for c in os.path.basename(image_path))
        rng = np.random.default_rng(seed)
        for sid, name in zip(self.known_ids, self.known_names):
            if rng.random() < 0.7:
                faces.append({
                    "box": {"top": 0, "right": 0, "bottom": 0, "left": 0},
                    "name": name,
                    "student_id": sid,
                    "confidence": round(0.80 + 0.18 * rng.random(), 3),
                })
        return {"annotated_b64": annotated, "faces": faces}