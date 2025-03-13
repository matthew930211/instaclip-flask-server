import uuid

def create_unique_id(extension=""):
    # Generate a UUID-based string
    unique_id = str(uuid.uuid4())
    if extension:
        return f"{unique_id}.{extension}"
    return unique_id
