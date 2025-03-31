"""
Transcribe Meeting - A package for transcribing and diarizing meeting recordings.

This package provides tools for audio extraction, transcription, speaker diarization,
and subtitle generation from video recordings of meetings.
"""

__version__ = "0.1.0"

# Import key modules for easy access
from transcribe_meeting.audio_utils import extract_audio
from transcribe_meeting.diarizer import (
    load_diarization_pipeline,
    run_diarization,
    extract_speaker_turns
)
from transcribe_meeting.file_manager import (
    calculate_paths,
    create_directories,
    delete_temp_audio,
    move_video
)
from transcribe_meeting.alignment import align_words_with_speakers

# Define what's available for import with "from transcribe_meeting import *"
__all__ = [
    'extract_audio',
    'load_diarization_pipeline', 
    'run_diarization',
    'extract_speaker_turns',
    'calculate_paths',
    'create_directories',
    'delete_temp_audio',
    'move_video',
    'align_words_with_speakers',
]
