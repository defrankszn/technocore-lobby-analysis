from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pathlib import Path
import json
import os
import urllib.request
from collections import Counter
from datetime import datetime, timezone

import psycopg


app = FastAPI()

DASHBOARD_FILE = Path(__file__).resolve().parent.parent / "index.html"
TECHNOCORE_URL = "https://technocore.chat/r/lobby?format=json&limit=200"

DATABASE_URL = os.environ.get("POSTGRES_URL")


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD_FILE.read_text(encoding="utf-8")


def initialize_database():
    if not DATABASE_URL:
        raise RuntimeError("POSTGRES_URL environment variable is missing.")

    with psycopg.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS lobby_snapshots (
                    id BIGSERIAL PRIMARY KEY,
                    generated_at TIMESTAMPTZ NOT NULL,
                    room TEXT NOT NULL,
                    first_seq BIGINT,
                    last_seq BIGINT NOT NULL UNIQUE,
                    total_messages INTEGER NOT NULL,
                    unique_dids INTEGER NOT NULL,
                    did_uniqueness_rate DOUBLE PRECISION NOT NULL,
                    unique_exact_texts INTEGER NOT NULL,
                    text_uniqueness_rate DOUBLE PRECISION NOT NULL,
                    repeated_text_messages INTEGER NOT NULL,
                    repeated_text_rate DOUBLE PRECISION NOT NULL
                );
                """
            )


def save_snapshot(metrics):
    initialize_database()

    with psycopg.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO lobby_snapshots (
                    generated_at,
                    room,
                    first_seq,
                    last_seq,
                    total_messages,
                    unique_dids,
                    did_uniqueness_rate,
                    unique_exact_texts,
                    text_uniqueness_rate,
                    repeated_text_messages,
                    repeated_text_rate
                )
                VALUES (
                    %(generated_at)s,
                    %(room)s,
                    %(first_seq)s,
                    %(last_seq)s,
                    %(total_messages)s,
                    %(unique_dids)s,
                    %(did_uniqueness_rate)s,
                    %(unique_exact_texts)s,
                    %(text_uniqueness_rate)s,
                    %(repeated_text_messages)s,
                    %(repeated_text_rate)s
                )
                ON CONFLICT (last_seq) DO NOTHING;
                """,
                metrics,
            )


@app.get("/api")
def analyze():
    try:
        request = urllib.request.Request(
            TECHNOCORE_URL,
            headers={
                "Accept": "application/json",
                "User-Agent": "technocore-lobby-intelligence/1.0",
            },
        )

        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))

        messages = data["messages"]

        dids = [message["from"] for message in messages]
        texts = [message["text"] for message in messages]

        did_counts = Counter(dids)
        text_counts = Counter(texts)

        unique_dids = len(did_counts)
        unique_texts = len(text_counts)

        repeated_text_messages = sum(
            count
            for count in text_counts.values()
            if count > 1
        )

        repeated_text_rate = (
            repeated_text_messages / len(messages) * 100
            if messages
            else 0
        )

        did_uniqueness_rate = (
            unique_dids / len(messages) * 100
            if messages
            else 0
        )

        text_uniqueness_rate = (
            unique_texts / len(messages) * 100
            if messages
            else 0
        )

        top_templates = [
            {
                "text": text,
                "count": count,
            }
            for text, count in text_counts.most_common(5)
            if count > 1
        ]

        generated_at = datetime.now(timezone.utc)

        metrics = {
            "generated_at": generated_at,
            "room": data.get("room", "lobby"),
            "first_seq": data.get("first_seq"),
            "last_seq": data.get("last_seq"),
            "total_messages": len(messages),
            "unique_dids": unique_dids,
            "did_uniqueness_rate": round(did_uniqueness_rate, 1),
            "unique_exact_texts": unique_texts,
            "text_uniqueness_rate": round(text_uniqueness_rate, 1),
            "repeated_text_messages": repeated_text_messages,
            "repeated_text_rate": round(repeated_text_rate, 1),
        }

        history_saved = True
        history_error = None

        try:
            save_snapshot(metrics)
        except Exception as error:
            history_saved = False
            history_error = str(error)

        return {
            "status": "ok",
            "service": "Technocore Lobby Intelligence",
            **metrics,
            "generated_at": generated_at.isoformat(),
            "top_repeated_templates": top_templates,
            "history_saved": history_saved,
            "history_error": history_error,
        }

    except Exception as error:
        return {
            "status": "error",
            "error": str(error),
        }


@app.get("/api/history")
def history():
    try:
        initialize_database()

        with psycopg.connect(DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        generated_at,
                        first_seq,
                        last_seq,
                        total_messages,
                        unique_dids,
                        did_uniqueness_rate,
                        unique_exact_texts,
                        text_uniqueness_rate,
                        repeated_text_messages,
                        repeated_text_rate
                    FROM lobby_snapshots
                    ORDER BY generated_at DESC
                    LIMIT 100;
                    """
                )

                rows = cursor.fetchall()

        observations = [
            {
                "generated_at": row[0].isoformat(),
                "first_seq": row[1],
                "last_seq": row[2],
                "total_messages": row[3],
                "unique_dids": row[4],
                "did_uniqueness_rate": row[5],
                "unique_exact_texts": row[6],
                "text_uniqueness_rate": row[7],
                "repeated_text_messages": row[8],
                "repeated_text_rate": row[9],
            }
            for row in rows
        ]

        return {
            "status": "ok",
            "count": len(observations),
            "observations": observations,
        }

    except Exception as error:
        return {
            "status": "error",
            "error": str(error),
        }