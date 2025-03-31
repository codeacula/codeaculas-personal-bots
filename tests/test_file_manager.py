"""Tests for the file_manager module."""

import os
import shutil
import tempfile
from pathlib import Path
import pytest
import sys
import datetime

# Add the src directory to path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from transcribe_meeting.file_manager import (
    calculate_paths,
    create_directories,
    delete_temp_audio,
    move_video,
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    tmp_dir = tempfile.mkdtemp()
    yield Path(tmp_dir)
    # Clean up after the test
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

def test_calculate_paths(temp_dir, monkeypatch):
    """Test that calculate_paths returns the expected file paths."""
    # Setup
    video_path = temp_dir / "test_video.mp4"
    repo_root = temp_dir / "repo_root"
    transcript_base_dir_name = "transcripts"
    processed_video_dir = temp_dir / "processed"
    
    # Create the test file
    video_path.touch()
    
    # Mock datetime.datetime.now to return a fixed date
    fixed_date = datetime.datetime(2023, 5, 15)
    monkeypatch.setattr(datetime, "datetime", type('datetime', (), {
        'now': lambda: fixed_date
    }))
    
    # Execute
    paths = calculate_paths(
        video_path, 
        repo_root, 
        transcript_base_dir_name, 
        processed_video_dir
    )
    
    # Assert
    assert paths["video_path"] == video_path
    assert paths["base_name"] == "test_video"
    assert paths["video_dir"] == temp_dir
    assert paths["audio_file"] == temp_dir / "test_video_audio.wav"
    assert paths["transcript_subdir"] == repo_root / transcript_base_dir_name / "2023" / "05"
    assert paths["output_txt_file"] == paths["transcript_subdir"] / "test_video_transcript_speakers.txt"
    assert paths["processed_video_path"] == processed_video_dir / "test_video.mp4"

def test_create_directories(temp_dir):
    """Test directory creation functionality."""
    # Setup
    paths = {
        "transcript_subdir": temp_dir / "transcripts" / "2023" / "01"
    }
    
    # Execute
    create_directories(paths)
    
    # Assert
    assert (temp_dir / "transcripts" / "2023" / "01").exists()

def test_delete_temp_audio(temp_dir):
    """Test temporary audio file deletion."""
    # Setup
    audio_path = temp_dir / "temp_audio.wav"
    audio_path.touch()
    
    # Verify the file exists
    assert audio_path.exists()
    
    # Execute
    delete_temp_audio(audio_path)
    
    # Assert the file was deleted
    assert not audio_path.exists()

def test_move_video(temp_dir):
    """Test video file moving functionality."""
    # Setup
    source_path = temp_dir / "source_dir"
    source_path.mkdir()
    video_file = source_path / "test_video.mp4"
    video_file.touch()
    
    dest_dir = temp_dir / "dest_dir"
    dest_dir.mkdir(parents=True)
    dest_path = dest_dir / "moved_video.mp4"
    
    # Execute
    result = move_video(video_file, dest_path)
    
    # Assert
    assert result is True
    assert not video_file.exists()
    assert dest_path.exists()