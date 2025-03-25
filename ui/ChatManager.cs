using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class ChatManager : MonoBehaviour
{
    [SerializeField] private TMP_InputField userInputField; // Input field for text
    [SerializeField] private TextMeshProUGUI chatDisplay;   // Chat display
    [SerializeField] private Button sendButton;            // Send button
    [SerializeField] private Button recordButton;          // Button to start/stop recording
    [SerializeField] private AudioSource audioSource;      // Audio source for playback

    private string pythonPath = "C:\\Python39\\python.exe"; // Path to Python; please check if this has to be changed
    private string scriptPath = "C:\\placeholder\\ai_script.py"; // Path to the AI script
    private string speechToTextScriptPath = "C:\\placeholder\\speech_to_text.py"; // Path to the Speech-to-text script 

    private List<string> messages = new List<string>(); // Chat history
    private bool firstResponseGiven = false; // Tracks first response
    private bool isRecording = false; // Tracks if audio is recording
    private AudioClip recordedClip;
    private float startTime;
    private float recordingLength;

    void Start()
    {
        sendButton.onClick.AddListener(() => SendMessageToAI(userInputField.text));
        recordButton.onClick.AddListener(ToggleRecording);
        userInputField.onSubmit.AddListener(delegate { SendMessageToAI(userInputField.text); });
    }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Return))
        {
            SendMessageToAI(userInputField.text);
        }
    }

    public void SendMessageToAI(string userMessage)
    {
        if (string.IsNullOrWhiteSpace(userMessage)) return;

        AppendMessage("You: " + userMessage);
        userInputField.text = ""; // Clearing the input field

        string aiResponse = GetAIResponse(userMessage);
        AppendMessage("AI: " + aiResponse);
    }

    private string GetAIResponse(string userMessage)
    {
        if (!firstResponseGiven)
        {
            firstResponseGiven = true;
            return "Hello! I am an AI-educator, designed to assist you with learning and providing information, but I am not a human instructor. Please look for the Disclaimer button for more information on my abilities and limitations.";
        }

        if (!File.Exists(scriptPath))
        {
            return "Error: AI script not found";
        }

        ProcessStartInfo psi = new ProcessStartInfo
        {
            FileName = pythonPath,
            Arguments = $"\"{scriptPath}\" \"{userMessage}\"",
            RedirectStandardOutput = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };

        Process process = new Process { StartInfo = psi };
        process.Start();
        string aiResponse = process.StandardOutput.ReadToEnd();
        process.WaitForExit();

        return aiResponse.Trim();
    }

    private void ToggleRecording()
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
        recordedClip = Microphone.Start(device, false, 3599, 44100);
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

        string transcribedText = ConvertSpeechToText(recordedClip);
        if (!string.IsNullOrEmpty(transcribedText))
        {
            SendMessageToAI(transcribedText); // Sending the transcribed text to AI
        }
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

        ProcessStartInfo psi = new ProcessStartInfo
        {
            FileName = pythonPath,
            Arguments = $"\"{speechToTextScriptPath}\" \"{tempWavPath}\"",
            RedirectStandardOutput = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };

        try
        {
            Process process = Process.Start(psi);
            string output = process.StandardOutput.ReadToEnd();
            process.WaitForExit();
            return output.Trim();
        }
        catch (Exception e)
        {
            UnityEngine.Debug.LogError("Error running Speech-to-Text script: " + e.Message);
            return "Error processing speech.";
        }
    }

    private void AppendMessage(string message)
    {
        messages.Add(message);
        if (messages.Count > 10) messages.RemoveAt(0);
        chatDisplay.text = string.Join("\n", messages);
    }
}
