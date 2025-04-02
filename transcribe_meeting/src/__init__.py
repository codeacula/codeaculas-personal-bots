"""
Initialize the transcribe_meeting package.

This module re-exports key components for easier imports.
"""

# Re-export core functionality
from .core import process_video, cleanup_job_files
from .transcriber import ModelManager
from .diarizer import load_diarization_pipeline, run_diarization, extract_speaker_turns
from .audio_utils import extract_audio
from .alignment import align_words_with_speakers
from .output_utils import save_transcript_with_speakers
from .resource_manager import select_device, cleanup_gpu_memory

# Add version information
__version__ = "0.1.0"
