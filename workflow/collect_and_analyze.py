import time
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "workflow_snapshots"
TECHNOCORE_AGENT = PROJECT_ROOT.parent / "technocore-did-starter" / "technocore_agent.py"

TECHNOCORE_PYTHON = (
    PROJECT_ROOT.parent
    / "technocore-did-starter"
    / ".venv"
    / "Scripts"
    / "python.exe"
)

DATA_DIR.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

snapshot_file = DATA_DIR / f"lobby_{timestamp}.json"

MAX_ATTEMPTS = 3

result = None

for attempt in range(1, MAX_ATTEMPTS + 1):
    result = subprocess.run(
        [
            str(TECHNOCORE_PYTHON),
            str(TECHNOCORE_AGENT),
            "read",
            "lobby",
            "--limit",
            "200",
        ],
        cwd=TECHNOCORE_AGENT.parent,
        capture_output=True,
        text=True,
    )

    output = result.stdout.strip()

    if result.returncode == 0 and output:
        break

    print(f"Attempt {attempt} failed or returned empty output.")

    if result.stderr:
        print(result.stderr.strip())

    if attempt < MAX_ATTEMPTS:
        time.sleep(5)

else:
    raise RuntimeError(
        "Technocore returned no usable data after 3 attempts."
    )

data = json.loads(output)

snapshot_file.write_text(
    json.dumps(data, indent=2),
    encoding="utf-8",
)

print(f"Saved snapshot: {snapshot_file}")

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

print()
print("Snapshot analysis")
print("-----------------")
print("Total messages:", len(messages))
print("Unique DIDs:", unique_dids)
print("Unique exact texts:", unique_texts)
print("Messages in repeated exact-text groups:", repeated_text_messages)
print(f"Repeated-text rate: {repeated_text_rate:.1f}%")

previous_files = sorted(DATA_DIR.glob("lobby_*.json"))

if len(previous_files) > 1:
    previous_file = previous_files[-2]

    with open(previous_file, "r", encoding="utf-8") as file:
        previous_data = json.load(file)

    previous_texts = [
        message["text"]
        for message in previous_data["messages"]
    ]

    previous_counts = Counter(previous_texts)

    shared_texts = set(text_counts) & set(previous_counts)

    print()
    print("Comparison with previous snapshot")
    print("---------------------------------")
    print("Previous snapshot:", previous_file.name)
    print("Shared exact texts:", len(shared_texts))

    ranked_shared = sorted(
        shared_texts,
        key=lambda text: text_counts[text] + previous_counts[text],
        reverse=True,
    )

    print()
    print("Top shared templates:")

    for text in ranked_shared[:5]:
        print(
            f"Previous: {previous_counts[text]:2} | "
            f"Current: {text_counts[text]:2} | "
            f"{text}"
        )

        report = {
    "snapshot_file": snapshot_file.name,
    "total_messages": len(messages),
    "unique_dids": unique_dids,
    "unique_exact_texts": unique_texts,
    "repeated_text_messages": repeated_text_messages,
    "repeated_text_rate": round(repeated_text_rate, 1),
}

if len(previous_files) > 1:
    report["previous_snapshot"] = previous_file.name
    report["shared_exact_texts"] = len(shared_texts)

report_file = snapshot_file.with_suffix(".report.json")

report_file.write_text(
    json.dumps(report, indent=2),
    encoding="utf-8",
)

print()
print(f"Saved report: {report_file}")