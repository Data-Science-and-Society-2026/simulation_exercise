import ollama
from ollama import chat
import PyPDF2

# Ask the user for a question
user_input = input("Ask your AI tutor a question: ")

system_prompt = "You are a helpful AI tutor for a specific course. Provide clear, structured, and educational responses."

stream = chat(
    model='ALIENTELLIGENCE/learningguidementortutor',
    messages=[
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_input}
    ],
    stream=True,
    options={  # ✅ Define parameters inside "options"
        "temperature": 0.7,  # Higher values (0.7-1.0) make responses more creative
        "top_p": 0.9,  # Limits token sampling diversity
    }
)

# Print the AI's response in real-time
print("\nAI Tutor's Response:\n")
for chunk in stream:
    print(chunk['message']['content'], end='', flush=True)