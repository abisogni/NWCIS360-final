from models.speech_to_text import SpeechRecognizer

# Path to a sample audio extracted earlier, e.g. tmp/audio_test.wav
AUDIO_FILE = "tmp/audio_test.wav"

sr = SpeechRecognizer(model_size="small")
transcript = sr.transcribe_audio(AUDIO_FILE)
print("Transcript:", transcript)

# Optionally, save to a text file for your docs
with open("docs/transcripts/sample.txt", "w") as f:
    f.write(transcript)
    print("Saved transcript to docs/transcripts/sample.txt")