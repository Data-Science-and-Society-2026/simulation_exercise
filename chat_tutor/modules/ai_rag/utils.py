from .model import Model
from .templates import Template


def get_student_name(user_input: str, name_chain):
    return name_chain.invoke({"text": user_input}).strip()


def get_course_name(user_input: str, course_chain):
    return course_chain.invoke({"text": user_input}).strip()


def get_familiarity_level(user_input: str, level_chain):
    return level_chain.invoke({"text": user_input}).strip()


def get_input(input_text: str):
    return input(input_text)


def format_docs(docs):
    return "\n\n".join([f"Document Excerpt:\n{doc.page_content.strip()}" for doc in docs])


def generate_standalone_question(question, chat_history):
    # Format the chat history
    formatted_history = "\n".join(
        [
            f"Student: {msg['content']}" if msg["role"] == "user" else f"AI Tutor: {msg['content']}"
            for msg in chat_history
        ]
    )
    # Create the prompt
    template = Template()
    model = Model("mistral")
    prompt = template.standalone_question_template.format(chat_history=formatted_history, question=question)
    # Generate the standalone question
    response = model.llm(prompt)
    return response.strip()
