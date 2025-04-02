"""Alignment utilities for matching transcribed words with speaker segments."""
import logging
from typing import List, Dict, Any, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed


def align_words_with_speakers(
    transcribed_segments: List[Dict[str, Any]],
    speaker_turns: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Align transcribed words with their corresponding speakers.

    Args:
        transcribed_segments: List of transcribed word segments
        speaker_turns: List of speaker turn segments

    Returns:
        List of word segments with speaker information
    """
    if not speaker_turns or not transcribed_segments:
        logging.warning("Empty speaker turns or transcribed segments.")
        return []

    aligned_words = []
    for segment in transcribed_segments:
        if not segment or "words" not in segment:
            continue

        for word in segment["words"]:
            word_with_speaker = _find_speaker_for_word(word, speaker_turns)
            if word_with_speaker:
                aligned_words.append(word_with_speaker)

    return sorted(aligned_words, key=lambda x: x["start"])


def _find_speaker_for_word(
    word: Dict[str, Any],
    speaker_turns: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Find the speaker for a given word based on timing.

    Args:
        word: Word information dict
        speaker_turns: List of speaker turn segments

    Returns:
        Word dict with speaker information or None if no match
    """
    if not word or "start" not in word or "end" not in word:
        return None

    word_start = word["start"]
    word_end = word["end"]
    word_duration = word_end - word_start
    word_midpoint = word_start + (word_duration / 2)

    # Find the speaker turn that contains the word's midpoint
    for turn in speaker_turns:
        if turn["start"] <= word_midpoint <= turn["end"]:
            return {
                "text": word["text"],
                "start": word_start,
                "end": word_end,
                "speaker": turn["speaker"],
                "confidence": word.get("confidence", 1.0)
            }

    # If no exact match, find the closest speaker turn
    return _find_closest_speaker_turn(word, speaker_turns)


def _find_closest_speaker_turn(
    word: Dict[str, Any],
    speaker_turns: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Find the closest speaker turn for a word that doesn't fall within any turn.

    Args:
        word: Word information dict
        speaker_turns: List of speaker turn segments

    Returns:
        Word dict with speaker information from closest turn
    """
    word_start = word["start"]
    word_end = word["end"]
    word_midpoint = word_start + ((word_end - word_start) / 2)
    
    closest_turn = None
    min_distance = float('inf')

    for turn in speaker_turns:
        turn_start = turn["start"]
        turn_end = turn["end"]
        turn_midpoint = turn_start + ((turn_end - turn_start) / 2)
        
        distance = abs(turn_midpoint - word_midpoint)
        if distance < min_distance:
            min_distance = distance
            closest_turn = turn

    if closest_turn:
        return {
            "text": word["text"],
            "start": word_start,
            "end": word_end,
            "speaker": closest_turn["speaker"],
            "confidence": word.get("confidence", 1.0)
        }
    
    # Fallback if no speaker turns are found
    return {
        "text": word["text"],
        "start": word_start,
        "end": word_end,
        "speaker": "UNKNOWN",
        "confidence": word.get("confidence", 1.0)
    }


def align_speech_and_speakers(
    speech_segments: List[Dict[str, Any]],
    speaker_segments: List[Dict[str, Any]],
    max_workers: Optional[int] = None,
    chunk_size: int = 500
) -> List[Dict[str, Any]]:
    """
    Parallel processing version of word-speaker alignment.

    Args:
        speech_segments: List of transcribed speech segments
        speaker_segments: List of speaker segments
        max_workers: Maximum number of worker processes
        chunk_size: Number of words to process in each chunk

    Returns:
        List of aligned word segments with speaker information
    """
    # Extract all words from speech segments
    all_words = []
    for segment in speech_segments:
        if segment and "words" in segment:
            all_words.extend(segment["words"])

    if not all_words or not speaker_segments:
        return []

    # Chunk the words for parallel processing
    word_chunks = [
        all_words[i:i + chunk_size]
        for i in range(0, len(all_words), chunk_size)
    ]

    aligned_words = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit chunks for parallel processing
        future_to_chunk = {
            executor.submit(
                _process_word_chunk,
                chunk,
                speaker_segments
            ): chunk for chunk in word_chunks
        }

        # Collect results
        for future in as_completed(future_to_chunk):
            try:
                chunk_result = future.result()
                aligned_words.extend(chunk_result)
            except Exception as e:
                logging.error(f"Error processing word chunk: {e}")
                continue

    # Sort by start time
    return sorted(aligned_words, key=lambda x: x["start"])


def _process_word_chunk(
    words: List[Dict[str, Any]],
    speaker_segments: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Process a chunk of words for parallel alignment.

    Args:
        words: List of words to process
        speaker_segments: List of speaker segments

    Returns:
        List of words with aligned speaker information
    """
    aligned_chunk = []
    for word in words:
        aligned_word = _find_speaker_for_word(word, speaker_segments)
        if aligned_word:
            aligned_chunk.append(aligned_word)
    return aligned_chunk