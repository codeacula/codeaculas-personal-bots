# transcribe_meeting_script.py
# Main script for automatic transcription and diarization of video files

import logging
import argparse
import os
import sys
from pathlib import Path
import time
from logging.handlers import RotatingFileHandler
from transcribe_meeting.transcriber import ModelManager
# Add missing import from pyannote.audio
from pyannote.audio import Pipeline

# Use absolute imports instead of relative imports
from transcribe_meeting import config
from transcribe_meeting import audio_utils
from transcribe_meeting import diarizer
from transcribe_meeting import transcriber
from transcribe_meeting import alignment
from transcribe_meeting import output_utils
from transcribe_meeting import file_manager
from transcribe_meeting import resource_manager
from transcribe_meeting import git_utils

# Set environment variables to disable symlinks in Hugging Face Hub
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

def setup_logging(log_level: int = logging.INFO) -> None:
    """
    Configure logging with formatters and handlers for console and rotating log files.
    
    Args:
        log_level: The logging level to use (default: logging.INFO)
    """
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers if any
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # Add rotating file handler for persistent logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    file_handler = RotatingFileHandler(
        log_dir / "transcribe.log", 
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(log_level)
    root_logger.addHandler(file_handler)
    
    logging.info("Logging initialized with console and file output")

def check_and_get_huggingface_token() -> str:
    """
    Check for Hugging Face token in environment variables or prompt user to enter it.
    
    Returns:
        The Hugging Face authentication token
    """
    token = os.environ.get("HUGGINGFACE_AUTH_TOKEN")
    if not token:
        logging.warning("HUGGINGFACE_AUTH_TOKEN environment variable is not set")
        print("\n" + "="*80)
        print("You need a Hugging Face authentication token to use this tool.")
        print("1. Sign up or log in at https://huggingface.co/")
        print("2. Go to https://huggingface.co/settings/tokens to create a token")
        print("3. Accept the terms for pyannote/speaker-diarization at:")
        print("   https://huggingface.co/pyannote/speaker-diarization")
        print("="*80 + "\n")
        
        token = input("Please enter your Hugging Face authentication token: ").strip()
        if token:
            # Temporarily set the environment variable for this session
            os.environ["HUGGINGFACE_AUTH_TOKEN"] = token
            print("\nToken accepted for this session. For future use, please set the HUGGINGFACE_AUTH_TOKEN environment variable.")
        else:
            raise ValueError("No Hugging Face authentication token provided. Cannot continue.")
    
    return token

def main():
    # Setup logging first thing
    setup_logging()
    
    # --- 1. Parse Arguments ---
    parser = argparse.ArgumentParser(description="Transcribe and diarize a video file.")
    parser.add_argument("video_file_path", help="Path to the video file to process.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose (debug) logging")
    args = parser.parse_args()
    
    # Set debug level if requested
    if args.verbose:
        setup_logging(logging.DEBUG)
        logging.debug("Debug logging enabled")
    
    video_path = args.video_file_path

    if not Path(video_path).exists(): 
        logging.error(f"Video file not found at '{video_path}'")
        sys.exit(1)

    # --- 2. Calculate Paths & Create Directories ---
    paths = file_manager.calculate_paths(
        video_path, config.REPO_ROOT, config.TRANSCRIPT_BASE_DIR_NAME, config.PROCESSED_VIDEO_DIR
    )
    logging.info(f"Processing video: {video_path}")
    logging.info(f"  Intermediate audio: {paths['audio_file']}")
    logging.info(f"  Output directory: {paths['transcript_subdir']}")
    if paths['processed_video_path']: 
        logging.info(f"  Processed video will move to: {paths['processed_video_path']}")
        
    try:
        file_manager.create_directories(paths)
    except Exception as e:
        logging.error(f"Could not create essential directories. Error: {e}")
        sys.exit(1)

    # --- 3. Extract Audio ---
    if not audio_utils.extract_audio(video_path, str(paths['audio_file'])): 
        logging.error("Exiting: audio extraction failure.")
        sys.exit(1)

    # --- Main Processing Block ---
    processing_successful = False
    # Keep variables in scope until main() ends
    diarization_pipeline = None
    aligned_words = None
    speaker_turns = []
    segments_list = []

    try:
        # --- 4. Load Models ---
        # Use the ModelManager context manager for the Whisper model
        with ModelManager(
            config.WHISPER_MODEL_SIZE, 
            config.WHISPER_DEVICE, 
            config.WHISPER_COMPUTE_TYPE
        ) as whisper_model:
            if whisper_model is None:
                raise ValueError("Failed to load Whisper model.")
                
            # Check for Hugging Face token
            try:
                HUGGINGFACE_AUTH_TOKEN = check_and_get_huggingface_token()
            except ValueError as e:
                logging.error(str(e))
                sys.exit(1)

            # Retry logic for loading the diarization pipeline
            MAX_RETRIES = 3
            RETRY_DELAY = 5  # seconds

            logging.info("Loading diarization pipeline with Hugging Face token...")
            diag_pipeline_loaded = False
            for attempt in range(MAX_RETRIES):
                try:
                    diarization_pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization@2.1", use_auth_token=HUGGINGFACE_AUTH_TOKEN
                    )
                    logging.info("Speaker diarization pipeline loaded successfully.")
                    diag_pipeline_loaded = True
                    break
                except Exception as e:
                    logging.error(
                        "Attempt %d: Error loading diarization pipeline: %s", attempt + 1, str(e)
                    )
                    if attempt < MAX_RETRIES - 1:
                        logging.info("Retrying in %d seconds...", RETRY_DELAY)
                        time.sleep(RETRY_DELAY)

            if not diag_pipeline_loaded:
                raise ValueError("Failed to load diarization pipeline after multiple attempts.")

            # --- 5. Run Diarization ---
            diarization_result = diarizer.run_diarization(diarization_pipeline, str(paths['audio_file']))
            if diarization_result is None: 
                raise ValueError("Diarization failed.")
            speaker_turns = diarizer.extract_speaker_turns(diarization_result)

            # --- 6. Run Transcription & Materialize Results ---
            raw_segments, info = transcriber.run_transcription(whisper_model, str(paths['audio_file']))
            if raw_segments is None: 
                raise ValueError("Transcription failed.")
            
            logging.info("Materializing transcript segments into list (might trigger GPU access)...")
            start_materialize = time.time()
            segments_list = list(raw_segments)
            logging.debug(f"Materialization completed in {time.time() - start_materialize:.2f} seconds")
            
            # --- 7. Align Speakers with Words ---
            logging.info("Aligning speakers with transcribed words...")
            aligned_words = alignment.align_words_with_speakers(segments_list, speaker_turns)
            
            # --- 8. Generate Output Files ---
            logging.info(f"Saving transcript to {paths['output_txt_file']}")
            output_utils.save_transcript_with_speakers(aligned_words, paths['output_txt_file'])
            
            # Mark as successful
            processing_successful = True
            logging.info("Processing completed successfully!")

    except Exception as e:
        logging.exception(f"Error during processing: {e}")
        
    finally:
        # --- 9. Cleanup ---
        if processing_successful:
            # Only move the original video if processing succeeded
            if paths.get('processed_video_path'):
                file_manager.move_video(video_path, paths['processed_video_path'])
            
            # Clean up the intermediate audio file
            file_manager.delete_temp_audio(paths['audio_file'])
        else:
            logging.warning("Processing failed, intermediate files preserved for debugging")
            
        logging.info("Transcription process completed.")
        return processing_successful

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)