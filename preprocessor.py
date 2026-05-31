import re
from collections import Counter


def clean_text(text: str) -> str:
    if text is None:
        return ""
    txt = str(text).replace("\r\n", " ").replace("\n", " ").strip()
    txt = re.sub(r"\s+", " ", txt)
    return txt


def summarize_text(text: str, max_sentences: int = 2) -> str:
    if not text:
        return ""
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]
    if len(sentences) <= max_sentences:
        return " ".join(sentences)
    top = sorted(sentences, key=lambda sentence: len(sentence), reverse=True)[:max_sentences]
    selected = [sentence for sentence in sentences if sentence in top]
    return " ".join(selected[:max_sentences])


def extract_tags(text: str, top_n: int = 6):
    if not text:
        return []
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
    counts = Counter(words)
    return [word for word, _ in counts.most_common(top_n)]


def analyze_content(payload):
    if isinstance(payload, dict):
        content = payload.get("content", "")
        typ = payload.get("type", "text")
        source = payload.get("source", "unknown")
    else:
        content = str(payload)
        typ = "text"
        source = "unknown"
    cleaned = clean_text(content)
    summary = summarize_text(cleaned, max_sentences=2)
    tags = extract_tags(cleaned)
    return {
        "type": typ,
        "source": source,
        "original": content,
        "cleaned": cleaned,
        "summary": summary,
        "tags": tags,
        "content_length": len(cleaned),
    }
