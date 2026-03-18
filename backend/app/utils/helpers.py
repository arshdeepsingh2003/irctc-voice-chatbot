import re

def extract_train_number(text: str):
    """
    Extracts train number (5 or 6 digits) from user text
    """
    if not text:
        return None

    match = re.search(r'\b\d{5,6}\b', text)
    return match.group() if match else None


def extract_pnr(text: str):
    """
    Extracts PNR number (10 digits) from user text
    """
    if not text:
        return None

    match = re.search(r'\b\d{10}\b', text)
    return match.group() if match else None