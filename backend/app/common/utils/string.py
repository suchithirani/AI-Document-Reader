import uuid


def generate_uuid() -> str:
    """
    Generate a UUID4 string.
    """
    return str(uuid.uuid4())


def normalize_string(value: str) -> str:
    """
    Normalize a string.
    """
    return value.strip().lower()
