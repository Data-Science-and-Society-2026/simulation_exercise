import os


def load_pdf(path: str):
    """Loads a single Pdf from a directory"""
    return os.getenv("pdfs")


def load_pdfs(folder_path: list[str]):
    """Loads various pdfs from a directory"""
