using UnityEngine;
using UnityEngine.UI;
using TMPro; // Required for TextMeshPro

public class DisclaimerManager : MonoBehaviour
{
    public GameObject disclaimerPanel; // Assign the UI Panel in the Inspector
    public TextMeshProUGUI disclaimerText; // Assign the Text component inside the panel

    private bool isVisible = false;

    void Start()
    {
        // Ensure the panel starts hidden
        if (disclaimerPanel != null)
        {
            disclaimerPanel.SetActive(false);
        }

        // Set default text if needed
        if (disclaimerText != null)
        {
            disclaimerText.text = "You are interacting with an AI-driven educator in this virtual environment. While I strive to provide accurate and helpful information, I am not perfect. I may make mistakes or offer limited perspectives. Always verify critical information with reliable sources or consult a human instructor when needed.";
        }
    }

    // Method to toggle the panel
    public void ToggleDisclaimer()
    {
        if (disclaimerPanel != null)
        {
            isVisible = !isVisible;
            disclaimerPanel.SetActive(isVisible);
        }
        else
        {
            Debug.LogError("Disclaimer Panel is not assigned in the Inspector!");
        }
    }
}

