# transcribe_meeting.py
# Main script - Removes the explicit model unloading block to avoid crash.
# Uses segment materialization. Should be paired with tuned multiprocessing alignment.py.

import argparse
import sys
import os
import time
import traceback
import torch # Still potentially needed by modules if not unloaded

# Import utility modules
import config
import audio_utils
import transcriber
import diarizer
import alignment # Should be the Tuned Multiprocessing version
import output_utils
import file_manager
import git_utils

def main():
    # --- 1. Parse Arguments ---
    parser = argparse.ArgumentParser(description="Transcribe and diarize a video file.")
    parser.add_argument("video_file_path", help="Path to the video file to process.")
    args = parser.parse_args()
    video_path = args.video_file_path

    if not os.path.exists(video_path): print(f"Error: Video file not found at '{video_path}'"); sys.exit(1)

    # --- 2. Calculate Paths & Create Directories ---
    paths = file_manager.calculate_paths(
        video_path, config.REPO_ROOT, config.TRANSCRIPT_BASE_DIR_NAME, config.PROCESSED_VIDEO_DIR
    )
    print(f"Processing video: {video_path}"); print(f"  Intermediate audio: {paths['audio_file']}")
    print(f"  Output directory: {paths['transcript_subdir']}");
    if paths['processed_video_path']: print(f"  Processed video will move to: {paths['processed_video_path']}")
    if not file_manager.create_directories([paths['transcript_subdir'], paths['processed_video_dir']]):
        print(f"Error: Could not create essential transcript directory {paths['transcript_subdir']}. Exiting."); sys.exit(1)

    # --- 3. Extract Audio ---
    if not audio_utils.extract_audio(video_path, paths['audio_file']): print("Exiting: audio extraction failure."); sys.exit(1)

    # --- Main Processing Block ---
    processing_successful = False
    # Keep model variables in scope until main() ends
    whisper_model = None
    diarization_pipeline = None
    aligned_words = None
    speaker_turns = []
    segments_list = [] # Store materialized segments

    try:
        # --- 4. Load Models ---
        whisper_model = transcriber.load_whisper_model(
            config.WHISPER_MODEL_SIZE, config.WHISPER_DEVICE, config.WHISPER_COMPUTE_TYPE)
        diarization_pipeline = diarizer.load_diarization_pipeline(
            config.DIARIZATION_PIPELINE_NAME, config.HUGGINGFACE_AUTH_TOKEN)
        if whisper_model is None or diarization_pipeline is None: raise Exception("Failed to load models.")

        # --- 5. Run Diarization ---
        diarization_result = diarizer.run_diarization(diarization_pipeline, paths['audio_file'])
        if diarization_result is None: raise Exception("Diarization failed.")
        speaker_turns = diarizer.extract_speaker_turns(diarization_result)

        # --- 6. Run Transcription & Materialize Results ---
        raw_segments, info = transcriber.run_transcription(whisper_model, paths['audio_file'])
        if raw_segments is None: raise Exception("Transcription failed.")
        # --- >>> Materialize Segments <<< ---
        print("Materializing transcript segments into list (might trigger GPU access)...")
        start_materialize = time.time()
        segments_list = list(raw_segments) # Convert generator/iterable to list
        print(f"Materialized {len(segments_list)} segments in {time.time() - start_materialize:.2f} seconds.")

        # --- MODEL UNLOADING BLOCK REMOVED --- # <---------------- REMOVED

        # --- 7. Align Results (Using Materialized List) ---
        # This alignment function (tuned multiprocessing) will use the list
        # Models are still technically loaded in memory here, but alignment code shouldn't use GPU.
        aligned_words = alignment.align_speech_and_speakers(segments_list, speaker_turns)
        if aligned_words is None: raise Exception("Alignment failed critically.")

        # --- 8. Save Transcripts ---
        print("-" * 50)
        # Ensure using the fixed output_utils.py
        txt_saved = output_utils.save_to_txt(aligned_words, paths['output_txt_file'])
        srt_saved = output_utils.save_to_srt(aligned_words, paths['output_srt_file'], config.SRT_OPTIONS)
        if not txt_saved or not srt_saved: print("Warning: Transcript saving failed."); processing_successful = False
        else: print("Transcript files saved successfully."); processing_successful = True

    # --- Error Handling ---
    except Exception as e: print(f"\n--- Error during main processing ---\nError: {e}"); traceback.print_exc(); processing_successful = False

    # --- 9. Cleanup ---
    finally:
        # Delete intermediate audio file regardless of success/failure
        if config.DELETE_TEMP_AUDIO: file_manager.delete_temp_audio(paths['audio_file'])
        # Note: Models are NOT explicitly deleted here anymore. Python GC handles it on exit.

    # --- 10. Git & Move ---
    if processing_successful:
        # (Git and Move logic remains unchanged)
        git_success = False
        if config.GIT_ENABLED:
            try:
                rel_txt_path = os.path.relpath(paths['output_txt_file'], config.REPO_ROOT).replace('\\', '/'); rel_srt_path = os.path.relpath(paths['output_srt_file'], config.REPO_ROOT).replace('\\', '/')
                commit_message = f"{config.GIT_COMMIT_MESSAGE_PREFIX} '{paths['base_name']}'"
                if os.path.exists(paths['output_txt_file']) and os.path.exists(paths['output_srt_file']): git_success = git_utils.add_commit_push(config.REPO_ROOT, [rel_txt_path, rel_srt_path], commit_message)
                else: print("Skipping Git: Transcript files not found.")
            except Exception as e: print(f"Error during Git prep/exec: {e}"); git_success = False
        else: print("Git disabled."); git_success = True
        if config.MOVE_PROCESSED_VIDEO:
             if git_success: file_manager.move_video(video_path, paths['processed_video_path'])
             else: print("Skipping video move: Git failed or processing error occurred.")
        else: print("Moving video disabled.")
        print("-" * 50); print("Processing Complete!"); print(f"Final transcripts in: {paths['transcript_subdir']}"); print("-" * 50)
    else: print("-" * 50); print("Processing FAILED."); print("Git/Move skipped."); print("-" * 50); sys.exit(1)

if __name__ == "__main__":
    main()