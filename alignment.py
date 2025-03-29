# alignment.py
import time
import traceback

def align_speech_and_speakers(segments, speaker_turns):
    """ Aligns Whisper word segments with Pyannote speaker turns (Optimized). """
    print("Aligning transcript segments with speakers (Optimized)...")
    start_alignment = time.time()
    aligned_words = []

    if not speaker_turns:
        print("Warning: No speaker turns found for alignment. Assigning UNKNOWN to all words.")
        # Handle case with no diarization result - assign UNKNOWN to all words
        word_index = 0
        for segment in segments:
            for word in segment.words:
                word_text = word.word.strip()
                if not word_text: continue
                aligned_words.append({
                    "start": word.start, "end": word.end, "speaker": "UNKNOWN",
                    "text": word_text, "word_index": word_index
                })
                word_index += 1
        print(f"Alignment (defaulted) complete in {time.time() - start_alignment:.2f} seconds.")
        return aligned_words

    # --- Pointer/Iterator Alignment Logic ---
    current_turn_index = 0
    word_index = 0
    try:
        for segment in segments:
            for word in segment.words:
                word_text = word.word.strip()
                if not word_text: continue

                word_start = word.start
                word_end = word.end
                word_midpoint = word_start + (word_end - word_start) / 2
                speaker = "UNKNOWN" # Default

                # Advance turn pointer
                while current_turn_index < len(speaker_turns) and \
                      speaker_turns[current_turn_index]['end'] < word_start:
                    current_turn_index += 1

                # Check current turn
                if current_turn_index < len(speaker_turns) and \
                   speaker_turns[current_turn_index]['start'] <= word_midpoint < speaker_turns[current_turn_index]['end']:
                    speaker = speaker_turns[current_turn_index]['speaker']
                else:
                    # Check next turn (handles edge cases near turn boundaries)
                    next_turn_index = current_turn_index + 1
                    if word_start >= speaker_turns[current_turn_index]['end'] and \
                       next_turn_index < len(speaker_turns) and \
                       speaker_turns[next_turn_index]['start'] <= word_midpoint < speaker_turns[next_turn_index]['end']:
                           current_turn_index = next_turn_index
                           speaker = speaker_turns[current_turn_index]['speaker']
                    # Else: Keep speaker as UNKNOWN (word is in a gap)

                aligned_words.append({
                    "start": word_start, "end": word_end, "speaker": speaker,
                    "text": word_text, "word_index": word_index
                })
                word_index += 1

    except Exception as e:
        print(f"Error processing Whisper segments/words during alignment: {e}")
        traceback.print_exc()
        # Return partially aligned words or empty list? Let's return what we have.
        # Consider adding more robust error handling if needed.
        pass # Continue to saving with potentially incomplete alignment


    print(f"Alignment complete in {time.time() - start_alignment:.2f} seconds.")
    return aligned_words