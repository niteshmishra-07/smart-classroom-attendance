import face_recognition
import cv2
import os
import numpy as np

# Step A: Load known faces
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
            print(f"Loaded: {name}")
        else:
            print(f"No face found in: {filename}")

# Step B: Load group photo
group_image = face_recognition.load_image_file('test_images/group1.jpg')
face_locations = face_recognition.face_locations(group_image)
face_encodings = face_recognition.face_encodings(group_image, face_locations)
print(f"\nFound {len(face_encodings)} faces in group photo")

# Step C: Match faces
group_image_bgr = cv2.cvtColor(group_image, cv2.COLOR_RGB2BGR)
for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
    matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.6)
    distances = face_recognition.face_distance(known_encodings, face_encoding)
    name = "Unknown"
    if True in matches:
        best_match = np.argmin(distances)
        if matches[best_match]:
            name = known_names[best_match]
    color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
    cv2.rectangle(group_image_bgr, (left, top), (right, bottom), color, 2)
    cv2.putText(group_image_bgr, name, (left, top-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

cv2.imwrite('output_recognized.jpg', group_image_bgr)
print("Saved output_recognized.jpg")