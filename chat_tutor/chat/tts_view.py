import os
import soundfile as sf
from django.http import JsonResponse
from chat.chat_view import generate_ai_response
from chat_tutor import settings
from modules.stt_tts.asr import ASR
from modules.stt_tts.tts import Tts


def voice_chat(request):
    """
    A view to capture audio from the microphone, transcribe it via ASR,
    query the AI model with the recognized text, then convert the AI response to speech.
    Returns a JSON response containing:
      - recognized_text: The text from the user's speech.
      - ai_text: The AI's text response.
      - doc_count: How many PDF documents contributed to the answer.
      - query_time: How long inference took.
      - audio_url: A URL to the generated audio file.
    """
    if request.method == "POST":
        try:
            record_time = int(request.POST.get("record_time", 5))
            # Instantiate ASR and TTS systems

            asr_system = ASR(name="Speech Recognition System")
            tts_system = Tts(name="Text-to-Speech System")

            # 1. Use ASR to capture audio and transcribe to text
            recognized_text = asr_system.speech_to_text(record_time)
            print(f"Recognized Text: {recognized_text}")

            # 2. Use your existing generate_ai_response to get the AI answer.
            # Note: You may need to set an empty chat history or pass an existing one.
            chat_history = ""  # or load existing chat history if needed
            ai_text, doc_count, query_time = generate_ai_response(recognized_text, chat_history, request)
            print(f"AI Response: {ai_text}")

            # 3. Convert the AI text response into speech using TTS
            audio_waveform = tts_system.text_to_speech(ai_text)
            if audio_waveform is None:
                return JsonResponse({"error": "TTS failed to generate waveform."}, status=500)

            audio_filename = "voice_response.wav"
            audio_file_path = os.path.join(settings.MEDIA_ROOT, audio_filename)
            waveform_data = audio_waveform.numpy()
            if waveform_data.ndim == 1:
                waveform_data = waveform_data.reshape(-1, 1)
            elif waveform_data.ndim == 2 and waveform_data.shape[0] == 1:
                waveform_data = waveform_data.squeeze(axis=0)
            sf.write(audio_file_path, waveform_data, 22050)  # Adjust sampling rate as needed

            # 5. Build a URL to the saved audio file
            audio_url = settings.MEDIA_URL + audio_filename

            return JsonResponse(
                {
                    "recognized_text": recognized_text,
                    "ai_text": ai_text,
                    "doc_count": doc_count,
                    "query_time": query_time,
                    "audio_url": audio_url,
                }
            )
        except Exception as e:
            print("Error in voice_chat:", e)
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=400)
