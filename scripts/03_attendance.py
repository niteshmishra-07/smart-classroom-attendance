import face_recognition
import cv2
import os
import numpy as np
import csv
from datetime import datetime

print("Loading known faces...")
known_encodings = []
known_names = []

known_faces_dir = 'test_images/known_faces'
for filename in os.listdir(known_faces_dir):
    if filename.endswith(('.jpg', '.png')):
        path = os.path.join(known_faces_dir, filename)
        image = face_recognition.load_image_file(path)
        encodings = face_recognition.face_encodings(image)
        if len(encodings) > 0:
            known_encodings.append(encodings[0])
            name = filename.split('.')[0]
            known_names.append(name)
            print(f"  Loaded: {name}")

all_students = [f.split('.')[0] for f in os.listdir(known_faces_dir)
                if f.endswith(('.jpg', '.png'))]

print("\nProcessing group photo...")
image_path = 'test_images/group2.jpg'
group_image = face_recognition.load_image_file(image_path)
face_locations = face_recognition.face_locations(group_image)
face_encodings = face_recognition.face_encodings(group_image, face_locations)
print(f"Found {len(face_encodings)} faces in group photo")

# DUPLICATE FIX — track already seen students
present_students = []
group_image_bgr = cv2.cvtColor(group_image, cv2.COLOR_RGB2BGR)

for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
    matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.6)
    distances = face_recognition.face_distance(known_encodings, face_encoding)
    name = "Unknown"
    if True in matches:
        best_match = np.argmin(distances)
        if matches[best_match]:
            name = known_names[best_match]
            # DUPLICATE CHECK — sirf ek baar add karo
            if name not in present_students:
                present_students.append(name)

    color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
    cv2.rectangle(group_image_bgr, (left, top), (right, bottom), color, 2)
    cv2.putText(group_image_bgr, name, (left, top-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

cv2.imwrite('outputs/output_group2_fixed.jpg', group_image_bgr)

# CSV Generate
date_today = datetime.now().strftime("%Y-%m-%d")
time_now = datetime.now().strftime("%H:%M:%S")
csv_path = f'outputs/attendance_{date_today}.csv'

with open(csv_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Name', 'Status', 'Date', 'Time'])
    for student in all_students:
        status = 'Present' if student in present_students else 'Absent'
        writer.writerow([student, status, date_today, time_now])

print("\n=== ATTENDANCE REPORT ===")
for student in all_students:
    status = 'Present ✓' if student in present_students else 'Absent ✗'
    print(f"  {student}: {status}")

print(f"\nPresent: {len(present_students)}/{len(all_students)}")
print(f"CSV saved: {csv_path}")
print(f"Image saved: outputs/output_group2_fixed.jpg")