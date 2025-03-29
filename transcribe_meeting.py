# transcribe_meeting.py
# Main script to process video, diarize, transcribe, save, and manage files.

import argparse
import sys
import os
import time
import traceback

# Import utility modules
import config
import audio_utils
import transcriber
import diarizer
import alignment
import output_utils
import file_manager
import git_utils

def main():
    # --- 1. Parse Arguments ---
    parser = argparse.ArgumentParser(description="Transcribe and diarize a video file.")
    parser.add_argument("video_file_path", help="Path to the video file to process.")
    args = parser.parse_args()
    video_path = args.video_file_path

    if not os.path.exists(video_path):
        print(f"Error: Video file not found at '{video_path}'")
        sys.exit(1)

    # --- 2. Calculate Paths & Create Directories ---
    paths = file_manager.calculate_paths(
        video_path,
        config.REPO_ROOT,
        config.TRANSCRIPT_BASE_DIR_NAME,
        config.PROCESSED_VIDEO_DIR
    )

    print(f"Processing video: {video_path}")
    print(f"  Intermediate audio: {paths['audio_file']}")
    print(f"  Output directory: {paths['transcript_subdir']}")
    # (Print other paths as needed)

    if not file_manager.create_directories([paths['transcript_subdir'], paths['processed_video_dir']]):
        # Handle critical directory creation failure if necessary
        print("Exiting due to directory creation issues.")
        sys.exit(1)


    # --- 3. Extract Audio ---
    if not audio_utils.extract_audio(video_path, paths['audio_file']):
        print("Exiting due to audio extraction failure.")
        sys.exit(1)

    # --- Main Processing Block ---
    processing_successful = False
    whisper_model = None
    diarization_pipeline = None
    aligned_words = None

    try:
        # --- 4. Load Models ---
        # Load models once at the beginning
        whisper_model = transcriber.load_whisper_model(
            config.WHISPER_MODEL_SIZE, config.WHISPER_DEVICE, config.WHISPER_COMPUTE_TYPE
        )
        diarization_pipeline = diarizer.load_diarization_pipeline(
            config.DIARIZATION_PIPELINE_NAME, config.HUGGINGFACE_AUTH_TOKEN
        )

        if whisper_model is None or diarization_pipeline is None:
            raise Exception("Failed to load one or more models.") # Ensure script exits if models fail

        # --- 5. Run Diarization ---
        diarization_result = diarizer.run_diarization(diarization_pipeline, paths['audio_file'])
        if diarization_result is None:
             raise Exception("Diarization step failed.")

        speaker_turns = diarizer.extract_speaker_turns(diarization_result)
        # Optional: print number of speaker turns found

        # --- 6. Run Transcription ---
        segments, info = transcriber.run_transcription(whisper_model, paths['audio_file'])
        if segments is None:
            raise Exception("Transcription step failed.")

        # --- 7. Align Results ---
        aligned_words = alignment.align_speech_and_speakers(segments, speaker_turns)
        if aligned_words is None: # Check if alignment function indicates critical failure
            raise Exception("Alignment step failed critically.")

        # --- 8. Save Transcripts ---
        print("-" * 50)
        txt_saved = output_utils.save_to_txt(aligned_words, paths['output_txt_file'])
        srt_saved = output_utils.save_to_srt(aligned_words, paths['output_srt_file'], config.SRT_OPTIONS)

        if not txt_saved or not srt_saved:
            print("Warning: One or both transcript files failed to save.")
            # Decide if processing should still be marked as successful for Git/Move
            # For now, let's proceed if at least one saved, but maybe add stricter checks.
        print("Transcript saving attempted.")
        processing_successful = True # Mark success if we got this far

    # --- Error Handling for Main Processing ---
    except Exception as e:
        print(f"\n--- An error occurred during main processing ---")
        print(f"Error: {e}")
        traceback.print_exc()
        processing_successful = False # Ensure flag is False on error

    # --- 9. Cleanup and Final Operations ---
    finally:
        # Delete intermediate audio file regardless of success/failure
        if config.DELETE_TEMP_AUDIO:
            file_manager.delete_temp_audio(paths['audio_file'])

    # --- 10. Git Commit/Push & Move Video (Only on Success) ---
    if processing_successful:
        git_success = False
        if config.GIT_ENABLED:
            # Calculate relative paths for Git Add command
            try:
                rel_txt_path = os.path.relpath(paths['output_txt_file'], config.REPO_ROOT).replace('\\', '/')
                rel_srt_path = os.path.relpath(paths['output_srt_file'], config.REPO_ROOT).replace('\\', '/')
                commit_message = f"{config.GIT_COMMIT_MESSAGE_PREFIX} '{paths['base_name']}'"

                git_success = git_utils.add_commit_push(
                    config.REPO_ROOT,
                    [rel_txt_path, rel_srt_path],
                    commit_message
                )
            except Exception as e:
                print(f"Error preparing or executing Git commands: {e}")
                git_success = False # Mark Git as failed
        else:
            print("Git operations disabled in config.")
            git_success = True # Treat as success if disabled

        # Move video only if processing succeeded AND (Git was disabled OR Git succeeded)
        if config.MOVE_PROCESSED_VIDEO:
             # Optionally only move if git succeeded: if git_success:
             file_manager.move_video(video_path, paths['processed_video_path'])
        else:
             print("Moving processed video disabled in config.")

        print("-" * 50)
        print("Processing Complete!")
        print(f"Final transcripts in: {paths['transcript_subdir']}")
        print("-" * 50)

    else:
        print("-" * 50)
        print("Processing FAILED due to errors during model inference or alignment.")
        print("Transcripts may not be complete or saved.")
        print("Git operations and video move SKIPPED.")
        print("-" * 50)
        sys.exit(1) # Exit with error code if processing failed


if __name__ == "__main__":
    main()