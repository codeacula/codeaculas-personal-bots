# file_manager.py
import os
import datetime
import shutil

def calculate_paths(video_path, repo_root, transcript_base_dir_name, processed_video_dir):
    """ Calculates all necessary input/output paths. """
    paths = {}
    paths['video_path'] = video_path
    paths['base_name'] = os.path.splitext(os.path.basename(video_path))[0]
    paths['video_dir'] = os.path.dirname(video_path)

    # Intermediate audio file
    paths['audio_file'] = os.path.join(paths['video_dir'], f"{paths['base_name']}_audio.wav")

    # Transcript output paths
    transcript_base_dir = os.path.join(repo_root, transcript_base_dir_name)
    now = datetime.datetime.now()
    year = now.strftime('%Y')
    month = now.strftime('%m')
    paths['transcript_subdir'] = os.path.join(transcript_base_dir, year, month)
    paths['output_txt_file'] = os.path.join(paths['transcript_subdir'], f"{paths['base_name']}_transcript_speakers.txt")
    paths['output_srt_file'] = os.path.join(paths['transcript_subdir'], f"{paths['base_name']}_transcript_speakers.srt")

    # Processed video path
    paths['processed_video_dir'] = processed_video_dir
    paths['processed_video_path'] = os.path.join(paths['processed_video_dir'], os.path.basename(video_path))

    return paths

def create_directories(dir_list):
    """ Creates directories if they don't exist. """
    for directory in dir_list:
        if directory: # Ensure path is not None
            try:
                os.makedirs(directory, exist_ok=True)
            except OSError as e:
                print(f"Warning: Could not create directory {directory}: {e}")
                # Decide if this is critical - for processed dir, maybe not, for transcript dir, maybe yes?
                # For simplicity, we just warn here. Main script handles None paths later.
                if directory in dir_list[-1]: # Example: if it's the processed_video_dir
                     return False # Indicate failure relevant to moving video later
    return True

def delete_temp_audio(audio_file_path):
    """ Deletes the intermediate audio file. """
    try:
        if os.path.exists(audio_file_path):
            os.remove(audio_file_path)
            print(f"Cleaned up intermediate audio file: {audio_file_path}")
    except Exception as e:
        print(f"Warning: Could not delete intermediate audio file {audio_file_path}. Error: {e}")

def move_video(video_source_path, video_dest_path):
    """ Moves the video file to the destination path. """
    if not video_dest_path:
        print("Skipping video move because destination path is invalid.")
        return False
    print(f"Moving processed video to: {video_dest_path}")
    try:
        shutil.move(video_source_path, video_dest_path)
        print("Video file moved successfully.")
        return True
    except Exception as e:
        print(f"Error moving video file: {e}")
        print(f"Original video remains at: {video_source_path}")
        return False