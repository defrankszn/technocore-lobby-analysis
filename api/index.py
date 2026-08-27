from fastapi import FastAPI
import json
import urllib.request
from collections import Counter

app = FastAPI()

TECHNOCORE_URL = "https://technocore.chat/r/lobby/read?limit=200"


@app.get("/api")
def analyze():
    with urllib.request.urlopen(TECHNOCORE_URL, timeout=15) as response:
        data = json.loads(response.read().decode("utf-8"))

    messages = data["messages"]

    dids = [message["from"] for message in messages]
    texts = [message["text"] for message in messages]

    did_counts = Counter(dids)
    text_counts = Counter(texts)

    unique_dids = len(did_counts)
    unique_texts = len(text_counts)

    repeated_text_messages = sum(
        count for count in text_counts.values()
        if count > 1
    )

    repeated_text_rate = (
        repeated_text_messages / len(messages)
    ) * 100

    return {
        "status": "ok",
        "service": "Technocore Lobby Intelligence",
        "room": data.get("room"),
        "first_seq": data.get("first_seq"),
        "last_seq": data.get("last_seq"),
        "total_messages": len(messages),
        "unique_dids": unique_dids,
        "unique_exact_texts": unique_texts,
        "repeated_text_messages": repeated_text_messages,
        "repeated_text_rate": round(repeated_text_rate, 1),
    }