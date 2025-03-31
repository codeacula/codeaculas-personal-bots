import pytest
from transcribe_meeting.alignment import align_speech_and_speakers

# Mock data for testing
def test_align_speech_and_speakers():
    segments = [
        type("Segment", (object,), {"words": [
            type("Word", (object,), {"start": 0.0, "end": 1.0, "word": "Hello"}),
            type("Word", (object,), {"start": 1.1, "end": 2.0, "word": "world"})
        ]})()
    ]

    speaker_turns = [
        {"start": 0.0, "end": 1.5, "speaker": "SPEAKER_1"},
        {"start": 1.5, "end": 2.5, "speaker": "SPEAKER_2"}
    ]

    expected_output = [
        {"start": 0.0, "end": 1.0, "text": "Hello", "word_index": 0, "speaker": "SPEAKER_1"},
        {"start": 1.1, "end": 2.0, "text": "world", "word_index": 1, "speaker": "SPEAKER_2"}
    ]

    result = align_speech_and_speakers(segments, speaker_turns)
    assert result == expected_output