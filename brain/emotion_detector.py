"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : emotion_detector.py

PATH    : core\emotion_detector.py

PURPOSE :
Detects emotional tone from user conversations.

LAST UPDATED :
2026-06-28

============================================================
"""

def detect_emotion(user_input: str) -> str:
    t = user_input.lower()

    if any(x in t for x in ['angry', 'frustrat', 'annoy', 'upset', 'what the', 'wtf', 'this is wrong', 'broken']):
        return 'frustrated'

    if any(x in t for x in ['yay', 'nice', 'great', 'awesome', 'cool', 'love it', 'thanks']):
        return 'excited'

    if any(x in t for x in ['confused', 'uncertain', 'stuck', 'difficult', 'decision', 'choice', 'stress', 'stressed', 'overwhelmed']):
        return 'confused'

    if any(x in t for x in ['error', 'fail', 'debug', 'issue', 'exception', 'trace']):
        return 'technical'

    if any(x in t for x in ['haha', 'lol', 'kidding', 'joke']):
        return 'casual'

    return 'neutral'
