import os
import json
from pathlib import Path
from preprocess.preprocess import extract_frames, extract_audio
from models.face_detector import FaceDetector
from models.object_tracker import ObjectTracker
from models.speech_to_text import SpeechRecognizer

# Set up paths relative to the project root
BASE_DIR     = Path(__file__).resolve().parent.parent
UPLOAD_DIR   = BASE_DIR / "tmp" / "uploads"
FRAMES_DIR   = BASE_DIR / "tmp" / "frames"
AUDIO_DIR    = BASE_DIR / "tmp" / "audio"
RESULTS_DIR  = BASE_DIR / "tmp" / "results"

# Ensure output dirs exist
for d in (FRAMES_DIR, AUDIO_DIR, RESULTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

def process_job(job_id: str, filename: str):
    """
    Run the full pipeline for a given job:
    1) Preprocess video → frames + audio
    2) Run face detection on each frame
    3) Run object tracking on each frame
    4) Transcribe audio
    5) Save JSON result to tmp/results/<job_id>.json
    """
    # Paths
    job_folder  = UPLOAD_DIR / job_id
    video_path  = job_folder / filename
    frames_out  = FRAMES_DIR / job_id
    audio_out   = AUDIO_DIR / f"{job_id}.wav"
    result_file = RESULTS_DIR / f"{job_id}.json"

    # 1) Preprocess
    extract_frames(str(video_path), str(frames_out), fps=1)
    extract_audio(str(video_path), str(audio_out))

    # 2) Models
    fd      = FaceDetector()
    ot      = ObjectTracker()
    sr      = SpeechRecognizer(model_size="small")

    faces_list   = []
    objects_list = []

    # 3) Inference per frame
    for frame_file in sorted(frames_out.glob("*.jpg")):
        import cv2
        img = cv2.imread(str(frame_file))

        # Faces
        faces = fd.detect_faces(img)
        for box in faces:
            faces_list.append({
                "frame": frame_file.name,
                "box": box
            })

        # Objects
        tracks = ot.detect_and_track(img)
        for obj in tracks:
            objects_list.append({
                "frame": frame_file.name,
                "id":    obj["id"],
                "label": obj["label"],
                "box":   obj["box"]
            })

    # 4) Speech
    transcript = sr.transcribe_audio(str(audio_out))

    # 5) Aggregate & write
    result = {
        "faces":     faces_list,
        "objects":   objects_list,
        "transcript": transcript
    }
    with open(result_file, "w") as f:
        json.dump(result, f, indent=2)

    return result_file