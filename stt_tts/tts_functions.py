import whisper
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wavfile
from TTS.api import TTS
import torch
import collections

if torch.cuda.is_available():
    device_name = torch.cuda.get_device_name(0)
    print(f"CUDA is available! Using GPU: {device_name}")
    tts_processor = "cuda"
else:
    print("CUDA is not available. Using CPU.")
    tts_processor = "cpu"

def speech_to_text():
    STTmodel = whisper.load_model('small.en')
    print("Please speak now")
    STTrecording = sd.rec(5*44100, samplerate=44100, channels=1, dtype=np.int16)
    sd.wait(5)
    wavfile.write("STTaudio.wav", 44100, STTrecording)
    STTresult = STTmodel.transcribe("STTaudio.wav")
    return STTresult["text"]

def text_to_speech(text):

    # Init TTS with the target model name
    tts = TTS(model_name="tts_models/en/ek1/tacotron2", progress_bar=False).to(tts_processor)

    # Run TTS
    tts.tts_to_file(text=text, file_path="TTSaudio.wav")