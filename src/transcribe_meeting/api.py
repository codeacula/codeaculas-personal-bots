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

from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import audio_utils
from . import transcriber
from . import diarizer
from . import alignment
from . import output_utils
from . import resource_manager
from . import config

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


def cleanup_job_files(job_id: str) -> None:
    """
    Clean up temporary files for a completed job.
    
    Args:
        job_id: The job ID to clean up
    """
    job_dir = TEMP_DIR / job_id
    if job_dir.exists():
        try:
            shutil.rmtree(job_dir)
            logging.info(f"Cleaned up job directory: {job_dir}")
        except Exception as e:
            logging.error(f"Error cleaning up job directory {job_dir}: {e}")


async def process_video(job_id: str, video_path: Path) -> None:
    """
    Process the video file asynchronously in the background.
    
    Args:
        job_id: The job identifier 
        video_path: Path to the video file
    """
    jobs[job_id]["status"] = "processing"
    jobs[job_id]["message"] = "Processing started"
    
    job_dir = TEMP_DIR / job_id
    job_dir.mkdir(exist_ok=True)
    
    audio_path = job_dir / "audio.wav"
    output_path = job_dir / "transcript.txt"
    
    try:
        # Extract audio
        if not audio_utils.extract_audio(video_path, audio_path):
            raise RuntimeError("Failed to extract audio from video")
        
        # Load models
        device = resource_manager.select_device()
        
        # Use Whisper model
        with transcriber.ModelManager(
            config.WHISPER_MODEL_SIZE, 
            device,
            config.WHISPER_COMPUTE_TYPE
        ) as whisper_model:
            if whisper_model is None:
                raise RuntimeError("Failed to load Whisper model")
                
            # Load diarization pipeline
            diarization_pipeline = diarizer.load_diarization_pipeline(
                config.DIARIZATION_PIPELINE_NAME, 
                config.HUGGINGFACE_AUTH_TOKEN
            )
            if diarization_pipeline is None:
                raise RuntimeError("Failed to load diarization pipeline")
                
            # Run diarization
            diarization_result = diarizer.run_diarization(diarization_pipeline, audio_path)
            if diarization_result is None:
                raise RuntimeError("Diarization failed")
                
            speaker_turns = diarizer.extract_speaker_turns(diarization_result)
            
            # Run transcription
            raw_segments, _ = transcriber.run_transcription(whisper_model, audio_path)
            if raw_segments is None:
                raise RuntimeError("Transcription failed")
                
            segments_list = list(raw_segments)
            
            # Align speakers with words
            aligned_words = alignment.align_words_with_speakers(segments_list, speaker_turns)
            
            # Save transcript
            output_utils.save_transcript_with_speakers(aligned_words, output_path)
            
            # Update job status
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["message"] = "Processing completed successfully"
            jobs[job_id]["output_file"] = str(output_path)
            
    except Exception as e:
        logging.exception(f"Error processing job {job_id}: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = f"Processing failed: {str(e)}"
        
    finally:
        # Clean up resources
        resource_manager.cleanup_gpu_memory()


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
    background_tasks.add_task(process_video, job_id, video_path)
    
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