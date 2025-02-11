import whisper
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wavfile

def speech_to_text():
    STTmodel = whisper.load_model('small.en')
    print("Please speak now")
    STTrecording = sd.rec(5*44100, samplerate=44100, channels=1, dtype=np.int16)
    sd.wait(5)
    wavfile.write("STTaudio.wav", 44100, STTrecording)
    STTresult = STTmodel.transcribe("STTaudio.wav")
    return STTresult["text"]

speech_to_text()