# Core logic for transcribing meetings

import logging
import shutil
from pathlib import Path
from typing import Dict, Any

from . import audio_utils
from . import transcriber
from . import diarizer
from . import alignment
from . import output_utils
from . import resource_manager
from . import config

TEMP_DIR = Path(tempfile.gettempdir()) / "transcribe_meeting"
TEMP_DIR.mkdir(exist_ok=True)

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

async def process_video(job_id: str, video_path: Path, jobs: Dict[str, Dict[str, Any]]) -> None:
    """
    Process the video file asynchronously in the background.
    
    Args:
        job_id: The job identifier 
        video_path: Path to the video file
        jobs: Dictionary to store job status and metadata
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