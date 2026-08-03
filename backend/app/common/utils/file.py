from pathlib import Path


def get_extension(filename: str) -> str:
    """
    Return the file extension.
    """
    return Path(filename).suffix.lower()


def get_filename(filename: str) -> str:
    """
    Return filename without extension.
    """
    return Path(filename).stem