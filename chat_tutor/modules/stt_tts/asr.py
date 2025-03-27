import whisper
import pyaudio
import wave


class ASR:
    def __init__(self, name: str):
        self.name = name
        self.model = whisper.load_model("base")

    def speech_to_text(self, record_time: int):
        print("Listening your query...")

        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        CHUNK = 1024
        RECORD_SECONDS = record_time
        WAVE_OUTPUT_FILENAME = "audio_query.wav"

        p = pyaudio.PyAudio()

        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        print("Recording...")
        frames = []

        for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)

        print("Finished recording.")
        stream.stop_stream()
        stream.close()
        p.terminate()

        with wave.open(WAVE_OUTPUT_FILENAME, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b"".join(frames))

        result = self.model.transcribe(WAVE_OUTPUT_FILENAME)
        print(f"Recognized text: {result['text']}")
        return result["text"]
