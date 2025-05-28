import cv2
from models.object_tracker import ObjectTracker

# Load a sample frame from your extracted frames
frame = cv2.imread("tmp/frames_test/frame_0000.jpg")
tracker = ObjectTracker(model_name="yolov8n.pt")

# Run detection & tracking
results = tracker.detect_and_track(frame)
print("Tracks:", results)

# Draw & save
for obj in results:
    x1,y1,x2,y2 = obj['box']
    label = f"{obj['label']}:{obj['id']}"
    cv2.rectangle(frame, (x1,y1), (x2,y2), (255,0,0), 2)
    cv2.putText(frame, label, (x1,y1-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 1)
cv2.imwrite("tmp/obj_test.jpg", frame)
print("Annotated object image saved to tmp/obj_test.jpg")