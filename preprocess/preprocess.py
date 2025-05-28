import cv2
import os
from ffmpeg import input as ffmpeg_input

def extract_frames(video_path: str, output_dir: str, fps: int = 1) -> None:
    """
    Extract frames from video at `fps` frames-per-second.
    Saves JPEGs to output_dir/frame_0001.jpg, frame_0002.jpg, etc.
    """
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    video_fps = cap.get(cv2.CAP_PROP_FPS) or fps
    frame_interval = int(video_fps // fps)

    count = 0
    saved = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if count % frame_interval == 0:
            filename = os.path.join(output_dir, f"frame_{saved:04d}.jpg")
            cv2.imwrite(filename, frame)
            saved += 1
        count += 1

    cap.release()

def extract_audio(video_path: str, audio_path: str) -> None:
    """
    Extract the audio track from video_path and save as audio_path (wav).
    Requires ffmpeg installed on your system.
    """
    (
        ffmpeg_input(video_path)
        .output(audio_path, format='wav', acodec='pcm_s16le', ac=1, ar='16k')
        .overwrite_output()
        .run(quiet=True)
    )