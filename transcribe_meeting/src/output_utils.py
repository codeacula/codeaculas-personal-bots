# output_utils.py
import math
import logging
from typing import List, Any, Dict

def format_srt_time(seconds: float) -> str:
    """ Converts seconds to SRT time format HH:MM:SS,ms """
    if seconds is None or not isinstance(seconds, (int, float)) or math.isnan(seconds) or math.isinf(seconds):
        return "00:00:00,000" # Handle invalid input
    millisec = max(0, int((seconds - int(seconds)) * 1000))
    sec = max(0, int(seconds) % 60)
    mins = max(0,(int(seconds) // 60) % 60)
    hrs = max(0, int(seconds) // 3600)
    return f"{hrs:02}:{mins:02}:{sec:02},{millisec:03}"

def save_to_txt(aligned_words: List[Dict[str, Any]], filepath: str) -> bool:
    """ Saves the aligned transcript to a simple TXT file. """
    logging.info(f"Saving speaker-aligned TXT transcript to: {filepath}")
    try:
        with open(filepath, "w", encoding="utf-8") as f_txt:
            current_speaker_txt = None
            current_line_txt = ""
            for word_info in aligned_words:
                if not word_info or not word_info.get("text"): continue
                speaker = word_info.get("speaker", "UNKNOWN")
                text = word_info["text"]
                if current_speaker_txt != speaker:
                    if current_line_txt: f_txt.write(f"[{current_speaker_txt}]: {current_line_txt.strip()}\n")
                    current_speaker_txt = speaker; current_line_txt = text
                else: current_line_txt += " " + text
            if current_line_txt: f_txt.write(f"[{current_speaker_txt}]: {current_line_txt.strip()}\n")
        return True
    except Exception as e: logging.error(f"Error writing TXT file {filepath}: {e}"); return False

def _wrap_text_to_lines(text: str, max_line_length: int) -> str:
    """Helper function to wrap text to specific line length"""
    if not max_line_length or len(text) <= max_line_length:
        return text
        
    wrapped_lines = []
    current_line = ""
    words = text.split()
    
    for word in words:
        if not current_line:
            current_line = word
        elif len(current_line) + len(word) + 1 <= max_line_length:
            current_line += " " + word
        else:
            wrapped_lines.append(current_line)
            current_line = word
            
    if current_line:
        wrapped_lines.append(current_line)
        
    return "\n".join(wrapped_lines)

def save_to_srt(aligned_words: List[Dict[str, Any]], filepath: str, srt_options: Dict[str, Any]) -> bool:
    """ Saves the aligned transcript to an SRT subtitle file with phrase grouping and word wrap. """
    logging.info(f"Saving speaker-aligned SRT transcript to: {filepath}")
    max_line_length = srt_options.get("max_line_length", 42)
    max_words_per_entry = srt_options.get("max_words_per_entry", 10)
    gap_threshold = srt_options.get("speaker_gap_threshold", 1.0)

    try:
        with open(filepath, "w", encoding="utf-8") as f_srt:
            srt_sequence = 1
            phrase_start_time = None
            phrase_end_time = None
            phrase_text = ""
            current_speaker_srt = None
            words_in_phrase = 0
            last_word_end_time = 0

            for i, word_info in enumerate(aligned_words):
                if not word_info or not all(k in word_info for k in ['start', 'end', 'text', 'speaker']) \
                   or word_info['start'] is None or word_info['end'] is None: continue
                word_start_time = word_info['start']
                word_end_time = word_info['end']
                speaker = word_info['speaker']
                text = word_info['text']
                if word_start_time > word_end_time: continue

                is_new_speaker = current_speaker_srt != speaker
                is_long_gap = (i > 0) and (word_start_time - last_word_end_time > gap_threshold)
                is_phrase_too_long = (max_words_per_entry is not None and words_in_phrase >= max_words_per_entry)

                if phrase_text and (is_new_speaker or is_long_gap or is_phrase_too_long):
                    f_srt.write(str(srt_sequence) + "\n")
                    f_srt.write(f"{format_srt_time(phrase_start_time)} --> {format_srt_time(phrase_end_time)}\n")
                    line_to_write = f"[{current_speaker_srt}]: {phrase_text.strip()}"
                    
                    # Apply word wrapping
                    line_to_write = _wrap_text_to_lines(line_to_write, max_line_length)
                    
                    f_srt.write(line_to_write + "\n\n")
                    srt_sequence += 1
                    phrase_text = ""

                if not phrase_text: # Start new phrase
                     current_speaker_srt = speaker
                     phrase_start_time = word_start_time
                     phrase_text = text
                     words_in_phrase = 1
                     phrase_end_time = word_end_time
                else: # Append to existing phrase
                     if not is_new_speaker:
                          phrase_text += " " + text
                          phrase_end_time = word_end_time
                          words_in_phrase += 1
                     else: # Start new phrase immediately if speaker changed
                          phrase_text = text
                          words_in_phrase = 1
                          current_speaker_srt = speaker
                          phrase_start_time = word_start_time
                          phrase_end_time = word_end_time
                last_word_end_time = word_end_time

            if phrase_text: # Write last phrase
                f_srt.write(str(srt_sequence) + "\n")
                f_srt.write(f"{format_srt_time(phrase_start_time)} --> {format_srt_time(phrase_end_time)}\n")
                line_to_write = f"[{current_speaker_srt}]: {phrase_text.strip()}"
                
                # Apply word wrapping
                line_to_write = _wrap_text_to_lines(line_to_write, max_line_length)
                
                f_srt.write(line_to_write + "\n\n")
        return True
    except Exception as e: 
        logging.error(f"Error writing SRT file {filepath}: {e}")
        import traceback
        traceback.print_exc()
        return False