import face_recognition
import os
import numpy as np

def load_student_encodings(students_dir):
    """Har student ke liye multiple angle encodings load karo"""
    student_encodings = {}
    
    for student_name in os.listdir(students_dir):
        student_folder = os.path.join(students_dir, student_name)
        if os.path.isdir(student_folder):
            encodings = []
            for photo in os.listdir(student_folder):
                if photo.endswith(('.jpg', '.png')):
                    path = os.path.join(student_folder, photo)
                    image = face_recognition.load_image_file(path)
                    found = face_recognition.face_encodings(image)
                    if found:
                        encodings.append(found[0])
                        print(f"  Loaded: {student_name}/{photo}")
                    else:
                        print(f"  WARNING: No face in {photo}")
            
            if encodings:
                # Average embedding — yeh tera novelty hai!
                student_encodings[student_name] = np.mean(encodings, axis=0)
                print(f"  ✅ {student_name}: {len(encodings)} angles averaged")
    
    return student_encodings

# Load students
print("=== Loading Student Encodings ===")
students_dir = 'data/students'
student_encodings = load_student_encodings(students_dir)

print(f"\nTotal students loaded: {len(student_encodings)}")
for name in student_encodings:
    print(f"  - {name}")

print("\n✅ Multi-angle encoding ready!")
print("Next step: Match against group photo")
import cv2
import csv
from datetime import datetime

print("\n=== Processing Group Photo ===")
image_path = 'test_images/group2.jpg'
group_image = face_recognition.load_image_file(image_path)
face_locations = face_recognition.face_locations(group_image)
face_encodings_list = face_recognition.face_encodings(group_image, face_locations)
print(f"Found {len(face_encodings_list)} faces")

# Match faces
present_students = []
group_image_bgr = cv2.cvtColor(group_image, cv2.COLOR_RGB2BGR)

known_names = list(student_encodings.keys())
known_encodings = list(student_encodings.values())

for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings_list):
    distances = face_recognition.face_distance(known_encodings, face_encoding)
    name = "Unknown"
    if len(distances) > 0:
        best_match = np.argmin(distances)
        if distances[best_match] < 0.6:
            name = known_names[best_match]
            if name not in present_students:
                present_students.append(name)
    color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
    cv2.rectangle(group_image_bgr, (left, top), (right, bottom), color, 2)
    cv2.putText(group_image_bgr, name, (left, top-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

cv2.imwrite('outputs/output_multiangle.jpg', group_image_bgr)

# Attendance Report
print("\n=== ATTENDANCE REPORT ===")
all_students = list(student_encodings.keys())
for student in all_students:
    status = 'Present ✓' if student in present_students else 'Absent ✗'
    print(f"  {student}: {status}")

print(f"\nPresent: {len(present_students)}/{len(all_students)}")
print("Image saved: outputs/output_multiangle.jpg")