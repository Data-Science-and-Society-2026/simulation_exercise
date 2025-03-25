using UnityEngine;
using System.IO;

public class ReadInput : MonoBehaviour
{
    private string input;

    public void ReadStringInput(string s)
    {
        input = s;
        Debug.Log("Input received: " + input);
        SaveTextToFile(input);
    }

    void SaveTextToFile(string text)
    {
        string path = Application.persistentDataPath + "/savedText.txt";

        try
        {
            File.WriteAllText(path, text);
            Debug.Log("Text saved to: " + path);
        }
        catch (IOException e)
        {
            Debug.LogError("Error saving file: " + e.Message);
        }
    }
}
