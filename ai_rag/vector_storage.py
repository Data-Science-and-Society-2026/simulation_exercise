from langchain_community.vectorstores import DocArrayInMemorySearch


class VectorStorage:
    def __init__(self, pages, embeddings) -> None:
        self.store = DocArrayInMemorySearch.from_documents(pages, embeddings)
        self.retriever = self.store.as_retriever()
