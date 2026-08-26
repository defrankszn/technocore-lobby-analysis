import json
from collections import Counter
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent.parent / "data"

FILES = [
    DATA_DIR / "lobby_200.json",
    DATA_DIR / "lobby_200_2.json",
    DATA_DIR / "lobby_200_3.json",
]


messages = []

for file_path in FILES:
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
        messages.extend(data["messages"])

print("Total observations:", len(messages))

dids = [message["from"] for message in messages]

did_counts = Counter(dids)

unique_dids = len(did_counts)
repeated_dids = sum(1 for count in did_counts.values() if count > 1)
max_did_appearances = max(did_counts.values())

print("Unique DIDs:", unique_dids)
print("DIDs appearing more than once:", repeated_dids)
print("Most appearances by one DID:", max_did_appearances)

texts = [message["text"] for message in messages]

text_counts = Counter(texts)

unique_texts = len(text_counts)
repeated_text_messages = sum(
    count for count in text_counts.values() if count > 1
)

repeated_text_rate = (
    repeated_text_messages / len(messages)
) * 100

print("Unique exact texts:", unique_texts)
print("Messages belonging to repeated exact texts:", repeated_text_messages)
print(f"Combined repeated-text rate: {repeated_text_rate:.1f}%")

snapshot_counts = []

for file_path in FILES:
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
        counts = Counter(
            message["text"] for message in data["messages"]
        )
        snapshot_counts.append(counts)

shared_texts = (
    set(snapshot_counts[0])
    & set(snapshot_counts[1])
    & set(snapshot_counts[2])
)

persistent_messages = sum(
    sum(counts[text] for counts in snapshot_counts)
    for text in shared_texts
)

persistent_rate = (
    persistent_messages / len(messages)
) * 100

print("Exact texts shared across all 3 snapshots:", len(shared_texts))
print("Messages from those persistent templates:", persistent_messages)
print(f"Persistent-template share: {persistent_rate:.1f}%")

print("\nPersistent templates across all 3 snapshots:")
print("-" * 80)

ranked_shared_texts = sorted(
    shared_texts,
    key=lambda text: sum(
        counts[text] for counts in snapshot_counts
    ),
    reverse=True,
)

for text in ranked_shared_texts:
    counts = [snapshot[text] for snapshot in snapshot_counts]
    total = sum(counts)

    print(
        f"S1: {counts[0]:2} | "
        f"S2: {counts[1]:2} | "
        f"S3: {counts[2]:2} | "
        f"Total: {total:2} | "
        f"{text}"
    )