# output_utils.py
import math

def format_srt_time(seconds):
    """ Converts seconds to SRT time format HH:MM:SS,ms """
    if seconds is None or not isinstance(seconds, (int, float)) or math.isnan(seconds) or math.isinf(seconds):
        return "00:00:00,000" # Handle invalid input
    millisec = max(0, int((seconds - int(seconds)) * 1000))
    sec = max(0, int(seconds) % 60)
    mins = max(0,(int(seconds) // 60) % 60)
    hrs = max(0, int(seconds) // 3600)
    return f"{hrs:02}:{mins:02}:{sec:02},{millisec:03}"

def save_to_txt(aligned_words, filepath):
    """ Saves the aligned transcript to a simple TXT file. """
    print(f"Saving speaker-aligned TXT transcript to: {filepath}")
    # Note: This format uses simple grouping - might look choppy if diarization was noisy.
    try:
        with open(filepath, "w", encoding="utf-8") as f_txt:
            current_speaker_txt = None
            current_line_txt = ""
            for word_info in aligned_words:
                if not word_info or not word_info.get("text"): continue # Basic validation
                speaker = word_info.get("speaker", "UNKNOWN")
                text = word_info["text"]
                if current_speaker_txt != speaker:
                    if current_line_txt:
                        f_txt.write(f"[{current_speaker_txt}]: {current_line_txt}\n")
                    current_speaker_txt = speaker
                    current_line_txt = text
                else:
                    current_line_txt += " " + text
            # Write the last line
            if current_line_txt:
                f_txt.write(f"[{current_speaker_txt}]: {current_line_txt}\n")
        return True
    except Exception as e:
        print(f"Error writing TXT file {filepath}: {e}")
        return False

def save_to_srt(aligned_words, filepath, srt_options):
    """ Saves the aligned transcript to an SRT subtitle file with phrase grouping. """
    print(f"Saving speaker-aligned SRT transcript to: {filepath}")
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
            last_word_end_time = 0 # Track end time for gap calculation

            for i, word_info in enumerate(aligned_words):
                if not word_info or not word_info.get("text") or \
                   word_info.get("start") is None or word_info.get("end") is None: continue # Validation

                word_start_time = word_info['start']
                word_end_time = word_info['end']
                speaker = word_info.get('speaker', 'UNKNOWN')
                text = word_info['text']

                is_new_speaker = current_speaker_srt != speaker
                # Check gap based on current word start and *previous* word end
                is_long_gap = (i > 0) and (word_start_time - last_word_end_time > gap_threshold)
                is_phrase_too_long = (max_words_per_entry is not None and words_in_phrase >= max_words_per_entry)

                # If phrase exists and needs to be written out...
                if phrase_text and (is_new_speaker or is_long_gap or is_phrase_too_long):
                    f_srt.write(str(srt_sequence) + "\n")
                    f_srt.write(f"{format_srt_time(phrase_start_time)} --> {format_srt_time(phrase_end_time)}\n")
                    line = f"[{current_speaker_srt}]: {phrase_text}"

                    # Word wrap logic
                    if max_line_length:
                        wrapped_lines = []; current_line = ""
                        for word in line.split():
                             if not current_line: current_line = word
                             elif len(current_line) + len(word) + 1 <= max_line_length: current_line += " " + word
                             else: wrapped_lines.append(current_line); current_line = word
                        wrapped_lines.append(current_line); line = "\n".join(wrapped_lines)

                    f_srt.write(line + "\n\n")
                    srt_sequence += 1
                    phrase_text = "" # Reset phrase

                # Start or continue the current phrase
                if not phrase_text: # Start of a new phrase
                     current_speaker_srt = speaker
                     phrase_start_time = word_start_time
                     phrase_text = text
                     words_in_phrase = 1
                     phrase_end_time = word_end_time # Initialize end time
                else: # Append to existing phrase
                     phrase_text += " " + text
                     phrase_end_time = word_end_time # Update end time
                     words_in_phrase += 1

                last_word_end_time = word_end_time # Update for next iteration's gap check

            # Write the very last phrase after the loop
            if phrase_text:
                f_srt.write(str(srt_sequence) + "\n")
                f_srt.write(f"{format_srt_time(phrase_start_time)} --> {format_srt_time(phrase_end_time)}\n")
                line = f"[{current_speaker_srt}]: {phrase_text}"
                # Word wrap logic (duplicated for last line)
                if max_line_length:
                    wrapped_lines = []; current_line = ""
                    for word in line.split():
                         if not current_line: current_line = word
                         elif len(current_line) + len(word) + 1 <= max_line_length: current_line += " " + word
                         else: wrapped_lines.append(current_line); current_line = word
                    wrapped_lines.append(current_line); line = "\n".join(wrapped_lines)
                f_srt.write(line + "\n\n")
        return True
    except Exception as e:
         print(f"Error writing SRT file {filepath}: {e}")
         return False