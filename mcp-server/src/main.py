from fastapi import FastAPI, UploadFile, BackgroundTasks, HTTPException
from pathlib import Path
from transcribe_meeting import process_video, cleanup_job_files
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid
import tempfile


app = FastAPI(
    title="MCP Server",
    description="MCP Server for exposing transcription services",
    version="0.1.0",
)


# Directory to store temporary files
TEMP_DIR = Path(tempfile.gettempdir()) / "mcp_server"
TEMP_DIR.mkdir(exist_ok=True)

# Storage for background job status
jobs: Dict[str, Dict[str, Any]] = {}


class TranscriptionJob(BaseModel):
    job_id: str
    status: str
    message: str
    output_file: Optional[str] = None


@app.post("/mcp/transcribe", response_model=TranscriptionJob)
async def transcribe(background_tasks: BackgroundTasks, file: UploadFile):
    job_id = str(uuid.uuid4())
    job_dir = TEMP_DIR / job_id
    job_dir.mkdir(exist_ok=True)

    video_path = job_dir / file.filename
    with open(video_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "message": "Job queued for processing",
        "output_file": None,
    }

    background_tasks.add_task(process_video, job_id, video_path, jobs)

    return TranscriptionJob(**jobs[job_id])


@app.get("/mcp/jobs/{job_id}", response_model=TranscriptionJob)
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return TranscriptionJob(**jobs[job_id])


@app.delete("/mcp/jobs/{job_id}")
async def delete_job(job_id: str):
    if job_id not in jobs:
        return {"error": "Job not found"}

    cleanup_job_files(job_id)
    del jobs[job_id]
    return {"message": f"Job {job_id} deleted successfully"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}