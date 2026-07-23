import os
import sqlite3
import traceback

import pandas as pd
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from chart_logic import infer_chart
import nl_engine

load_dotenv()

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
SOURCE_DB_PATH = os.path.join(DATA_DIR, "branches.db")

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

# One shared in-memory database that all connectors load into.
_MEMORY_DB = sqlite3.connect(":memory:", check_same_thread=False)
_CONNECTED_SOURCES = []  # for the UI to display "connected: SQLite, CSV"


def get_db() -> sqlite3.Connection:
    return _MEMORY_DB


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/status")
def status():
    return jsonify({"connected_sources": _CONNECTED_SOURCES})


@app.route("/api/connectors/sql", methods=["POST"])
def connect_sql():
    try:
        if not os.path.exists(SOURCE_DB_PATH):
            return jsonify({"error": "branches.db not found. Run generate_data.py first."}), 400

        source = sqlite3.connect(SOURCE_DB_PATH)
        db = get_db()
        table_details = []
        for table_name in ("branches", "sales", "footfall"):
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", source)
            df.to_sql(table_name, db, if_exists="replace", index=False)
            table_details.append({"table": table_name, "rows": len(df)})
        source.close()

        if "SQLite (branches.db)" not in _CONNECTED_SOURCES:
            _CONNECTED_SOURCES.append("SQLite (branches.db)")

        return jsonify({
            "status": "connected",
            "db_type": "SQLite",
            "db_path": SOURCE_DB_PATH,
            "tables_loaded": ["branches", "sales", "footfall"],
            "table_details": table_details,
            "connected_sources": _CONNECTED_SOURCES,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/connectors/csv", methods=["POST"])
def connect_csv():
    """Connector #2: uploads a CSV file and loads it as a table (default: 'inventory')."""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded. Field name must be 'file'."}), 400

        file = request.files["file"]
        table_name = request.form.get("table_name", "inventory")
        # sanitize table name
        table_name = "".join(c for c in table_name if c.isalnum() or c == "_") or "inventory"

        df = pd.read_csv(file)
        db = get_db()
        df.to_sql(table_name, db, if_exists="replace", index=False)

        label = f"CSV ({table_name})"
        if label not in _CONNECTED_SOURCES:
            _CONNECTED_SOURCES.append(label)

        return jsonify({
            "status": "connected",
            "table_name": table_name,
            "rows_loaded": len(df),
            "columns": list(df.columns),
            "preview": df.head(3).to_dict(orient="records"),
            "connected_sources": _CONNECTED_SOURCES,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/query", methods=["POST"])
def query():
    """Takes {"question": "..."} and returns SQL, rows, chart spec, and an insight."""
    try:
        payload = request.get_json(force=True)
        question = (payload or {}).get("question", "").strip()
        if not question:
            return jsonify({"error": "Question is required."}), 400

        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        if not cur.fetchall():
            return jsonify({"error": "No data sources connected yet. Connect at least one connector first."}), 400

        sql = nl_engine.question_to_sql(db, question)
        rows = nl_engine.run_query(db, sql)
        chart_spec = infer_chart(rows)
        insight = nl_engine.generate_insight(question, rows)

        return jsonify({
            "question": question,
            "sql": sql,
            "rows": rows,
            "chart": chart_spec,
            "insight": insight,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)