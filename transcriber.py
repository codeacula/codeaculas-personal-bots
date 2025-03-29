# transcriber.py
import time
from faster_whisper import WhisperModel, BatchedInferencePipeline # <-- Import added
import os
import config # <-- Import config to get settings

# Keep load_whisper_model simple, it just loads the base model
def load_whisper_model(model_size, device, compute_type):
    """ Loads the base faster-whisper model. """
    print(f"Loading Whisper base model: {model_size} ({device}, {compute_type})...")
    try:
        # Load with potentially new compute_type from config
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print("Whisper base model loaded successfully.")
        return model
    except Exception as e:
        print(f"Error loading Whisper base model: {e}")
        return None

# Modify run_transcription to use the BatchedInferencePipeline
def run_transcription(model, audio_path):
    """ Runs transcription using BatchedInferencePipeline. """
    if model is None:
        print("Error: Whisper base model not loaded.")
        return None, None

    # Get settings from config
    batch_size = config.WHISPER_BATCH_SIZE
    beam_size = config.WHISPER_BEAM_SIZE

    print(f"Running transcription on {os.path.basename(audio_path)} "
          f"(batch_size={batch_size}, beam_size={beam_size}, word timestamps enabled)...")
    start_transcription = time.time()

    try:
        # --- Create BatchedInferencePipeline ---
        # We create it here, potentially loading specific batch-related resources
        print("Initializing BatchedInferencePipeline...")
        # Note: Pass the already loaded base 'model' object
        batched_model = BatchedInferencePipeline(model=model)
        print("BatchedInferencePipeline initialized.")
        # ---------------------------------------

        # --- Call transcribe on the batched model ---
        segments, info = batched_model.transcribe(
            audio_path,
            batch_size=batch_size,
            beam_size=beam_size,
            word_timestamps=True,
            vad_filter=True # Keep VAD enabled
        )
        # --------------------------------------------

        # NOTE: 'segments' is still likely a generator! Materialization needed later.
        print(f"Transcription call returned in {time.time() - start_transcription:.2f} seconds.") # Time for setup + yielding generator
        if info:
             print(f"Detected language: {info.language} (Prob: {info.language_probability:.2f})")
        return segments, info
    except Exception as e:
        print(f"Error during batched transcription: {e}")
        import traceback
        traceback.print_exc() # Print full traceback for debugging
        return None, None