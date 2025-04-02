# simple_transcribe.py
# Simplified transcription script that bypasses speaker diarization

import logging
import argparse
import os
import sys
from pathlib import Path
import time
from logging.handlers import RotatingFileHandler

from transcribe_meeting import config
from transcribe_meeting import audio_utils
from transcribe_meeting import transcriber
from transcribe_meeting import file_manager
from transcribe_meeting import output_utils
from transcribe_meeting import resource_manager

def setup_logging(log_level: int = logging.INFO) -> None:
    """Configure logging with formatters and handlers."""
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

def save_simple_transcript(segments, output_path):
    """Save the transcription without speaker diarization."""
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments):
                # Format timestamp as [MM:SS]
                start_time = time.strftime("%M:%S", time.gmtime(segment.start))
                f.write(f"[{start_time}] {segment.text}\n")
                if i < len(segments) - 1:
                    f.write("\n")
        logging.info(f"Transcript saved to {output_path}")
        return True
    except Exception as e:
        logging.error(f"Error saving transcript: {e}")
        return False

def main():
    # Setup logging first thing
    setup_logging()
    
    # Parse Arguments
    parser = argparse.ArgumentParser(description="Transcribe a video file (without speaker diarization).")
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

    # Calculate Paths & Create Directories
    paths = file_manager.calculate_paths(
        video_path, config.REPO_ROOT, config.TRANSCRIPT_BASE_DIR_NAME, config.PROCESSED_VIDEO_DIR
    )
    logging.info(f"Processing video: {video_path}")
    logging.info(f"  Intermediate audio: {paths['audio_file']}")
    logging.info(f"  Output directory: {paths['transcript_subdir']}")
    
    # Create a different filename for the simplified transcription
    output_txt_file = paths['transcript_subdir'] / f"{paths['base_name']}_transcript_simple.txt"
    logging.info(f"  Output transcript: {output_txt_file}")
    
    try:
        file_manager.create_directories(paths)
    except Exception as e:
        logging.error(f"Could not create essential directories. Error: {e}")
        sys.exit(1)

    # Extract Audio
    if not audio_utils.extract_audio(video_path, str(paths['audio_file'])): 
        logging.error("Exiting: audio extraction failure.")
        sys.exit(1)

    # Main Processing Block
    processing_successful = False

    try:
        # Use the ModelManager context manager for the Whisper model
        with transcriber.ModelManager(
            config.WHISPER_MODEL_SIZE, 
            config.WHISPER_DEVICE, 
            config.WHISPER_COMPUTE_TYPE
        ) as whisper_model:
            if whisper_model is None:
                raise ValueError("Failed to load Whisper model.")
            
            # Run Transcription & Materialize Results
            logging.info("Running transcription...")
            raw_segments, info = transcriber.run_transcription(whisper_model, str(paths['audio_file']))
            if raw_segments is None: 
                raise ValueError("Transcription failed.")
            
            logging.info("Materializing transcript segments into list...")
            start_materialize = time.time()
            segments_list = list(raw_segments)
            logging.info(f"Materialization completed in {time.time() - start_materialize:.2f} seconds")
            
            # Save the simple transcript
            logging.info(f"Saving transcript to {output_txt_file}")
            if save_simple_transcript(segments_list, output_txt_file):
                processing_successful = True
                logging.info("Processing completed successfully!")
            else:
                raise ValueError("Failed to save transcript")

    except Exception as e:
        logging.exception(f"Error during processing: {e}")
        
    finally:
        # Cleanup
        if processing_successful:
            # Clean up the intermediate audio file
            file_manager.delete_temp_audio(paths['audio_file'])
        else:
            logging.warning("Processing failed, intermediate files preserved for debugging")
            
        logging.info("Transcription process completed.")
        return processing_successful

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)