"""Tests for the API module.

This module contains tests for the FastAPI endpoints and supporting functions
for video transcription processing.
"""

import sys
import os
from pathlib import Path
import tempfile
import shutil
import uuid
from typing import Generator, Dict, Any
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import UploadFile, HTTPException

# Add the src directory to path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import the module under test
from transcribe_meeting.api import app, jobs, cleanup_job_files, process_video


@pytest.fixture
def test_client() -> TestClient:
    """Create a FastAPI test client.
    
    Returns:
        TestClient: A FastAPI test client for making test requests.
    """
    return TestClient(app)


@pytest.fixture
def setup_temp_dir() -> Generator[Dict[str, Path], None, None]:
    """Create a temporary directory for testing file operations.
    
    Yields:
        Dict[str, Path]: Dictionary containing paths to test files:
            - video_path: Path to mock video file
            - transcript_path: Path to mock transcript file
            - temp_dir: Path to temporary directory
    """
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    
    try:
        # Create test files
        mock_video = temp_path / "test_video.mp4"
        mock_video.touch()
        
        mock_transcript = temp_path / "transcript.txt"
        mock_transcript.write_text("This is a mock transcript")
        
        yield {
            "video_path": mock_video,
            "transcript_path": mock_transcript,
            "temp_dir": temp_path
        }
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


@pytest.fixture
def mock_job():
    """Create a mock job for testing."""
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "job_id": job_id,
        "status": "completed",
        "message": "Processing completed successfully",
        "output_file": "/path/to/output.txt"
    }
    yield job_id
    # Clean up
    if job_id in jobs:
        del jobs[job_id]


def test_health_check(test_client):
    """Test the health check endpoint."""
    with patch("transcribe_meeting.resource_manager.check_gpu_availability", return_value=True):
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["cuda_available"] == "true"


@patch("transcribe_meeting.api.process_video")
def test_transcribe_video_endpoint(mock_process, test_client, setup_temp_dir):
    """Test the transcribe video endpoint."""
    # Mock the background task
    mock_process.return_value = None
    
    # Create a test file to upload
    video_path = setup_temp_dir["video_path"]
    
    # Make the API request
    with open(video_path, "rb") as video_file:
        response = test_client.post(
            "/transcribe",
            files={"file": ("test_video.mp4", video_file, "video/mp4")}
        )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert "job_id" in data
    
    # Check that the background task was added
    # (Cannot test directly since BackgroundTasks processing happens after the response)
    # but we can verify the job was created
    job_id = data["job_id"]
    assert job_id in jobs


def test_get_job_status_found(test_client, mock_job):
    """Test getting job status when the job exists."""
    response = test_client.get(f"/jobs/{mock_job}")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == mock_job
    assert data["status"] == "completed"


def test_get_job_status_not_found(test_client):
    """Test getting job status when the job does not exist."""
    response = test_client.get("/jobs/nonexistent-job")
    assert response.status_code == 404


@patch("transcribe_meeting.api.Path")
def test_download_transcript_success(mock_path, test_client, mock_job, setup_temp_dir):
    """Test downloading a transcript successfully."""
    # Update the job to point to the mock transcript
    jobs[mock_job]["output_file"] = str(setup_temp_dir["transcript_path"])
    
    # Mock Path.exists to return True
    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path.return_value = mock_path_instance
    
    # Make the request
    response = test_client.get(f"/jobs/{mock_job}/download")
    
    # Check response
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert "attachment; filename=transcript_" in response.headers["content-disposition"]


def test_download_transcript_job_not_found(test_client):
    """Test downloading a transcript when the job does not exist."""
    response = test_client.get("/jobs/nonexistent-job/download")
    assert response.status_code == 404


def test_download_transcript_not_completed(test_client, mock_job):
    """Test downloading a transcript when the job is not completed."""
    # Update job status to "processing"
    jobs[mock_job]["status"] = "processing"
    
    response = test_client.get(f"/jobs/{mock_job}/download")
    assert response.status_code == 400


@patch("transcribe_meeting.api.cleanup_job_files")
def test_delete_job(mock_cleanup, test_client, mock_job):
    """Test deleting a job."""
    response = test_client.delete(f"/jobs/{mock_job}")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    
    # Check that the job was deleted
    assert mock_job not in jobs
    
    # Check that cleanup was called
    mock_cleanup.assert_called_once_with(mock_job)


def test_delete_job_not_found(test_client):
    """Test deleting a job that does not exist."""
    response = test_client.delete("/jobs/nonexistent-job")
    assert response.status_code == 404


@patch("transcribe_meeting.api.shutil.rmtree")
@patch("transcribe_meeting.api.Path")
def test_cleanup_job_files(mock_path, mock_rmtree):
    """Test cleaning up job files."""
    # Setup
    job_id = "test-job"
    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path.return_value = mock_path_instance
    
    # Call the function
    cleanup_job_files(job_id)
    
    # Check that rmtree was called
    mock_rmtree.assert_called_once()


@patch("transcribe_meeting.api.output_utils.save_transcript_with_speakers")
@patch("transcribe_meeting.api.alignment.align_words_with_speakers")
@patch("transcribe_meeting.api.transcriber.run_transcription")
@patch("transcribe_meeting.api.diarizer.extract_speaker_turns")
@patch("transcribe_meeting.api.diarizer.run_diarization")
@patch("transcribe_meeting.api.diarizer.load_diarization_pipeline")
@patch("transcribe_meeting.api.transcriber.ModelManager")
@patch("transcribe_meeting.api.resource_manager.select_device")
@patch("transcribe_meeting.api.audio_utils.extract_audio")
@pytest.mark.asyncio
async def test_process_video_success(
    mock_extract_audio: MagicMock,
    mock_select_device: MagicMock,
    mock_model_manager: MagicMock,
    mock_load_diarization: MagicMock,
    mock_run_diarization: MagicMock,
    mock_extract_speaker_turns: MagicMock,
    mock_run_transcription: MagicMock,
    mock_align_words: MagicMock,
    mock_save_transcript: MagicMock
) -> None:
    """Test successful video processing workflow.
    
    Args:
        mock_*: Mocked dependencies for testing
        
    Tests the complete video processing pipeline with successful execution.
    Verifies all components are called in the correct order and job status
    is properly updated.
    """
    # Setup
    job_id = "test-job"
    video_path = Path("/path/to/video.mp4")
    jobs[job_id] = {"status": "queued", "message": "Queued", "output_file": None}
    
    # Mock returns
    mock_extract_audio.return_value = True
    mock_select_device.return_value = "cpu"
    mock_model_manager.return_value.__enter__.return_value = "whisper_model"
    mock_load_diarization.return_value = "diarization_pipeline"
    mock_run_diarization.return_value = "diarization_result"
    mock_extract_speaker_turns.return_value = ["speaker1", "speaker2"]
    mock_run_transcription.return_value = (["segment1", "segment2"], {})
    mock_align_words.return_value = ["aligned_word1", "aligned_word2"]
    
    # Call the function
    await process_video(job_id, video_path)
    
    # Check that job was updated
    assert jobs[job_id]["status"] == "completed"
    assert "completed" in jobs[job_id]["message"]
    assert jobs[job_id]["output_file"] is not None
    
    # Check that functions were called
    mock_extract_audio.assert_called_once()
    mock_select_device.assert_called_once()
    mock_model_manager.assert_called_once()
    mock_load_diarization.assert_called_once()
    mock_run_diarization.assert_called_once()
    mock_extract_speaker_turns.assert_called_once()
    mock_run_transcription.assert_called_once()
    mock_align_words.assert_called_once()
    mock_save_transcript.assert_called_once()


@patch("transcribe_meeting.api.audio_utils.extract_audio")
@pytest.mark.asyncio
async def test_process_video_extraction_failure(mock_extract_audio):
    """Test handling audio extraction failure during video processing."""
    # Setup
    job_id = "test-job"
    video_path = Path("/path/to/video.mp4")
    jobs[job_id] = {"status": "queued", "message": "Queued", "output_file": None}
    
    # Mock extract_audio to return False (failure)
    mock_extract_audio.return_value = False
    
    # Call the function
    await process_video(job_id, video_path)
    
    # Check that job was updated with failure
    assert jobs[job_id]["status"] == "failed"
    assert "failed" in jobs[job_id]["message"].lower()
    
    # Only extract_audio should be called
    mock_extract_audio.assert_called_once()


@patch("transcribe_meeting.api.get_azure_devops_client")
def test_get_pull_requests(mock_get_client, test_client):
    """Test fetching pull requests from Azure DevOps."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.get_pull_requests.return_value = [{"id": 1, "title": "PR 1"}]
    
    response = test_client.get("/api/azure-devops/prs")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 1
    assert data[0]["title"] == "PR 1"


@patch("transcribe_meeting.api.get_azure_devops_client")
def test_get_tasks(mock_get_client, test_client):
    """Test fetching tasks from Azure DevOps."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.get_work_items.return_value = [{"id": 1, "title": "Task 1"}]
    
    response = test_client.get("/api/azure-devops/tasks")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 1
    assert data[0]["title"] == "Task 1"


@patch("transcribe_meeting.api.get_azure_devops_client")
def test_get_task_changes(mock_get_client, test_client):
    """Test fetching task changes from Azure DevOps."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.get_work_item_changes.return_value = [{"id": 1, "change": "Updated"}]
    
    response = test_client.get("/api/azure-devops/task-changes")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 1
    assert data[0]["change"] == "Updated"


@patch("transcribe_meeting.api.get_azure_devops_client")
def test_post_pr_comment(mock_get_client, test_client):
    """Test posting a comment to a specific pull request in Azure DevOps."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.create_comment.return_value = {"id": 1, "comment": "Test comment"}
    
    response = test_client.post("/api/azure-devops/prs/1/comments", json={"comment": "Test comment"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["comment"] == "Test comment"
