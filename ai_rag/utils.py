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
