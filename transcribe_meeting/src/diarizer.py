# diarizer.py
"""Speaker diarization utilities using pyannote.audio."""
import time
import torch
import os
import shutil
import platform
from pathlib import Path
from pyannote.audio import Pipeline
import logging
from typing import Optional, Any, List, Dict


# Set environment variable to disable symlinks warning and use direct copies instead
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"


def windows_workaround_for_pyannote():
    """Workaround for Windows symlink issues with pyannote.audio.
    
    This function manually copies necessary files instead of relying on symlinks
    which require elevated privileges on Windows.
    """
    if platform.system() != "Windows":
        return
    
    # Define source and target paths
    cache_dir = Path(os.path.expanduser("~/.cache"))
    hf_cache = cache_dir / "huggingface" / "hub"
    torch_cache = cache_dir / "torch" / "pyannote" / "speechbrain"
    
    # Create directories
    torch_cache.mkdir(parents=True, exist_ok=True)
    
    # Find the speechbrain model directory
    try:
        speechbrain_dirs = list(hf_cache.glob(
            "**/models--speechbrain--spkrec-ecapa-voxceleb/snapshots/*"
        ))
        if speechbrain_dirs:
            src_dir = speechbrain_dirs[0]
            # Copy the hyperparams.yaml file directly instead of symlinking
            src_file = src_dir / "hyperparams.yaml"
            if src_file.exists():
                dst_file = torch_cache / "hyperparams.yaml"
                try:
                    shutil.copy2(src_file, dst_file)
                    logging.info(f"Successfully copied {src_file} to {dst_file}")
                except Exception as e:
                    logging.warning(f"Failed to copy file: {e}")
    except Exception as e:
        logging.warning(f"Windows workaround failed: {e}")


def load_diarization_pipeline(
    pipeline_name: str,
    auth_token: Optional[str] = None
) -> Optional[Pipeline]:
    """Load the pyannote.audio diarization pipeline.
    
    Args:
        pipeline_name: Name of the pipeline to load
        auth_token: Optional Hugging Face authentication token
        
    Returns:
        Loaded pipeline or None if loading failed
    """
    logging.info(f"Loading speaker diarization pipeline: {pipeline_name}...")
    
    # Apply Windows workaround
    windows_workaround_for_pyannote()
    
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
        logging.error("Ensure model name is correct, you've accepted HF terms, "
                     "and logged in via `huggingface-cli login` or provided a token.")
        return None


def run_diarization(pipeline: Optional[Pipeline], audio_path: str) -> Any:
    """Run diarization on the audio file using the loaded pipeline.
    
    Args:
        pipeline: The loaded diarization pipeline
        audio_path: Path to the audio file
        
    Returns:
        Diarization result or None if failed
    """
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
    """Extract speaker turns from the diarization result and sort them.
    
    Args:
        diarization_result: The result from the diarization pipeline
        
    Returns:
        List of speaker turns with start/end times and speaker labels
    """
    if diarization_result is None:
        return []
    
    speaker_turns = []
    try:
        for turn, _, speaker_label in diarization_result.itertracks(yield_label=True):
            speaker_turns.append({
                "start": turn.start,
                "end": turn.end,
                "speaker": speaker_label
            })
        speaker_turns.sort(key=lambda x: x['start'])
        return speaker_turns
    except Exception as e:
        logging.error(f"Error processing diarization result tracks: {e}. "
                     f"Result was: {diarization_result}")
        return []