import whisper

class SpeechRecognizer:
    def __init__(self, model_size: str = "small"):
        """
        model_size: one of tiny, base, small, medium, large.
        Smaller models are faster but less accurate.
        """
        self.model = whisper.load_model(model_size)

    def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe the given WAV file and return the raw transcript string.
        """
        result = self.model.transcribe(audio_path, language="de")
        # result['text'] contains your German transcript
        return result["text"].strip()