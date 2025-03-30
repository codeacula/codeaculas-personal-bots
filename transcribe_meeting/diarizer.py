# diarizer.py
import time
import torch
from pyannote.audio import Pipeline
import os
import sys

def load_diarization_pipeline(pipeline_name, auth_token=None):
    """ Loads the pyannote.audio diarization pipeline. """
    print(f"Loading speaker diarization pipeline: {pipeline_name}...")
    try:
        pipeline = Pipeline.from_pretrained(
            pipeline_name,
            use_auth_token=auth_token
        )
        if torch.cuda.is_available():
             pipeline.to(torch.device("cuda"))
        print("Diarization pipeline loaded successfully.")
        return pipeline
    except Exception as e:
        print(f"Error loading diarization pipeline: {e}")
        print("Ensure model name is correct, you've accepted HF terms, and logged in via `huggingface-cli login` or provided a token.")
        return None

def run_diarization(pipeline, audio_path):
    """ Runs diarization on the audio file using the loaded pipeline. """
    if pipeline is None:
        print("Error: Diarization pipeline not loaded.")
        return None

    print(f"Running speaker diarization on {os.path.basename(audio_path)}...")
    start_diarization = time.time()
    try:
        diarization_result = pipeline(audio_path)
        print(f"Diarization complete in {time.time() - start_diarization:.2f} seconds.")
        return diarization_result
    except Exception as e:
        print(f"Error during diarization: {e}")
        return None

def extract_speaker_turns(diarization_result):
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
         print(f"Error processing diarization result tracks: {e}. Result was: {diarization_result}")
         return []