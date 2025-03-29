# transcriber.py
import time
from faster_whisper import WhisperModel
import os

# Global variable to cache the model (optional, for efficiency if called multiple times)
# _whisper_model_cache = {}

def load_whisper_model(model_size, device, compute_type):
    """ Loads the faster-whisper model. """
    # Simple loading for now, caching could be added later if needed
    print(f"Loading Whisper model: {model_size} ({device}, {compute_type})...")
    try:
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print("Whisper model loaded successfully.")
        return model
    except Exception as e:
        print(f"Error loading Whisper model: {e}")
        # Consider more specific error handling or raising the exception
        return None

def run_transcription(model, audio_path):
    """ Runs transcription on the audio file using the loaded model. """
    if model is None:
        print("Error: Whisper model not loaded.")
        return None, None

    print(f"Running transcription on {os.path.basename(audio_path)} (word timestamps enabled)...")
    start_transcription = time.time()
    try:
        # Ensure word_timestamps=True for alignment
        segments, info = model.transcribe(
            audio_path,
            beam_size=5,
            vad_filter=True,
            word_timestamps=True
        )
        print(f"Transcription complete in {time.time() - start_transcription:.2f} seconds.")
        print(f"Detected language: {info.language} (Prob: {info.language_probability:.2f})")
        return segments, info
    except Exception as e:
        print(f"Error during transcription: {e}")
        return None, None