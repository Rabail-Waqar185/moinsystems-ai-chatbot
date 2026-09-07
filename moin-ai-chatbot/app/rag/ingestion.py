"""
Text normalization applied to knowledge records before embedding.
Kept deliberately conservative — we don't want to alter meaning, only
clean up whitespace/encoding artifacts that would otherwise pollute
embeddings and stored content.
"""
import re
import unicodedata


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
