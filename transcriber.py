# transcriber.py
import time
from faster_whisper import WhisperModel
import os # <-- Includes fix

def load_whisper_model(model_size, device, compute_type):
    """ Loads the faster-whisper model. """
    print(f"Loading Whisper model: {model_size} ({device}, {compute_type})...")
    try:
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print("Whisper model loaded successfully.")
        return model
    except Exception as e:
        print(f"Error loading Whisper model: {e}")
        return None

def run_transcription(model, audio_path):
    """ Runs transcription on the audio file using the loaded model. Returns generator. """
    if model is None:
        print("Error: Whisper model not loaded.")
        return None, None

    print(f"Running transcription on {os.path.basename(audio_path)} (word timestamps enabled)...")
    start_transcription = time.time()
    try:
        segments, info = model.transcribe(
            audio_path,
            beam_size=5,
            vad_filter=True,
            word_timestamps=True
        )
        print(f"Transcription complete in {time.time() - start_transcription:.2f} seconds.")
        if info:
             print(f"Detected language: {info.language} (Prob: {info.language_probability:.2f})")
        return segments, info
    except Exception as e:
        print(f"Error during transcription: {e}")
        return None, None