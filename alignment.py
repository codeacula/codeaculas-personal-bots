# alignment.py
# Aligns Whisper word segments with Pyannote speaker turns using multiprocessing
# with limited workers and explicit chunksize.

import time
import traceback
import multiprocessing
import os
import bisect
from functools import partial
import math

def _find_speaker_for_word(word_info, speaker_turns_tuple):
    """ Finds the speaker for a single word using binary search (bisect). """
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


def align_speech_and_speakers(segments, speaker_turns):
    """ Aligns Whisper word segments with Pyannote speaker turns using multiprocessing. """
    print("Aligning transcript segments with speakers (Parallel CPU - Tuned)...")
    start_alignment = time.time()

    if not speaker_turns:
        print("Warning: No speaker turns provided for alignment. Assigning UNKNOWN to all words.")
        speaker_turns = []

    words_to_process = []
    word_index = 0
    for segment in segments: # Assumes segments is iterable (list or generator)
        for word in segment.words:
            word_text = word.word.strip()
            if not word_text: continue
            words_to_process.append({
                "start": word.start, "end": word.end,
                "text": word_text, "word_index": word_index
            })
            word_index += 1

    if not words_to_process:
        print("No words found to align.")
        return []

    total_words = len(words_to_process)
    print(f"Total words to align: {total_words}")

    speaker_turns.sort(key=lambda x: x['start'])
    speaker_turns_tuple = tuple(speaker_turns)

    total_logical_cores = os.cpu_count()
    num_workers = max(1, total_logical_cores // 2) # Use half logical cores
    chunk_factor = 4
    chunksize = max(1, math.ceil(total_words / (num_workers * chunk_factor)))

    print(f"Using {num_workers} worker processes (Logical cores: {total_logical_cores}) with chunksize {chunksize}.")

    worker_func = partial(_find_speaker_for_word, speaker_turns_tuple=speaker_turns_tuple)

    aligned_words_results = []
    try:
        with multiprocessing.Pool(processes=num_workers) as pool:
            aligned_words_results = pool.map(worker_func, words_to_process, chunksize=chunksize)

    except Exception as e:
        print(f"Error during parallel alignment: {e}")
        traceback.print_exc()
        return []

    print(f"Alignment complete in {time.time() - start_alignment:.2f} seconds.")
    return aligned_words_results