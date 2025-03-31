import pytest
from unittest.mock import patch, MagicMock
from transcribe_meeting.file_manager import calculate_paths, create_directories, delete_temp_audio, move_video
from pathlib import Path

@patch("pathlib.Path.mkdir")
def test_create_directories_success(mock_mkdir):
    result = create_directories(["test_dir_1", "test_dir_2"])
    assert result is True

@patch("pathlib.Path.mkdir")
def test_create_directories_failure(mock_mkdir):
    mock_mkdir.side_effect = OSError("Failed to create directory")
    result = create_directories(["test_dir_1", "test_dir_2"])
    assert result is False

@patch("pathlib.Path")
def test_delete_temp_audio_success(mock_path):
    mock_path.return_value.exists.return_value = True
    mock_path.return_value.unlink.return_value = None
    delete_temp_audio("test_audio.wav")
    mock_path.return_value.unlink.assert_called_once()

@patch("pathlib.Path")
def test_delete_temp_audio_failure(mock_path):
    mock_path.return_value.exists.return_value = True
    mock_path.return_value.unlink.side_effect = Exception("Failed to delete file")
    delete_temp_audio("test_audio.wav")
    mock_path.return_value.unlink.assert_called_once()

@patch("shutil.move")
def test_move_video_success(mock_move):
    result = move_video("source_video.mp4", "dest_video.mp4")
    assert result is True

@patch("shutil.move")
def test_move_video_failure(mock_move):
    mock_move.side_effect = Exception("Failed to move file")
    result = move_video("source_video.mp4", "dest_video.mp4")
    assert result is False