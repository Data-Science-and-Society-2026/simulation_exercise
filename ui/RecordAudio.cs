using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using UnityEngine;

public class RecordAudio : MonoBehaviour
{
    private AudioClip recordedClip;
    [SerializeField] private AudioSource audioSource;
    private float startTime;
    private float recordingLength;
    private bool isRecording = false;

    public void ToggleRecording()
    {
        if (isRecording)
        {
            StopRecording();
        }
        else
        {
            StartRecording();
        }
    }

    private void StartRecording()
    {
        string device = Microphone.devices[0];
        int sampleRate = 44100;
        int lengthSec = 3599;

        recordedClip = Microphone.Start(device, false, lengthSec, sampleRate);
        startTime = Time.realtimeSinceStartup;
        isRecording = true;
        UnityEngine.Debug.Log("Recording started...");
    }

    private void StopRecording()
    {
        Microphone.End(null);
        recordingLength = Time.realtimeSinceStartup - startTime;
        recordedClip = TrimClip(recordedClip, recordingLength);
        isRecording = false;
        UnityEngine.Debug.Log("Recording stopped.");

        // Convert and send the recorded clip to the Python script
        string transcription = ConvertSpeechToText(recordedClip);
        UnityEngine.Debug.Log("Transcription: " + transcription);
    }

    private AudioClip TrimClip(AudioClip clip, float length)
    {
        int samples = (int)(clip.frequency * length);
        float[] data = new float[samples];
        clip.GetData(data, 0);

        AudioClip trimmedClip = AudioClip.Create(clip.name, samples, clip.channels, clip.frequency, false);
        trimmedClip.SetData(data, 0);

        return trimmedClip;
    }

    private string ConvertSpeechToText(AudioClip clip)
    {
        string tempWavPath = Path.Combine(Application.persistentDataPath, "temp_recording.wav");
        WavUtility.Save(tempWavPath, clip);

        ProcessStartInfo psi = new ProcessStartInfo();
        psi.FileName = "python";
        psi.Arguments = $"speech_to_text.py \"{tempWavPath}\"";
        psi.RedirectStandardOutput = true;
        psi.UseShellExecute = false;
        psi.CreateNoWindow = true;

        try
        {
            Process process = Process.Start(psi);
            string output = process.StandardOutput.ReadToEnd();
            process.WaitForExit();
            return output.Trim();
        }
        catch (Exception e)
        {
            UnityEngine.Debug.LogError("Error running Python script: " + e.Message);
            return "Error processing speech-to-text.";
        }
    }
}
