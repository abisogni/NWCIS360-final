import cv2
from models.face_detector import FaceDetector

fd = FaceDetector()
img = cv2.imread("tmp/frames_test/frame_0000.jpg")  # one of your extracted frames
faces = fd.detect_faces(img)
print("Detected faces:", faces)

# Optionally draw and save:
for (x, y, w, h) in faces:
    cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
cv2.imwrite("tmp/face_test.jpg", img)
print("Annotated image saved to tmp/face_test.jpg")