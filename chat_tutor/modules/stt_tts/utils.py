import pygame
from modules.stt_tts.asr import ASR
from modules.stt_tts.tts import Tts


class ListenAndSpeak:
    """SpeechSearchAndSynthesize retrieves the text, queries it with the google search api and later voices the result"""

    def __init__(self, ground_truth: str = "") -> None:
        self.asr = ASR(name="Speech Recognition System")
        self.tts = Tts(name="Text-to-Speech System")
        self.ground_truth = ground_truth

    def run(self):
        query_text = self.asr.speech_to_text()

        if query_text:
            print(f"Recognized Text: {query_text}")

            # Translation here
            # asyncio.run(translate_text(search_result))

            audio_waveform = self.tts.text_to_speech(ai_response)

            if audio_waveform is not None:
                waveform_data = audio_waveform.numpy()

                if waveform_data.ndim == 1:
                    waveform_data = waveform_data.reshape(-1, 1)
                elif waveform_data.ndim == 2 and waveform_data.shape[0] == 1:
                    waveform_data = waveform_data.squeeze(axis=0)

                sf.write("search_result_audio.wav", waveform_data, 22050)
                print("Audio file saved as 'search_result_audio.wav'.")

                pygame.mixer.init()
                pygame.mixer.music.load("search_result_audio.wav")
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(30)
            else:
                print("Error: No waveform data available.")
