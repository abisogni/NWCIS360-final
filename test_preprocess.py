from preprocess.preprocess import extract_frames, extract_audio

VIDEO = "test_flasche.mov"
FRAMES_OUT = "tmp/frames_test"
AUDIO_OUT  = "tmp/audio_test.wav"

# 1) Extract 1 fps frames
extract_frames(VIDEO, FRAMES_OUT, fps=1)
print("Frames saved in", FRAMES_OUT)

# 2) Extract audio
extract_audio(VIDEO, AUDIO_OUT)
print("Audio saved to", AUDIO_OUT)