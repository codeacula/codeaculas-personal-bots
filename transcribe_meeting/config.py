# config.py
# Configuration settings for the transcription process

import os

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