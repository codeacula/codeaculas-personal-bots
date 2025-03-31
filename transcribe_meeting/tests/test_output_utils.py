import pytest
from unittest.mock import patch, mock_open
from transcribe_meeting.output_utils import format_srt_time, save_to_txt, save_to_srt

# Test format_srt_time
def test_format_srt_time():
    assert format_srt_time(3661.123) == "01:01:01,123"
    assert format_srt_time(0) == "00:00:00,000"
    assert format_srt_time(None) == "00:00:00,000"

# Test save_to_txt
@patch("builtins.open", new_callable=mock_open)
def test_save_to_txt(mock_file):
    aligned_words = [
        {"text": "Hello", "speaker": "SPEAKER_1"},
        {"text": "world", "speaker": "SPEAKER_1"}
    ]
    result = save_to_txt(aligned_words, "test.txt")
    assert result is True
    mock_file.assert_called_once_with("test.txt", "w", encoding="utf-8")

# Test save_to_srt
@patch("builtins.open", new_callable=mock_open)
def test_save_to_srt(mock_file):
    aligned_words = [
        {"start": 0.0, "end": 1.0, "text": "Hello", "speaker": "SPEAKER_1"},
        {"start": 1.1, "end": 2.0, "text": "world", "speaker": "SPEAKER_1"}
    ]
    srt_options = {"max_line_length": 42, "max_words_per_entry": 10, "speaker_gap_threshold": 1.0}
    result = save_to_srt(aligned_words, "test.srt", srt_options)
    assert result is True
    mock_file.assert_called_once_with("test.srt", "w", encoding="utf-8")