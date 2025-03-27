import whisper
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wavfile
from TTS.api import TTS
import torch
import re
import os


def is_cuda():
    if torch.cuda.is_available():
        device_name = torch.cuda.get_device_name(0)
        print(f"CUDA is available! Using GPU: {device_name}")
        tts_processor = "cuda"
    else:
        print("CUDA is not available. Using CPU.")
        tts_processor = "cpu"


def speech_to_text():
    STTmodel = whisper.load_model("small.en")
    print("Please speak now")
    STTrecording = sd.rec(5 * 44100, samplerate=44100, channels=1, dtype=np.int16)
    sd.wait(5)
    wavfile.write("STTaudio.wav", 44100, STTrecording)
    STTresult = STTmodel.transcribe("STTaudio.wav")
    os.remove("STTaudio.wav")
    print(STTresult["text"])
    return STTresult["text"]


def text_to_speech(text):
    sentences = re.split(r"(?<=[.!?]) +", text)
    # Init TTS with the target model name
    tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False).to(tts_processor)
    for sentence in sentences:
        audio = tts.tts(sentence)
        sd.play(audio, samplerate=22050, blocking=True)

