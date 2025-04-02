# config.py
# Configuration settings for the transcription process

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

# --- Model/Device Settings ---
WHISPER_MODEL_SIZE = "large-v3"
WHISPER_DEVICE = "cuda"
# Change to int8 for potentially faster batched inference
WHISPER_COMPUTE_TYPE = "int8" # Was "float16"
WHISPER_BEAM_SIZE = 4 # Keep beam size at 4 from last test
WHISPER_BATCH_SIZE = 8 # Set batch size based on benchmark

DIARIZATION_PIPELINE_NAME = "pyannote/speaker-diarization-3.1"
HUGGINGFACE_AUTH_TOKEN = None

# --- Paths and File Management ---
# Use raw strings (r"...") for Windows paths if needed, but os.path.join handles separators
REPO_ROOT = r"D:\Projects\work-notes" # Root of the Git repository
TRANSCRIPT_BASE_DIR_NAME = "Transcripts" # Subdirectory for transcripts within repo
PROCESSED_VIDEO_DIR = r"D:\Processed" # Fixed directory for processed videos
DELETE_TEMP_AUDIO = True # Delete the intermediate WAV file?
MOVE_PROCESSED_VIDEO = True # Move the original video after processing?

# --- SRT Formatting Options ---
SRT_OPTIONS = {
    "max_line_length": 42,
    "max_words_per_entry": 10,
    "speaker_gap_threshold": 1.0, # Seconds gap to force new SRT entry
}

# --- Git Options ---
GIT_ENABLED = True # Enable/disable Git operations
GIT_COMMIT_MESSAGE_PREFIX = "Add transcript for" # Prefix for commit messages

# --- Alignment Multiprocessing Tuning ---
# Target number of words for each parallel alignment task
ALIGNMENT_TARGET_WORDS_PER_CHUNK = 5000
# Maximum number of worker processes to use for alignment (e.g., physical cores, or less)
ALIGNMENT_MAX_WORKERS = 12 # Set based on your preference/CPU (e.g., os.cpu_count() // 2)
# Minimum number of worker processes to use for alignment
ALIGNMENT_MIN_WORKERS = 1

def validate_config() -> List[str]:
    """Validate configuration settings to prevent runtime errors"""
    issues = []
    
    # Validate model settings
    valid_models = ["tiny", "base", "small", "medium", "large-v1", "large-v2", "large-v3"]
    if WHISPER_MODEL_SIZE not in valid_models:
        issues.append(f"Warning: WHISPER_MODEL_SIZE '{WHISPER_MODEL_SIZE}' may not be valid. Expected one of: {valid_models}")
    
    valid_devices = ["cpu", "cuda", "auto"]
    if WHISPER_DEVICE not in valid_devices:
        issues.append(f"Warning: WHISPER_DEVICE '{WHISPER_DEVICE}' not valid. Expected one of: {valid_devices}")
    
    valid_compute_types = ["float16", "float32", "int8"]
    if WHISPER_COMPUTE_TYPE not in valid_compute_types:
        issues.append(f"Warning: WHISPER_COMPUTE_TYPE '{WHISPER_COMPUTE_TYPE}' not valid. Expected one of: {valid_compute_types}")
    
    # Validate path settings
    if not Path(REPO_ROOT).exists():
        issues.append(f"Warning: REPO_ROOT directory '{REPO_ROOT}' does not exist")
    
    if PROCESSED_VIDEO_DIR and not Path(PROCESSED_VIDEO_DIR).exists():
        issues.append(f"Warning: PROCESSED_VIDEO_DIR '{PROCESSED_VIDEO_DIR}' does not exist")
    
    # Validate SRT options
    if not isinstance(SRT_OPTIONS, dict):
        issues.append("Error: SRT_OPTIONS must be a dictionary")
    else:
        if "max_line_length" in SRT_OPTIONS and not isinstance(SRT_OPTIONS["max_line_length"], int):
            issues.append("Warning: SRT_OPTIONS['max_line_length'] should be an integer")
        if "max_words_per_entry" in SRT_OPTIONS and not isinstance(SRT_OPTIONS["max_words_per_entry"], int):
            issues.append("Warning: SRT_OPTIONS['max_words_per_entry'] should be an integer")
        if "speaker_gap_threshold" in SRT_OPTIONS and not isinstance(SRT_OPTIONS["speaker_gap_threshold"], (int, float)):
            issues.append("Warning: SRT_OPTIONS['speaker_gap_threshold'] should be a number")
    
    # Validate alignment settings
    if not isinstance(ALIGNMENT_TARGET_WORDS_PER_CHUNK, int) or ALIGNMENT_TARGET_WORDS_PER_CHUNK <= 0:
        issues.append(f"Warning: ALIGNMENT_TARGET_WORDS_PER_CHUNK should be a positive integer")
    
    if not isinstance(ALIGNMENT_MAX_WORKERS, int) or ALIGNMENT_MAX_WORKERS <= 0:
        issues.append(f"Warning: ALIGNMENT_MAX_WORKERS should be a positive integer")
    
    if not isinstance(ALIGNMENT_MIN_WORKERS, int) or ALIGNMENT_MIN_WORKERS <= 0:
        issues.append(f"Warning: ALIGNMENT_MIN_WORKERS should be a positive integer")
        
    return issues

# Run validation when config is imported
config_issues = validate_config()
for issue in config_issues:
    logging.warning(issue)
