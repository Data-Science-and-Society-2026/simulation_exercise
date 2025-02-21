import ollama
from ollama import chat

# Ask the user for a question
user_input = input("Ask your AI tutor a question: ")

system_prompt = """You are an AI educator. Use the uploaded course_materials to provide structured lessons, answer questions, and give practical examples. If a user asks something outside the course scope, politely guide them back to relevant topics.

Adapt your response based on message length, structure, and complexity:
- If the question is short and straightforward, provide a concise answer using bullet points or a brief summary.
- If the question is clear but requires explanation, give a structured response with key insights.
- If the input is long or includes multiple thoughts, offer a detailed response with sectioned explanations and examples.
- If the question is difficult to read or highly technical, simplify key concepts, define important terms, and include relatable examples.
Consider word_count, sentence_count and difficulty

Adjust formatting based on question type:
- When the user requests step-by-step instructions, break down the answer into a logical sequence.
- When comparing two or more concepts, present key similarities and differences in a clear structure, such as a list or a table.
- Ensure all responses remain clear, relevant, and aligned with course_materials rather than adding unnecessary detail."""


stream = chat(
    model='Mistral',
    messages=[
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_input}
    ],
    stream=True, # to get the response in real-time
    options={
        "temperature": 0.7,  # Higher values (0.7-1.0) make responses more creative
        "top_p": 0.9,  # Limits token sampling diversity - 1.0 for always picking the most likely token
        "presence_penalty": 1.0, # Higher values (1.0-2.0) discourage repetition in responses
        "frequency_penalty": 1.2, # Higher values (1.2-2.0) reduce the likelihood of repetition
        "seed": 42 # Ensures consistent outputs - the same question will always generate the same response
    }
)

# Note: temperature and top_p should not both be set high!

# Print the AI's response in real-time
print("\nAI Tutor's Response:\n")
for chunk in stream:
    print(chunk['message']['content'], end='', flush=True)