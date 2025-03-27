from django.http import JsonResponse
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
import os
import time
import json
import soundfile as sf

from chat.chat_view import generate_ai_response

from modules.stt_tts.asr import ASR
from modules.stt_tts.tts import Tts


def voice_chat(request):

    if request.method == "POST":
        try:
            if "audio" not in request.FILES:
                return JsonResponse({"error": "No audio file provided."}, status=400)

            audio_file = request.FILES["audio"]
            input_audio_path = os.path.join(settings.MEDIA_ROOT, "voice_input.wav")
            with open(input_audio_path, "wb+") as destination:
                for chunk in audio_file.chunks():
                    destination.write(chunk)

            asr_system = ASR(name="Speech Recognition System")
            asr_result = asr_system.model.transcribe(input_audio_path)
            recognized_text = asr_result.get("text", "").strip()
            print(f"ASR recognized: {recognized_text}")

            if not recognized_text:
                return JsonResponse({"error": "No speech recognized."}, status=400)

            chat_history = ""  # or load conversation history if applicable
            ai_text, doc_count, query_time = generate_ai_response(recognized_text, chat_history, request)
            print(f"AI response: {ai_text}")

            tts_system = Tts(name="Text-to-Speech System")
            audio_waveform = tts_system.text_to_speech(ai_text)
            if audio_waveform is None:
                return JsonResponse({"error": "TTS failed to generate waveform."}, status=500)

            output_filename = "voice_response.wav"
            output_audio_path = os.path.join(settings.MEDIA_ROOT, output_filename)
            waveform_data = audio_waveform.numpy()
            if waveform_data.ndim == 1:
                waveform_data = waveform_data.reshape(-1, 1)
            elif waveform_data.ndim == 2 and waveform_data.shape[0] == 1:
                waveform_data = waveform_data.squeeze(axis=0)
            sf.write(output_audio_path, waveform_data, 22050)  # Adjust sampling rate as needed

            audio_url = settings.MEDIA_URL + output_filename

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
            print("Voice chat error:", e)
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method."}, status=400)
