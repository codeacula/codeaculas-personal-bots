# alignment.py
# Aligns Whisper word segments with Pyannote speaker turns using multiprocessing

import time
import multiprocessing
import logging
from functools import partial
import math
from typing import Dict, List, Any, Tuple
import traceback
import bisect

# Import config to get tuning parameters
from . import config

def _find_speaker_for_word(word_info: Dict[str, Any], speaker_turns_tuple: Tuple[Dict[str, Any], ...]) -> Dict[str, Any]:
    """
    Finds the speaker for a single word using binary search (bisect).

    Args:
        word_info (Dict[str, Any]): Information about the word, including start and end times.
        speaker_turns_tuple (Tuple[Dict[str, Any], ...]): Tuple of speaker turn dictionaries.

    Returns:
        Dict[str, Any]: Updated word information with the assigned speaker.
    """
    word_start = word_info['start']
    word_end = word_info['end']
    word_midpoint = word_start + (word_end - word_start) / 2
    speaker = "UNKNOWN"

    if not speaker_turns_tuple:
        word_info['speaker'] = speaker
        return word_info

    turn_start_times = [turn['start'] for turn in speaker_turns_tuple]
    potential_turn_index = bisect.bisect_right(turn_start_times, word_midpoint) - 1

    if potential_turn_index >= 0 and \
       speaker_turns_tuple[potential_turn_index]['start'] <= word_midpoint < speaker_turns_tuple[potential_turn_index]['end']:
        speaker = speaker_turns_tuple[potential_turn_index]['speaker']
    else:
        next_turn_index = potential_turn_index + 1
        if next_turn_index < len(speaker_turns_tuple) and \
           speaker_turns_tuple[next_turn_index]['start'] <= word_midpoint < speaker_turns_tuple[next_turn_index]['end']:
            speaker = speaker_turns_tuple[next_turn_index]['speaker']

    word_info['speaker'] = speaker
    return word_info


def align_speech_and_speakers(segments: List[Any], speaker_turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aligns Whisper word segments with Pyannote speaker turns using multiprocessing.

    Args:
        segments (List[Any]): List of Whisper word segments.
        speaker_turns (List[Dict[str, Any]]): List of speaker turn dictionaries.

    Returns:
        List[Dict[str, Any]]: List of aligned word dictionaries with speaker information.
    """
    logging.info("Aligning transcript segments with speakers (Parallel CPU - Dynamic Workers)...")
    start_alignment = time.time()

    if not speaker_turns:
        logging.warning("Warning: No speaker turns provided...")
        speaker_turns = []

    # Prepare word data
    words_to_process = []
    word_index = 0
    for segment in segments:
        for word in segment.words:
            word_text = word.word.strip()
            if not word_text:
                continue
            words_to_process.append({"start": word.start, "end": word.end, "text": word_text, "word_index": word_index})
            word_index += 1

    if not words_to_process:
        logging.warning("No words found to align.")
        return []

    total_words = len(words_to_process)
    logging.info(f"Total words to align: {total_words}")

    speaker_turns.sort(key=lambda x: x['start'])
    speaker_turns_tuple = tuple(speaker_turns)

    # Determine number of workers dynamically based on workload
    target_chunk_size = config.ALIGNMENT_TARGET_WORDS_PER_CHUNK
    max_workers = config.ALIGNMENT_MAX_WORKERS

    if total_words > 0 and target_chunk_size > 0:
        # Calculate ideal number of chunks/workers based on target size
        num_chunks_ideal = math.ceil(total_words / target_chunk_size)
        # Use the minimum of ideal workers vs the configured max workers
        num_workers = min(max_workers, num_chunks_ideal)
        # Ensure we use at least 1 worker
        num_workers = max(1, num_workers)
    else:
        num_workers = 1  # Default to 1 worker if no words or invalid config

    # Calculate chunksize for pool.map based on the actual number of workers
    chunk_factor = 4  # Aim for roughly 4 chunks per worker for load balancing
    chunksize = max(1, math.ceil(total_words / (num_workers * chunk_factor))) if total_words > 0 else 1

    logging.info(f"Using {num_workers} worker processes (Max configured: {max_workers}) with chunksize {chunksize}.")

    worker_func = partial(_find_speaker_for_word, speaker_turns_tuple=speaker_turns_tuple)
    aligned_words_results = []

    try:
        with multiprocessing.Pool(processes=num_workers) as pool:
            aligned_words_results = pool.map(worker_func, words_to_process, chunksize=chunksize)
    except multiprocessing.TimeoutError as e:
        logging.error(f"Multiprocessing timeout error during parallel alignment: {e}")
        traceback.print_exc()
        return []
    except multiprocessing.AuthenticationError as e:
        logging.error(f"Multiprocessing authentication error during parallel alignment: {e}")
        traceback.print_exc()
        return []
    except Exception as e:
        logging.error(f"Unexpected error during parallel alignment: {e}")
        traceback.print_exc()
        return []

    logging.info(f"Alignment complete in {time.time() - start_alignment:.2f} seconds.")
    return aligned_words_results

# Add an alias for backward compatibility
align_words_with_speakers = align_speech_and_speakers