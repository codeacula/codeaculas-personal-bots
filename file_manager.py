# file_manager.py
import os
import datetime
import shutil

def calculate_paths(video_path, repo_root, transcript_base_dir_name, processed_video_dir):
    paths = {}; paths['video_path'] = video_path; paths['base_name'] = os.path.splitext(os.path.basename(video_path))[0]; paths['video_dir'] = os.path.dirname(video_path)
    paths['audio_file'] = os.path.join(paths['video_dir'], f"{paths['base_name']}_audio.wav")
    transcript_base_dir = os.path.join(repo_root, transcript_base_dir_name); now = datetime.datetime.now(); year = now.strftime('%Y'); month = now.strftime('%m')
    paths['transcript_subdir'] = os.path.join(transcript_base_dir, year, month)
    paths['output_txt_file'] = os.path.join(paths['transcript_subdir'], f"{paths['base_name']}_transcript_speakers.txt")
    paths['output_srt_file'] = os.path.join(paths['transcript_subdir'], f"{paths['base_name']}_transcript_speakers.srt")
    paths['processed_video_dir'] = processed_video_dir; paths['processed_video_path'] = os.path.join(paths['processed_video_dir'], os.path.basename(video_path)) if processed_video_dir else None
    return paths

def create_directories(dir_list):
    essential_dirs_ok = True
    for i, directory in enumerate(dir_list):
        is_essential = (i == 0); # Assume transcript_subdir is essential
        if directory:
            try: os.makedirs(directory, exist_ok=True)
            except OSError as e: print(f"Warning: Could not create directory {directory}: {e}");
            if is_essential and not os.path.isdir(directory): essential_dirs_ok = False
    return essential_dirs_ok

def delete_temp_audio(audio_file_path):
    try:
        if os.path.exists(audio_file_path): os.remove(audio_file_path); print(f"Cleaned up intermediate audio file: {audio_file_path}")
    except Exception as e: print(f"Warning: Could not delete intermediate audio file {audio_file_path}. Error: {e}")

def move_video(video_source_path, video_dest_path):
    if not video_dest_path or not os.path.exists(os.path.dirname(video_dest_path)): print("Skipping video move: destination path/dir invalid."); return False
    print(f"Moving processed video to: {video_dest_path}")
    try: shutil.move(video_source_path, video_dest_path); print("Video file moved successfully."); return True
    except Exception as e: print(f"Error moving video file: {e}\nOriginal video remains at: {video_source_path}"); return False