from langchain_community.embeddings.ollama import OllamaEmbeddings
from langchain_community.llms.ollama import Ollama

MODEL_INSTANCE = None


def get_cached_model(name="mistral"):
    global MODEL_INSTANCE
    if MODEL_INSTANCE is None:
        print("Loading model for the first time...")
        MODEL_INSTANCE = get_model(name)
    else:
        print("Using cached model instance.")
    return MODEL_INSTANCE


class Model:
    def __init__(self, name) -> None:
        self.name = name
        self.llm = Ollama(model=name)
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        self.prompt = self.llm.get_prompts()


def get_model(name: str) -> Model:
    return Model(name=name)
