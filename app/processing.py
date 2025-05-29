# processing.py

import os
import json
from pathlib import Path

from preprocess.preprocess import extract_frames, extract_audio
from models.face_detector import FaceDetector
from models.object_tracker import ObjectTracker
from models.speech_to_text import SpeechRecognizer
from googletrans import Translator

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
    4) Transcribe audio (German)
    5) Translate detected object label to German
    6) Save JSON result to tmp/results/<job_id>.json
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

    # 2) Initialize models
    fd = FaceDetector()
    ot = ObjectTracker()
    sr = SpeechRecognizer(model_size="small")
    translator = Translator(service_urls=['translate.googleapis.com'])

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

    # 4) Speech transcription (expects German spoken)
    transcript = sr.transcribe_audio(str(audio_out))

    # 5) Pick primary detected object (filter out generic "person")
    filtered = [o for o in objects_list if o["label"].lower() != "person"]
    if filtered:
        label_english = filtered[0]["label"]
        # translate to German
        try:
            label_german = translator.translate(label_english, dest="de").text
            print(f"[debug] translate('{label_english}') → '{label_german}'")
        except Exception:
            # fallback to English if translation fails
            label_german = label_english
    else:
        label_english = None
        label_german  = None

    # 6) Aggregate & write result JSON
    result = {
        "faces":          faces_list,
        "objects":        objects_list,
        "transcript":     transcript,
        "label_english":  label_english,
        "label_german":   label_german
    }
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result_file