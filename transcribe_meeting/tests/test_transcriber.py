import pytest
from unittest.mock import patch, MagicMock
from transcribe_meeting.transcriber import ModelManager, load_whisper_model, run_transcription

@patch("transcribe_meeting.transcriber.WhisperModel")
def test_model_manager_success(mock_whisper_model):
    with ModelManager("large-v3", "cuda", "float16") as model:
        assert model == mock_whisper_model.return_value

@patch("transcribe_meeting.transcriber.WhisperModel")
def test_model_manager_failure(mock_whisper_model):
    mock_whisper_model.side_effect = Exception("Failed to load model")
    with ModelManager("large-v3", "cuda", "float16") as model:
        assert model is None

@patch("transcribe_meeting.transcriber.WhisperModel")
def test_load_whisper_model_success(mock_whisper_model):
    result = load_whisper_model("large-v3", "cuda", "float16")
    assert result == mock_whisper_model.return_value

@patch("transcribe_meeting.transcriber.WhisperModel")
def test_load_whisper_model_failure(mock_whisper_model):
    mock_whisper_model.side_effect = Exception("Failed to load model")
    result = load_whisper_model("large-v3", "cuda", "float16")
    assert result is None

@patch("transcribe_meeting.transcriber.BatchedInferencePipeline")
def test_run_transcription_success(mock_pipeline):
    mock_pipeline.return_value.transcribe.return_value = ("segments", MagicMock(language="en", language_probability=0.95))
    result = run_transcription(mock_pipeline, "test_audio.wav")
    assert result == ("segments", mock_pipeline.return_value.transcribe.return_value[1])

@patch("transcribe_meeting.transcriber.BatchedInferencePipeline")
def test_run_transcription_failure(mock_pipeline):
    mock_pipeline.return_value.transcribe.side_effect = Exception("Transcription failed")
    result = run_transcription(mock_pipeline, "test_audio.wav")
    assert result == (None, None)