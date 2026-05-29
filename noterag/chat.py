import json
import requests
from datetime import date

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b"
RELEVANCE_THRESHOLD = 0.85


def _build_system(chunks: list[dict], profile: str = "", custom_prompt: str = "") -> str:
    use_sources = bool(chunks) and chunks[0]["distance"] < RELEVANCE_THRESHOLD
    today = date.today().strftime("%B %d, %Y")

    parts = [
        f"Today's date is {today}.\n"
        "You are a thoughtful personal assistant who knows the user well through their private logs, journals, and notes.\n"
        "Respond in a warm, conversational tone — like a close friend who's been paying attention.\n"
        "Synthesize context naturally; never say 'according to source' or list sources.\n"
        "Keep answers concise but personal."
    ]

    if profile:
        parts.append(f"About the user:\n{profile}")

    if custom_prompt:
        parts.append(f"Additional instructions:\n{custom_prompt}")

    if use_sources:
        sources = ""
        for chunk in chunks:
            meta = chunk["metadata"]
            label = f"{meta.get('source', '')} · {meta.get('date', '')}"
            sources += f"{label}: {chunk['text']}\n\n"
        parts.append(f"Relevant context from the user's logs:\n{sources}")
    else:
        parts.append("If asked about personal data you don't have context for, say so honestly.")

    return "\n\n".join(parts)


def stream_chat(query: str, chunks: list[dict], history: list[dict] | None = None,
                profile: str = "", custom_prompt: str = ""):
    messages = [{"role": "system", "content": _build_system(chunks, profile, custom_prompt)}]
    for msg in (history or []):
        messages.append({"role": msg["role"], "content": msg["text"]})
    messages.append({"role": "user", "content": query})

    response = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "messages": messages, "stream": True},
        stream=True,
        timeout=120,
    )
    response.raise_for_status()
    for line in response.iter_lines():
        if not line:
            continue
        data = json.loads(line)
        token = data.get("message", {}).get("content", "")
        if token:
            yield token
        if data.get("done"):
            break
