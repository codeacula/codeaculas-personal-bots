# file_manager.py
import os
import datetime
import shutil
import logging
from pathlib import Path

def calculate_paths(video_path, repo_root, transcript_base_dir_name, processed_video_dir):
    paths = {}
    video_path = Path(video_path)
    paths['video_path'] = video_path
    paths['base_name'] = video_path.stem
    paths['video_dir'] = video_path.parent
    paths['audio_file'] = paths['video_dir'] / f"{paths['base_name']}_audio.wav"
    
    transcript_base_dir = Path(repo_root) / transcript_base_dir_name
    now = datetime.datetime.now()
    year = now.strftime('%Y')
    month = now.strftime('%m')
    paths['transcript_subdir'] = transcript_base_dir / year / month
    paths['output_txt_file'] = paths['transcript_subdir'] / f"{paths['base_name']}_transcript_speakers.txt"
    paths['output_srt_file'] = paths['transcript_subdir'] / f"{paths['base_name']}_transcript_speakers.srt"
    
    paths['processed_video_dir'] = processed_video_dir if processed_video_dir else None
    paths['processed_video_path'] = Path(processed_video_dir) / video_path.name if processed_video_dir else None
    return paths

def create_directories(dir_list):
    essential_dirs_ok = True
    for i, directory in enumerate(dir_list):
        is_essential = (i == 0)  # Assume transcript_subdir is essential
        if directory:
            try:
                Path(directory).mkdir(parents=True, exist_ok=True)
            except OSError as e:
                logging.warning(f"Could not create directory {directory}: {e}")
                if is_essential and not Path(directory).is_dir():
                    essential_dirs_ok = False
    return essential_dirs_ok

def delete_temp_audio(audio_file_path):
    try:
        audio_path = Path(audio_file_path)
        if audio_path.exists():
            audio_path.unlink()
            logging.info(f"Cleaned up intermediate audio file: {audio_file_path}")
    except Exception as e:
        logging.warning(f"Could not delete intermediate audio file {audio_file_path}. Error: {e}")

def move_video(video_source_path, video_dest_path):
    source_path = Path(video_source_path)
    dest_path = Path(video_dest_path)
    if not dest_path or not dest_path.parent.exists():
        logging.warning("Skipping video move: destination path/dir invalid.")
        return False
    
    logging.info(f"Moving processed video to: {dest_path}")
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_path), str(dest_path))
        logging.info("Video file moved successfully.")
        return True
    except Exception as e:
        logging.error(f"Error moving video file: {e}\nOriginal video remains at: {source_path}")
        return False