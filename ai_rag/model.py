from langchain_community.embeddings.ollama import OllamaEmbeddings
from langchain_community.llms.ollama import Ollama


class Model:
    def __init__(self, name) -> None:
        self.name = name
        self.llm = Ollama(model=name)
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")


def get_model(name: str) -> Model:
    return Model(name=name)
