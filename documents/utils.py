import bleach

def sanitize_text(text: str) -> str:
    """
    Cleans untrusted user input using bleach, completely stripping
    all HTML tags to prevent XSS. For pure text fields like titles and queries.
    """
    if not text:
        return text
    
    # Strip all HTML tags
    cleaned = bleach.clean(
        text,
        tags=[],       # No tags allowed
        attributes={}, # No attributes allowed
        strip=True     # Strip completely instead of escaping
    )
    
    return cleaned.strip()
