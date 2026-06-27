import cv2
from mtcnn import MTCNN

# Load detector
detector = MTCNN()

# Load image
image = cv2.imread('test_images/group1.jpg')
image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# Detect faces
faces = detector.detect_faces(image_rgb)

print(f"Number of faces detected: {len(faces)}")

# Draw boxes around faces
for face in faces:
    x, y, w, h = face['box']
    confidence = face['confidence']
    cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
    cv2.putText(image, f"{confidence:.2f}", (x, y-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

# Save output
cv2.imwrite('output_detected.jpg', image)
print("Saved output_detected.jpg")
