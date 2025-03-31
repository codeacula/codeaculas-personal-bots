# diarizer.py
import time
import torch
from pyannote.audio import Pipeline
import logging
from typing import Optional, Any, List, Dict
import os

def load_diarization_pipeline(pipeline_name: str, auth_token: Optional[str] = None) -> Optional[Pipeline]:
    """ Loads the pyannote.audio diarization pipeline. """
    logging.info(f"Loading speaker diarization pipeline: {pipeline_name}...")
    try:
        pipeline = Pipeline.from_pretrained(
            pipeline_name,
            use_auth_token=auth_token
        )
        if torch.cuda.is_available():
             pipeline.to(torch.device("cuda"))
        logging.info("Diarization pipeline loaded successfully.")
        return pipeline
    except Exception as e:
        logging.error(f"Error loading diarization pipeline: {e}")
        logging.error("Ensure model name is correct, you've accepted HF terms, and logged in via `huggingface-cli login` or provided a token.")
        return None

def run_diarization(pipeline: Optional[Pipeline], audio_path: str) -> Any:
    """ Runs diarization on the audio file using the loaded pipeline. """
    if pipeline is None:
        logging.error("Error: Diarization pipeline not loaded.")
        return None

    logging.info(f"Running speaker diarization on {os.path.basename(audio_path)}...")
    start_diarization = time.time()
    try:
        diarization_result = pipeline(audio_path)
        logging.info(f"Diarization complete in {time.time() - start_diarization:.2f} seconds.")
        return diarization_result
    except Exception as e:
        logging.error(f"Error during diarization: {e}")
        return None

def extract_speaker_turns(diarization_result: Any) -> List[Dict[str, Any]]:
    """ Extracts speaker turns from the diarization result and sorts them. """
    if diarization_result is None:
        return []
    speaker_turns = []
    try:
        for turn, _, speaker_label in diarization_result.itertracks(yield_label=True):
            speaker_turns.append({"start": turn.start, "end": turn.end, "speaker": speaker_label})
        speaker_turns.sort(key=lambda x: x['start'])
        return speaker_turns
    except Exception as e:
         logging.error(f"Error processing diarization result tracks: {e}. Result was: {diarization_result}")
         return []