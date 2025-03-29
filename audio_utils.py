# audio_utils.py
import subprocess
import os
import sys

def extract_audio(video_path, audio_output_path):
    """ Extracts audio from video using ffmpeg. """
    print(f"Extracting audio from {os.path.basename(video_path)}...")
    ffmpeg_command = [
        "ffmpeg",
        "-i", video_path,
        "-vn",  # No video
        "-acodec", "pcm_s16le", # Audio Codec WAV
        "-ar", "16000", # Sample rate
        "-y", # Overwrite output file if it exists
        audio_output_path
    ]
    try:
        process = subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True)
        print("FFmpeg audio extraction successful.")
        return True
    except FileNotFoundError:
         print("Error: ffmpeg command not found. Make sure ffmpeg is installed and in your system's PATH.")
         return False
    except subprocess.CalledProcessError as e:
        print(f"Error during FFmpeg execution: {e}")
        print(f"FFmpeg stderr:\n{e.stderr}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during audio extraction: {e}")
        return False