import json
import os
import re
import sqlite3
from openai import OpenAI

MODEL = "gpt-4o-mini"

_client = None


def get_client() -> OpenAI:
    """Lazily creates the OpenAI client so the app can boot even before .env is loaded,
    and so a missing key raises a clear error only when a query is actually made."""
    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Copy .env.example to .env and paste your key there."
            )
        _client = OpenAI(api_key=api_key)
    return _client


def _extract_schema(conn: sqlite3.Connection) -> str:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    schema_lines = []
    for t in tables:
        cur.execute(f"PRAGMA table_info({t})")
        cols = [f"{row[1]} ({row[2]})" for row in cur.fetchall()]
        schema_lines.append(f"Table {t}: " + ", ".join(cols))
    return "\n".join(schema_lines)


def _is_read_only(sql: str) -> bool:
    forbidden = ("insert", "update", "delete", "drop", "alter", "create", "attach", "pragma")
    lowered = sql.strip().lower()
    return lowered.startswith("select") and not any(f in lowered for f in forbidden)


def question_to_sql(conn: sqlite3.Connection, question: str) -> str:
    schema = _extract_schema(conn)
    system_prompt = (
        "You are a SQL generator for a SQLite database used by a business analytics tool. "
        "Given the schema and a plain-English question from a non-technical business owner, "
        "write ONE single read-only SQLite SELECT query that answers it. "
        "Rules:\n"
        "- Output ONLY the SQL query, no explanation, no markdown fences.\n"
        "- Only use SELECT statements. Never modify data.\n"
        "- Always JOIN to human-readable names (e.g. branch_name) instead of raw ids when relevant.\n"
        "- Use meaningful column aliases (e.g. total_revenue, avg_order_value) - these aliases "
        "  will be used to decide chart type, so name date columns with 'date' and category "
        "  columns clearly.\n"
        "- For 'lowest performing' or 'underperforming' questions, ORDER BY the relevant metric "
        "  ascending and LIMIT results sensibly (e.g. 5) unless the question asks for all rows.\n"
        "- For week-over-week or trend questions, use the date columns available.\n"
    )
    user_prompt = f"SCHEMA:\n{schema}\n\nQUESTION: {question}\n\nSQL:"

    resp = get_client().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
    )
    sql = resp.choices[0].message.content.strip()
    sql = re.sub(r"^```sql|```$|^```", "", sql, flags=re.IGNORECASE | re.MULTILINE).strip()

    if not _is_read_only(sql):
        raise ValueError(f"Generated query was not a safe read-only SELECT: {sql}")
    return sql


def run_query(conn: sqlite3.Connection, sql: str) -> list[dict]:
    cur = conn.cursor()
    cur.execute(sql)
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    return rows


def generate_insight(question: str, rows: list[dict]) -> str:
    if not rows:
        return "No data matched this question. Try rephrasing or check the date range."

    sample = rows[:15]  # keep prompt small
    system_prompt = (
        "You are a business analyst. Given a user's question and the query results (JSON), "
        "write a 1-2 sentence plain-English insight a non-technical business owner could act on. "
        "Be specific with numbers. Do not mention SQL, tables, or the word 'query'. "
        "If something stands out (a big drop, a clear winner/loser), call it out directly."
    )
    user_prompt = f"Question: {question}\nResults (JSON): {json.dumps(sample, default=str)}"

    resp = get_client().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )
    return resp.choices[0].message.content.strip()
