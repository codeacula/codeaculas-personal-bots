# transcriber.py
import time
from faster_whisper import WhisperModel, BatchedInferencePipeline
import os
import config
import logging
from typing import Optional, Tuple, Any, Dict, List, Union

class ModelManager:
    """Context manager for handling Whisper model resources"""
    def __init__(self, model_size: str, device: str, compute_type: str):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None
        
    def __enter__(self) -> Optional[WhisperModel]:
        """Load the model when entering context"""
        logging.info(f"Loading Whisper base model: {self.model_size} ({self.device}, {self.compute_type})...")
        try:
            self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
            logging.info("Whisper base model loaded successfully.")
            return self.model
        except Exception as e:
            logging.error(f"Error loading Whisper base model: {e}")
            return None
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources when exiting context"""
        # Currently, WhisperModel doesn't have an explicit cleanup method
        # But this context manager allows for proper cleanup in the future
        self.model = None

def load_whisper_model(model_size: str, device: str, compute_type: str) -> Optional[WhisperModel]:
    """ Loads the base faster-whisper model. """
    logging.info(f"Loading Whisper base model: {model_size} ({device}, {compute_type})...")
    try:
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
        logging.info("Whisper base model loaded successfully.")
        return model
    except Exception as e:
        logging.error(f"Error loading Whisper base model: {e}")
        return None

def run_transcription(model: Optional[WhisperModel], audio_path: str) -> Tuple[Optional[Any], Optional[Dict]]:
    """ Runs transcription using BatchedInferencePipeline. """
    if model is None:
        logging.error("Error: Whisper base model not loaded.")
        return None, None

    # Get settings from config
    batch_size = config.WHISPER_BATCH_SIZE
    beam_size = config.WHISPER_BEAM_SIZE

    logging.info(f"Running transcription on {os.path.basename(audio_path)} "
          f"(batch_size={batch_size}, beam_size={beam_size}, word timestamps enabled)...")
    start_transcription = time.time()

    try:
        # Create BatchedInferencePipeline
        logging.info("Initializing BatchedInferencePipeline...")
        batched_model = BatchedInferencePipeline(model=model)
        logging.info("BatchedInferencePipeline initialized.")

        # Call transcribe on the batched model
        segments, info = batched_model.transcribe(
            audio_path,
            batch_size=batch_size,
            beam_size=beam_size,
            word_timestamps=True,
            vad_filter=True
        )

        # Note: 'segments' is a generator that will be materialized later
        logging.info(f"Transcription call returned in {time.time() - start_transcription:.2f} seconds.")
        if info:
             logging.info(f"Detected language: {info.language} (Prob: {info.language_probability:.2f})")
        return segments, info
    except Exception as e:
        logging.error(f"Error during batched transcription: {e}")
        import traceback
        traceback.print_exc()
        return None, None