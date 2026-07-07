import asyncio
import edge_tts
import tempfile
import os
import time
import pygame

VOICE = "en-US-AndrewNeural"


async def _generate(text: str, output: str):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output)


def speak_edge(text: str):

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    temp.close()

    asyncio.run(_generate(text, temp.name))

    if not pygame.mixer.get_init():
        pygame.mixer.init()

    pygame.mixer.music.load(temp.name)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        time.sleep(0.05)

    pygame.mixer.music.unload()

    try:
        os.remove(temp.name)
    except:
        pass