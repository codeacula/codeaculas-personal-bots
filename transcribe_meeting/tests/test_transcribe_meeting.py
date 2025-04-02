"""Tests for the main transcribe_meeting module."""

import sys
import os
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock, call
from typing import Dict, Any

# Add the src directory to path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import the module under test
from transcribe_meeting import transcribe_meeting


@pytest.fixture
def mock_setup() -> Dict[str, MagicMock]:
    """Set up common mocks for tests.
    
    Returns:
        Dict[str, MagicMock]: Dictionary containing all mocked dependencies:
            - setup_logging: Mock for logging setup
            - file_manager: Mock for file operations
            - audio_utils: Mock for audio processing
            - model_manager: Mock for ML model management
            - diarizer: Mock for speaker diarization
            - transcriber: Mock for transcription
            - alignment: Mock for word alignment
            - output_utils: Mock for output handling
    """
    with patch("transcribe_meeting.transcribe_meeting.setup_logging") as mock_setup_logging, \
         patch("transcribe_meeting.transcribe_meeting.file_manager") as mock_file_manager, \
         patch("transcribe_meeting.transcribe_meeting.audio_utils") as mock_audio_utils, \
         patch("transcribe_meeting.transcribe_meeting.ModelManager") as mock_model_manager, \
         patch("transcribe_meeting.transcribe_meeting.diarizer") as mock_diarizer, \
         patch("transcribe_meeting.transcribe_meeting.transcriber") as mock_transcriber, \
         patch("transcribe_meeting.transcribe_meeting.alignment") as mock_alignment, \
         patch("transcribe_meeting.transcribe_meeting.output_utils") as mock_output_utils:
         
        # Setup mock file_manager
        mock_file_manager.calculate_paths.return_value = {
            "video_path": "/path/to/video.mp4",
            "audio_file": "/path/to/audio.wav",
            "transcript_subdir": "/path/to/transcripts",
            "output_txt_file": "/path/to/transcripts/video_transcript.txt",
            "processed_video_path": "/path/to/processed/video.mp4",
        }
        
        # Setup mock audio_utils
        mock_audio_utils.extract_audio.return_value = True
        
        # Setup mock ModelManager
        mock_model_instance = MagicMock()
        mock_model_manager.return_value.__enter__.return_value = mock_model_instance
        
        # Setup mock diarizer
        mock_diarizer.load_diarization_pipeline.return_value = "diarization_pipeline"
        mock_diarizer.run_diarization.return_value = "diarization_result"
        mock_diarizer.extract_speaker_turns.return_value = ["speaker1", "speaker2"]
        
        # Setup mock transcriber
        mock_transcriber.run_transcription.return_value = (["segment1", "segment2"], {})
        
        # Setup mock alignment
        mock_alignment.align_words_with_speakers.return_value = ["aligned_word1", "aligned_word2"]
        
        yield {
            "setup_logging": mock_setup_logging,
            "file_manager": mock_file_manager,
            "audio_utils": mock_audio_utils,
            "model_manager": mock_model_manager,
            "diarizer": mock_diarizer,
            "transcriber": mock_transcriber,
            "alignment": mock_alignment,
            "output_utils": mock_output_utils,
        }


@pytest.fixture
def mock_args() -> None:
    """Mock command line arguments for testing.
    
    Sets up sys.argv with a default test video path.
    """
    with patch("sys.argv", ["transcribe_meeting", "/path/to/video.mp4"]):
        yield


def test_setup_logging() -> None:
    """Test the setup_logging function.
    
    Verifies that logging is configured with both console and file handlers.
    """
    with patch("transcribe_meeting.transcribe_meeting.logging") as mock_logging:
        # Call the function
        transcribe_meeting.setup_logging()
        
        # Check that root logger was configured
        mock_logging.getLogger.assert_called_once()
        mock_logging.StreamHandler.assert_called_once()
        
        # Check that file handler was added
        mock_logging.RotatingFileHandler.assert_called_once()
        
        # Check that both handlers were added to the logger
        root_logger = mock_logging.getLogger.return_value
        assert root_logger.addHandler.call_count == 2


def test_main_successful_processing(mock_setup: Dict[str, MagicMock], mock_args: None) -> None:
    """Test successful end-to-end processing in the main function.
    
    Args:
        mock_setup: Dictionary of mocked dependencies
        mock_args: Mocked command line arguments
        
    Verifies that all processing steps are called in the correct order.
    """
    # Mock sys.exit to prevent the test from actually exiting
    with patch("sys.exit"):
        # Run main
        transcribe_meeting.main()
        
        # Verify the correct sequence of operations
        mock_setup["setup_logging"].assert_called_once()
        mock_setup["file_manager"].calculate_paths.assert_called_once()
        mock_setup["file_manager"].create_directories.assert_called_once()
        mock_setup["audio_utils"].extract_audio.assert_called_once()
        mock_setup["model_manager"].assert_called_once()
        mock_setup["diarizer"].load_diarization_pipeline.assert_called_once()
        mock_setup["diarizer"].run_diarization.assert_called_once()
        mock_setup["diarizer"].extract_speaker_turns.assert_called_once()
        mock_setup["transcriber"].run_transcription.assert_called_once()
        mock_setup["alignment"].align_words_with_speakers.assert_called_once()
        mock_setup["output_utils"].save_transcript_with_speakers.assert_called_once()
        
        # Check cleanup actions
        mock_setup["file_manager"].move_video.assert_called_once()
        mock_setup["file_manager"].delete_temp_audio.assert_called_once()


def test_main_file_not_found(mock_setup):
    """Test handling of file not found error."""
    with patch("sys.argv", ["transcribe_meeting", "/nonexistent/video.mp4"]), \
         patch("pathlib.Path.exists", return_value=False), \
         patch("sys.exit") as mock_exit:
        
        # Run main
        transcribe_meeting.main()
        
        # Should exit with error
        mock_exit.assert_called_once_with(1)
        
        # Should not proceed to processing
        mock_setup["file_manager"].create_directories.assert_not_called()
        mock_setup["audio_utils"].extract_audio.assert_not_called()


def test_main_audio_extraction_failure(mock_setup, mock_args):
    """Test handling of audio extraction failure."""
    # Setup audio extraction to fail
    mock_setup["audio_utils"].extract_audio.return_value = False
    
    with patch("sys.exit") as mock_exit:
        # Run main
        transcribe_meeting.main()
        
        # Should exit with error
        mock_exit.assert_called_once_with(1)
        
        # Should not proceed to model loading
        mock_setup["model_manager"].__enter__.assert_not_called()


def test_main_diarization_failure(mock_setup, mock_args):
    """Test handling of diarization failure."""
    # Setup diarization to fail
    mock_setup["diarizer"].run_diarization.return_value = None
    
    # Run main, it should catch the ValueError
    result = transcribe_meeting.main()
    
    # Should return False to indicate failure
    assert result is False
    
    # Should not move the video or delete audio on failure
    mock_setup["file_manager"].move_video.assert_not_called()
    mock_setup["file_manager"].delete_temp_audio.assert_not_called()


def test_main_with_verbose_flag(mock_setup):
    """Test main function with verbose flag."""
    with patch("sys.argv", ["transcribe_meeting", "/path/to/video.mp4", "--verbose"]), \
         patch("sys.exit"):
        
        # Run main
        transcribe_meeting.main()
        
        # Should set up logging with DEBUG level
        mock_setup["setup_logging"].assert_has_calls([
            call(),  # First call with default level
            call(level=10)  # Second call with DEBUG level (10)
        ])


def test_main_handles_exception(mock_setup, mock_args):
    """Test that main handles exceptions gracefully."""
    # Setup diarizer to raise an exception
    mock_setup["diarizer"].load_diarization_pipeline.side_effect = Exception("Test error")
    
    with patch("transcribe_meeting.transcribe_meeting.logging.exception") as mock_log_exception:
        # Run main
        result = transcribe_meeting.main()
        
        # Should log the exception
        mock_log_exception.assert_called_once()
        
        # Should return False to indicate failure
        assert result is False
        
        # Should not clean up on failure
        mock_setup["file_manager"].move_video.assert_not_called()