import face_recognition
import cv2
import os
import numpy as np

class FaceRecognizer:
    def __init__(self, known_faces_dir, tolerance=0.6):
        self.tolerance = tolerance
        self.known_encodings = []
        self.known_names = []
        self._load_known_faces(known_faces_dir)

    def _load_known_faces(self, directory):
        for filename in os.listdir(directory):
            if filename.endswith(('.jpg', '.png')):
                path = os.path.join(directory, filename)
                image = face_recognition.load_image_file(path)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    self.known_encodings.append(encodings[0])
                    name = os.path.splitext(filename)[0]
                    self.known_names.append(name)
                    print(f"Loaded: {name}")
                else:
                    print(f"WARNING: No face in {filename}")

    def recognize_in_image(self, image_path):
        image = face_recognition.load_image_file(image_path)
        face_locations = face_recognition.face_locations(image)
        face_encodings = face_recognition.face_encodings(image, face_locations)

        results = []
        for location, encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(
                self.known_encodings, encoding, tolerance=self.tolerance
            )
            distances = face_recognition.face_distance(self.known_encodings, encoding)
            name = "Unknown"
            if True in matches:
                best_match = np.argmin(distances)
                if matches[best_match]:
                    name = self.known_names[best_match]
            results.append((name, location))

        return results, image