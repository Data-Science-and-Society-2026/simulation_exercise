import whisper
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wavfile
from TTS.api import TTS
import torch
import collections

def speech_to_text():
    STTmodel = whisper.load_model('small.en')
    print("Please speak now")
    STTrecording = sd.rec(5*44100, samplerate=44100, channels=1, dtype=np.int16)
    sd.wait(5)
    wavfile.write("STTaudio.wav", 44100, STTrecording)
    STTresult = STTmodel.transcribe("STTaudio.wav")
    return STTresult["text"]

def text_to_speech(text):
    
    torch.serialization.add_safe_globals([dict, collections.defaultdict])

    # Init TTS with the target model name
    tts = TTS(model_name="tts_models/en/ek1/tacotron2", progress_bar=False).to("cpu")

    # Run TTS
    tts.tts_to_file(text=text, file_path="TTSaudio.wav")