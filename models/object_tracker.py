import cv2
from ultralytics import YOLO
from collections import deque

class ObjectTracker:
    def __init__(self, model_name="yolov8n.pt", max_age=5):
        """
        model_name: pretrained YOLOv8 model (e.g., yolov8n.pt for the nano model).
        max_age: how many frames to keep “lost” tracks before dropping.
        """
        self.model = YOLO(model_name)
        self.next_id = 0
        self.tracks = {}            # track_id → {'box': (x1,y1,x2,y2), 'age': 0}
        self.max_age = max_age

    def _create_track(self, box):
        tid = self.next_id
        self.tracks[tid] = {'box': box, 'age': 0}
        self.next_id += 1
        return tid

    def _iou(self, boxA, boxB):
        # Compute Intersection over Union between two boxes (x1,y1,x2,y2)
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        interW = max(0, xB - xA)
        interH = max(0, yB - yA)
        interArea = interW * interH
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        return interArea / float(boxAArea + boxBArea - interArea + 1e-6)

    def detect_and_track(self, frame):
        """
        Run YOLO detection on frame, then match to existing tracks via IoU.
        Returns a list of dicts: [{'id': track_id, 'label': str, 'box': [x1,y1,x2,y2]}, ...].
        """
        results = self.model(frame)[0]
        detections = []
        # Convert each detection to [x1,y1,x2,y2,label]
        for *xyxy, conf, cls in results.boxes.data.tolist():
            x1, y1, x2, y2 = map(int, xyxy)
            label = self.model.names[int(cls)]
            detections.append({'box': (x1, y1, x2, y2), 'label': label})

        # Age existing tracks
        for tid in list(self.tracks):
            self.tracks[tid]['age'] += 1
            if self.tracks[tid]['age'] > self.max_age:
                del self.tracks[tid]

        # Match detections to tracks
        outputs = []
        for det in detections:
            best_tid, best_iou = None, 0.0
            for tid, tr in self.tracks.items():
                iou = self._iou(det['box'], tr['box'])
                if iou > best_iou and iou > 0.3:
                    best_tid, best_iou = tid, iou
            if best_tid is None:
                best_tid = self._create_track(det['box'])
            # Update track
            self.tracks[best_tid] = {'box': det['box'], 'age': 0}
            outputs.append({
                'id': best_tid,
                'label': det['label'],
                'box': det['box']
            })

        return outputs