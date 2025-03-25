using System.Collections.Generic;
using UnityEngine;

public class GameManager : MonoBehaviour
{

    [SerializeField]
    List<Message> messageList = new List<Message>();

    void Start()
    {
        
    }


    void Update()
    {
        if(Input.GetKeyDown(KeyCode.Space))
            SendMessageToChat("Space");
    }

    public void SendMessageToChat(string text)
    {
        Message newMessage = new Message();

        newMessage.text = text;

        messageList.Add(newMessage);
    }
}

[System.Serializable]
public class Message
{
    public string text;
}
