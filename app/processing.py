# processing.py

import os
import json
import cv2
from pathlib import Path
from collections import Counter

# Import your local modules - corrected paths for your structure
import sys

sys.path.append(str(Path(__file__).resolve().parent))

from preprocess.preprocess import extract_frames, extract_audio
from models.face_detector import FaceDetector
from models.object_tracker import ObjectTracker
from models.speech_to_text import SpeechRecognizer
from deep_translator import GoogleTranslator


# Set up paths relative to the project root (parent of app folder)
BASE_DIR = Path(__file__).resolve().parent.parent  # This should point to Project folder
UPLOAD_DIR = BASE_DIR / "tmp" / "uploads"
FRAMES_DIR = BASE_DIR / "tmp" / "frames"
AUDIO_DIR = BASE_DIR / "tmp" / "audio"
RESULTS_DIR = BASE_DIR / "tmp" / "results"

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
    job_folder = UPLOAD_DIR / job_id
    video_path = job_folder / filename
    frames_out = FRAMES_DIR / job_id
    audio_out = AUDIO_DIR / f"{job_id}.wav"
    result_file = RESULTS_DIR / f"{job_id}.json"

    print(f"\n[DEBUG] Starting processing for job {job_id}")
    print(f"[DEBUG] Video path: {video_path}")

    # 1) Preprocess
    extract_frames(str(video_path), str(frames_out), fps=1)
    extract_audio(str(video_path), str(audio_out))

    # 2) Initialize models
    fd = FaceDetector()
    ot = ObjectTracker()
    sr = SpeechRecognizer(model_size="base")
    # No need to initialize translator with deep-translator

    faces_list = []
    objects_list = []

    # 3) Inference per frame
    frame_files = sorted(frames_out.glob("*.jpg"))
    print(f"[DEBUG] Processing {len(frame_files)} frames")

    for frame_file in frame_files:
        img = cv2.imread(str(frame_file))
        print(f"\n[DEBUG] Processing frame: {frame_file.name}")

        # Faces
        faces = fd.detect_faces(img)
        for box in faces:
            faces_list.append({
                "frame": frame_file.name,
                "box": box
            })

        # Objects (with enhanced debugging)
        tracks = ot.detect_and_track(img)
        for obj in tracks:
            objects_list.append({
                "frame": frame_file.name,
                "id": obj["id"],
                "label": obj["label"],
                "box": obj["box"],
                "confidence": obj.get("confidence", 0.0)
            })

    # 4) Speech transcription (expects German spoken)
    print(f"\n[DEBUG] Transcribing audio: {audio_out}")
    transcript = sr.transcribe_audio(str(audio_out))
    print(f"[DEBUG] Transcription result: '{transcript}'")

    # 5) Enhanced object analysis with debugging
    print(f"\n[DEBUG] Total objects detected across all frames: {len(objects_list)}")
    for i, obj in enumerate(objects_list):
        print(
            f"[DEBUG] Object {i + 1}: {obj['label']} (ID: {obj['id']}, conf: {obj.get('confidence', 0):.2f}) in frame {obj['frame']}")

    # Show all unique labels detected
    unique_labels = list(set([o["label"] for o in objects_list]))
    print(f"[DEBUG] Unique object labels detected: {unique_labels}")

    # Filter out person objects
    filtered = [o for o in objects_list if o["label"].lower() != "person"]
    print(f"[DEBUG] After filtering out 'person' objects: {len(filtered)} remaining")

    if filtered:
        # Group by label to see counts
        label_counts = Counter([o["label"] for o in filtered])
        print(f"[DEBUG] Object counts: {dict(label_counts)}")

        # Pick the most common non-person object
        most_common_label = label_counts.most_common(1)[0][0]
        primary_objects = [o for o in filtered if o["label"] == most_common_label]
        primary_object = primary_objects[0]

        label_english = primary_object["label"]
        print(f"[DEBUG] Selected primary object: {label_english}")

        # translate to German
        try:
            label_german = GoogleTranslator(source='en', target='de').translate(label_english)
            print(f"[DEBUG] Translated '{label_english}' → '{label_german}'")
        except Exception as e:
            print(f"[DEBUG] Translation failed: {e}")
            # fallback to English if translation fails
            label_german = label_english
    else:
        print("[DEBUG] No objects detected after filtering out 'person'")
        label_english = None
        label_german = None

    # 6) Aggregate & write result JSON
    result = {
        "faces": faces_list,
        "objects": objects_list,
        "transcript": transcript,
        "label_english": label_english,
        "label_german": label_german
    }

    print(f"\n[DEBUG] Final result summary:")
    print(f"[DEBUG] - Faces detected: {len(faces_list)}")
    print(f"[DEBUG] - Objects detected: {len(objects_list)}")
    print(f"[DEBUG] - Transcript: '{transcript}'")
    print(f"[DEBUG] - Primary object (EN): {label_english}")
    print(f"[DEBUG] - Primary object (DE): {label_german}")

    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result_file