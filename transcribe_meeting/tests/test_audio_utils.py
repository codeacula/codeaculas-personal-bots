import subprocess
import pytest
from transcribe_meeting.audio_utils import extract_audio
from unittest.mock import patch

@patch("subprocess.run")
def test_extract_audio_success(mock_subprocess):
    mock_subprocess.return_value.returncode = 0
    result = extract_audio("test_video.mp4", "output_audio.wav")
    assert result is True

@patch("subprocess.run")
def test_extract_audio_ffmpeg_not_found(mock_subprocess):
    mock_subprocess.side_effect = FileNotFoundError
    result = extract_audio("test_video.mp4", "output_audio.wav")
    assert result is False

@patch("subprocess.run")
def test_extract_audio_failure(mock_subprocess):
    mock_subprocess.side_effect = subprocess.CalledProcessError(1, "ffmpeg")
    result = extract_audio("test_video.mp4", "output_audio.wav")
    assert result is False