import pytest
from unittest.mock import patch, MagicMock
import torch
from transcribe_meeting.diarizer import load_diarization_pipeline, run_diarization, extract_speaker_turns

@patch("transcribe_meeting.diarizer.Pipeline.from_pretrained")
def test_load_diarization_pipeline_success(mock_from_pretrained):
    mock_pipeline = MagicMock()
    mock_from_pretrained.return_value = mock_pipeline
    result = load_diarization_pipeline("test-pipeline", "test-token")
    assert result == mock_pipeline

@patch("transcribe_meeting.diarizer.Pipeline.from_pretrained")
def test_load_diarization_pipeline_failure(mock_from_pretrained):
    mock_from_pretrained.side_effect = Exception("Failed to load pipeline")
    result = load_diarization_pipeline("test-pipeline", "test-token")
    assert result is None

@patch("transcribe_meeting.diarizer.Pipeline")
def test_run_diarization_success(mock_pipeline):
    mock_pipeline.return_value = MagicMock()
    mock_pipeline.return_value.__call__.return_value = "diarization-result"
    result = run_diarization(mock_pipeline.return_value, "test-audio.wav")
    assert result == "diarization-result"

def test_run_diarization_failure(mock_pipeline):
    mock_pipeline.return_value = MagicMock()
    mock_pipeline.return_value.__call__.side_effect = Exception("Diarization failed")
    result = run_diarization(mock_pipeline.return_value, "test-audio.wav")
    assert result is None

def test_extract_speaker_turns():
    diarization_result = MagicMock()
    diarization_result.itertracks.return_value = [
        (MagicMock(start=0.0, end=1.0), None, "SPEAKER_1"),
        (MagicMock(start=1.0, end=2.0), None, "SPEAKER_2")
    ]
    result = extract_speaker_turns(diarization_result)
    expected = [
        {"start": 0.0, "end": 1.0, "speaker": "SPEAKER_1"},
        {"start": 1.0, "end": 2.0, "speaker": "SPEAKER_2"}
    ]
    assert result == expected

@patch('torch.cuda.is_available')
@patch("transcribe_meeting.diarizer.Pipeline.from_pretrained")
def test_load_diarization_pipeline_with_gpu(mock_from_pretrained, mock_cuda_available):
    mock_pipeline = MagicMock()
    mock_from_pretrained.return_value = mock_pipeline
    mock_cuda_available.return_value = True
    
    result = load_diarization_pipeline("test-pipeline", "test-token")
    
    assert result == mock_pipeline
    mock_pipeline.to.assert_called_once_with(torch.device("cuda"))

@patch('torch.cuda.is_available')
@patch("transcribe_meeting.diarizer.Pipeline.from_pretrained")
def test_load_diarization_pipeline_without_gpu(mock_from_pretrained, mock_cuda_available):
    mock_pipeline = MagicMock()
    mock_from_pretrained.return_value = mock_pipeline
    mock_cuda_available.return_value = False
    
    result = load_diarization_pipeline("test-pipeline", "test-token")
    
    assert result == mock_pipeline
    mock_pipeline.to.assert_not_called()

def test_run_diarization_with_none_pipeline():
    result = run_diarization(None, "test-audio.wav")
    assert result is None

def test_extract_speaker_turns_with_none_result():
    result = extract_speaker_turns(None)
    assert result == []

def test_extract_speaker_turns_with_error():
    diarization_result = MagicMock()
    diarization_result.itertracks.side_effect = Exception("Error processing tracks")
    result = extract_speaker_turns(diarization_result)
    assert result == []

def test_extract_speaker_turns_with_unsorted_speakers():
    diarization_result = MagicMock()
    diarization_result.itertracks.return_value = [
        (MagicMock(start=1.0, end=2.0), None, "SPEAKER_2"),
        (MagicMock(start=0.0, end=1.0), None, "SPEAKER_1"),
        (MagicMock(start=2.0, end=3.0), None, "SPEAKER_1")
    ]
    result = extract_speaker_turns(diarization_result)
    expected = [
        {"start": 0.0, "end": 1.0, "speaker": "SPEAKER_1"},
        {"start": 1.0, "end": 2.0, "speaker": "SPEAKER_2"},
        {"start": 2.0, "end": 3.0, "speaker": "SPEAKER_1"}
    ]
    assert result == expected