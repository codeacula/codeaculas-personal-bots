# transcribe_meeting.py
# Main script for automatic transcription and diarization of video files

import argparse
import sys
import os
import time
import traceback
import torch
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

# Import utility modules
import config
import audio_utils
import transcriber
from transcriber import ModelManager
import diarizer
import alignment
import output_utils
import file_manager
import git_utils

def setup_logging():
    """Configure logging with formatters and handlers"""
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)
    
    # Optionally add file handler (log to file)
    # file_handler = logging.FileHandler('transcribe.log')
    # file_handler.setFormatter(log_formatter)
    # root_logger.addHandler(file_handler)

def main():
    # Setup logging first thing
    setup_logging()
    
    # --- 1. Parse Arguments ---
    parser = argparse.ArgumentParser(description="Transcribe and diarize a video file.")
    parser.add_argument("video_file_path", help="Path to the video file to process.")
    args = parser.parse_args()
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
        
    if not file_manager.create_directories([paths['transcript_subdir'], paths['processed_video_dir']]):
        logging.error(f"Could not create essential transcript directory {paths['transcript_subdir']}. Exiting.")
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
                
            diarization_pipeline = diarizer.load_diarization_pipeline(
                config.DIARIZATION_PIPELINE_NAME, config.HUGGINGFACE_AUTH_TOKEN)
            if diarization_pipeline is None: 
                raise ValueError("Failed to load diarization pipeline.")

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
            logging.info(f"Materialized {len(segments_list)} segments in {time.time() - start_materialize:.2f} seconds.")

            # --- 7. Align Results ---
            aligned_words = alignment.align_speech_and_speakers(segments_list, speaker_turns)
            if aligned_words is None: 
                raise ValueError("Alignment failed critically.")

            # --- 8. Save Transcripts ---
            logging.info("-" * 50)
            txt_saved = output_utils.save_to_txt(aligned_words, str(paths['output_txt_file']))
            srt_saved = output_utils.save_to_srt(aligned_words, str(paths['output_srt_file']), config.SRT_OPTIONS)
            if not txt_saved or not srt_saved: 
                logging.warning("Transcript saving failed.")
                processing_successful = False
            else: 
                logging.info("Transcript files saved successfully.")
                processing_successful = True

    # --- Error Handling ---
    except Exception as e: 
        logging.error(f"\n--- Error during main processing ---\nError: {e}")
        traceback.print_exc()
        processing_successful = False

    # --- 9. Cleanup ---
    finally:
        # Delete intermediate audio file if configured
        if config.DELETE_TEMP_AUDIO: 
            file_manager.delete_temp_audio(str(paths['audio_file']))

    # --- 10. Git & Move ---
    if processing_successful:
        git_success = False
        if config.GIT_ENABLED:
            try:
                rel_txt_path = os.path.relpath(paths['output_txt_file'], config.REPO_ROOT).replace('\\', '/')
                rel_srt_path = os.path.relpath(paths['output_srt_file'], config.REPO_ROOT).replace('\\', '/')
                commit_message = f"{config.GIT_COMMIT_MESSAGE_PREFIX} '{paths['base_name']}'"
                if Path(paths['output_txt_file']).exists() and Path(paths['output_srt_file']).exists():
                    git_success = git_utils.add_commit_push(config.REPO_ROOT, [rel_txt_path, rel_srt_path], commit_message)
                else: logging.warning("Skipping Git: Transcript files not found.")
            except Exception as e: 
                logging.error(f"Error during Git prep/exec: {e}")
                git_success = False
        else: 
            logging.info("Git disabled.")
            git_success = True
        
        if config.MOVE_PROCESSED_VIDEO:
             if git_success: 
                 file_manager.move_video(video_path, str(paths['processed_video_path']))
             else: 
                 logging.warning("Skipping video move: Git failed or processing error occurred.")
        else: 
            logging.info("Moving video disabled.")
            
        logging.info("-" * 50)
        logging.info("Processing Complete!")
        logging.info(f"Final transcripts in: {paths['transcript_subdir']}")
        logging.info("-" * 50)
    else: 
        logging.error("-" * 50)
        logging.error("Processing FAILED.")
        logging.error("Git/Move skipped.")
        logging.error("-" * 50)
        sys.exit(1)

if __name__ == "__main__":
    main()