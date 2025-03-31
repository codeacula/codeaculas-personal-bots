"""Tests for the audio_utils module."""

import sys
import os
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add the src directory to path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import the module under test - this depends on how your audio_utils module is structured
# You may need to adjust this import
try:
    from transcribe_meeting import audio_utils
except ImportError:
    # Fallback if the module structure is different
    from transcribe_meeting.audio_utils import extract_audio


class TestAudioUtils:
    """Test cases for audio utilities."""

    @patch("transcribe_meeting.audio_utils.ffmpeg")
    def test_extract_audio_success(self, mock_ffmpeg):
        """Test successful audio extraction."""
        # Setup mock
        mock_ffmpeg.input.return_value = mock_ffmpeg
        mock_ffmpeg.output.return_value = mock_ffmpeg
        mock_ffmpeg.global_args.return_value = mock_ffmpeg
        mock_ffmpeg.overwrite_output.return_value = mock_ffmpeg
        mock_ffmpeg.run.return_value = (b"", b"")  # stdout, stderr
        
        # Call the function
        result = extract_audio("input.mp4", "output.wav")
        
        # Assertions
        assert result is True
        mock_ffmpeg.input.assert_called_once_with("input.mp4")
        mock_ffmpeg.output.assert_called_once()
        mock_ffmpeg.overwrite_output.assert_called_once()
        mock_ffmpeg.run.assert_called_once()

    @patch("transcribe_meeting.audio_utils.ffmpeg")
    def test_extract_audio_raises_exception(self, mock_ffmpeg):
        """Test handling of exceptions during audio extraction."""
        # Setup mock to raise an exception
        mock_ffmpeg.input.return_value = mock_ffmpeg
        mock_ffmpeg.output.return_value = mock_ffmpeg
        mock_ffmpeg.global_args.return_value = mock_ffmpeg
        mock_ffmpeg.overwrite_output.return_value = mock_ffmpeg
        mock_ffmpeg.run.side_effect = Exception("FFmpeg error")
        
        # Call the function
        result = extract_audio("input.mp4", "output.wav")
        
        # Assertions
        assert result is False
        mock_ffmpeg.run.assert_called_once()

    @patch("transcribe_meeting.audio_utils.ffmpeg")
    def test_extract_audio_with_specific_params(self, mock_ffmpeg):
        """Test audio extraction with specific parameters."""
        # Setup mock
        mock_ffmpeg.input.return_value = mock_ffmpeg
        mock_ffmpeg.output.return_value = mock_ffmpeg
        mock_ffmpeg.global_args.return_value = mock_ffmpeg
        mock_ffmpeg.overwrite_output.return_value = mock_ffmpeg
        mock_ffmpeg.run.return_value = (b"", b"")  # stdout, stderr
        
        # Call the function with specific params (assuming your extract_audio supports these)
        # If it doesn't, you might need to adjust this test
        result = extract_audio(
            "input.mp4", 
            "output.wav", 
            sample_rate=16000,
            channels=1
        )
        
        # Assertions
        assert result is True
        mock_ffmpeg.input.assert_called_once_with("input.mp4")
        # Check that output was called with the right parameters
        # This test might need adjustment depending on your actual implementation
        mock_ffmpeg.output.assert_called_once()
        mock_ffmpeg.run.assert_called_once()

    @patch("transcribe_meeting.audio_utils.ffmpeg")
    def test_extract_audio_input_not_found(self, mock_ffmpeg):
        """Test handling of non-existent input file."""
        # Setup mock
        mock_ffmpeg.input.return_value = mock_ffmpeg
        mock_ffmpeg.output.return_value = mock_ffmpeg
        mock_ffmpeg.global_args.return_value = mock_ffmpeg
        mock_ffmpeg.overwrite_output.return_value = mock_ffmpeg
        mock_ffmpeg.run.side_effect = FileNotFoundError("Input file not found")
        
        # Call the function
        result = extract_audio("nonexistent.mp4", "output.wav")
        
        # Assertions
        assert result is False