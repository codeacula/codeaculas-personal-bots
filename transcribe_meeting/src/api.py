"""
API endpoints for the transcribe_meeting package using FastAPI.

This module provides asynchronous REST API endpoints for transcription services.
"""

import os
import uuid
import tempfile
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException, APIRouter, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

from . import audio_utils
from . import transcriber
from . import diarizer
from . import alignment
from . import output_utils
from . import resource_manager
from . import config
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
    background_tasks: BackgroundTasks, file: UploadFile = File(...)
) -> TranscriptionJob:
    """
    Upload a video file and start a transcription job.
    
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
    """
    Get the status of a transcription job.
    
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
    """
    Download the transcript for a completed job.
    
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
    """
    Delete a job and its associated files.
    
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
    """
    Check API health status.
    
    Returns:
        Dict with status information
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
        "cuda_available": "true" if resource_manager.check_gpu_availability() else "false"
    }

# Azure DevOps Router
azure_devops_router = APIRouter()

# Azure DevOps Client
def get_azure_devops_client():
    personal_access_token = os.getenv("AZURE_DEVOPS_PAT")
    organization_url = os.getenv("AZURE_DEVOPS_ORG_URL")
    credentials = BasicAuthentication('', personal_access_token)
    connection = Connection(base_url=organization_url, creds=credentials)
    return connection.clients.get_git_client()

@azure_devops_router.get("/azure-devops/prs")
async def get_pull_requests(request: Request):
    """
    Get pull requests from Azure DevOps.
    
    Args:
        request: FastAPI request object
        
    Returns:
        List of pull requests
    """
    client = get_azure_devops_client()
    project = os.getenv("AZURE_DEVOPS_PROJECT")
    prs = client.get_pull_requests(project)
    return prs

@azure_devops_router.get("/azure-devops/tasks")
async def get_tasks(request: Request):
    """
    Get tasks from Azure DevOps.
    
    Args:
        request: FastAPI request object
        
    Returns:
        List of tasks
    """
    client = get_azure_devops_client()
    project = os.getenv("AZURE_DEVOPS_PROJECT")
    tasks = client.get_work_items(project)
    return tasks

@azure_devops_router.get("/azure-devops/task-changes")
async def get_task_changes(request: Request):
    """
    Get task changes from Azure DevOps.
    
    Args:
        request: FastAPI request object
        
    Returns:
        List of task changes
    """
    client = get_azure_devops_client()
    project = os.getenv("AZURE_DEVOPS_PROJECT")
    task_changes = client.get_work_item_changes(project)
    return task_changes

@azure_devops_router.post("/azure-devops/prs/{pr_id}/comments")
async def post_pr_comment(pr_id: int, comment: str):
    """
    Post a comment to a specific pull request in Azure DevOps.
    
    Args:
        pr_id: Pull request ID
        comment: Comment text
        
    Returns:
        Response from Azure DevOps
    """
    client = get_azure_devops_client()
    project = os.getenv("AZURE_DEVOPS_PROJECT")
    response = client.create_comment(project, pr_id, comment)
    return response

app.include_router(azure_devops_router, prefix="/api")
