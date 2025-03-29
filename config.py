# config.py
# Configuration settings for the transcription process

import os

# --- Model/Device Settings ---
WHISPER_MODEL_SIZE = "large-v3" # "tiny.en", "base.en", ..., "large-v3"
WHISPER_DEVICE = "cuda"         # "cuda" or "cpu"
WHISPER_COMPUTE_TYPE = "float16" # "float16", "int8_float16", "int8"

DIARIZATION_PIPELINE_NAME = "pyannote/speaker-diarization-3.1"
# Optional: Set Hugging Face token here if not using CLI login
# HUGGINGFACE_AUTH_TOKEN = "hf_YOUR_TOKEN_HERE"
HUGGINGFACE_AUTH_TOKEN = None # Set to None to rely on CLI login

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