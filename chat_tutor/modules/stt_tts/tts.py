import speechbrain as sb
from speechbrain.inference import Tacotron2, HIFIGAN


class Tts:
    def __init__(self, name: str):
        self.name = name
        self.models = {}

        self.load_models()

    def load_models(self):
        self.models["tacotron2"] = Tacotron2.from_hparams(
            source="speechbrain/tts-tacotron2-ljspeech", savedir="tacotron_dir"
        )

        self.models["hifigan"] = HIFIGAN.from_hparams(
            source="speechbrain/tts-hifigan-ljspeech", savedir="hifigan_vocoder"
        )

    def text_to_speech(self, text: str):
        tacotron2 = self.models.get("tacotron2")
        hifigan = self.models.get("hifigan")

        if tacotron2 is None or hifigan is None:
            print("Error: Models not loaded.")
            return None

        encoded_text = tacotron2.encode_text(text)

        if isinstance(encoded_text, tuple):
            encoded_text = encoded_text[0]

        mel_output, mel_length, alignment = tacotron2.encode_text(text)

        waveform, *_ = hifigan.decode_batch(mel_output)

        if waveform is None:
            raise ValueError("Error: Waveform generation failed")

        return waveform.squeeze(1)
