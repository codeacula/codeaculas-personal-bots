"""
API endpoints for the transcribe_meeting package using FastAPI.

This module provides asynchronous REST API endpoints for transcription services.
"""

import uuid
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .core import process_video, cleanup_job_files


app = FastAPI(
    title="Transcribe Meeting API",
    description="API for transcribing and diarizing meeting recordings",
    version="0.1.0",
)

# Directory to store temporary files
TEMP_DIR = Path(tempfile.gettempdir()) / "transcribe_meeting"
TEMP_DIR.mkdir(exist_ok=True)

# Storage for background job status
jobs: Dict[str, Dict[str, Any]] = {}


class TranscriptionJob(BaseModel):
    """Model for transcription job information."""
    job_id: str
    status: str  # "queued", "processing", "completed", "failed"
    message: Optional[str] = None
    output_file: Optional[str] = None


@app.post("/transcribe", response_model=TranscriptionJob)
async def transcribe_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
) -> TranscriptionJob:
    """Upload a video file and start a transcription job.
    
    Args:
        background_tasks: FastAPI background tasks handler
        file: The uploaded video file
        
    Returns:
        TranscriptionJob: Job status information
    """
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    job_dir = TEMP_DIR / job_id
    job_dir.mkdir(exist_ok=True)
    
    # Save uploaded file
    video_path = job_dir / file.filename
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create job record
    jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "message": "Job queued for processing",
        "output_file": None
    }
    
    # Process in background
    background_tasks.add_task(process_video, job_id, video_path, jobs)
    
    return TranscriptionJob(**jobs[job_id])


@app.get("/jobs/{job_id}", response_model=TranscriptionJob)
async def get_job_status(job_id: str) -> TranscriptionJob:
    """Get the status of a transcription job.
    
    Args:
        job_id: The job identifier
        
    Returns:
        TranscriptionJob: Job status information
        
    Raises:
        HTTPException: If the job is not found
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return TranscriptionJob(**jobs[job_id])


@app.get("/jobs/{job_id}/download")
async def download_transcript(job_id: str):
    """Download the transcript for a completed job.
    
    Args:
        job_id: The job identifier
        
    Returns:
        FileResponse: The transcript file
        
    Raises:
        HTTPException: If the job is not found or not completed
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    job = jobs[job_id]
    if job["status"] != "completed" or not job["output_file"]:
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} is not completed or has no output file"
        )
    
    output_file = Path(job["output_file"])
    if not output_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Output file for job {job_id} not found"
        )
    
    return FileResponse(
        path=output_file,
        media_type="text/plain",
        filename=f"transcript_{job_id}.txt"
    )


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str) -> Dict[str, str]:
    """Delete a job and its associated files.
    
    Args:
        job_id: The job identifier
        
    Returns:
        Dict with a success message
        
    Raises:
        HTTPException: If the job is not found
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    # Clean up files
    cleanup_job_files(job_id)
    
    # Remove job from dictionary
    del jobs[job_id]
    
    return {"message": f"Job {job_id} deleted successfully"}


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Check API health status.
    
    Returns:
        Dict with status information
    """
    return {
        "status": "healthy",
        "version": "0.1.0"
    }