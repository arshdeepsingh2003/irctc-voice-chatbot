# Text-to-Speech
from gtts import gTTS
import uuid
import os

AUDIO_DIR = "audio"

def text_to_speech(text):
    if not os.path.exists(AUDIO_DIR):
        os.makedirs(AUDIO_DIR)

    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)

    tts = gTTS(text=text, lang="en")
    tts.save(filepath)

    return filename