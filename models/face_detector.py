import cv2

class FaceDetector:
    def __init__(self, cascade_path=None):
        # Use OpenCV’s built‑in frontal‑face Haar Cascade by default
        if cascade_path:
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
        else:
            # This path comes bundled with OpenCV
            default_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self.face_cascade = cv2.CascadeClassifier(default_path)

    def detect_faces(self, image):
        """
        Detect faces in a single BGR image (numpy array).
        Returns a list of [x, y, w, h] rectangles.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        return faces.tolist() if len(faces) > 0 else []