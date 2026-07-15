from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("SUPER_EXCEL_DATA_DIR", BASE_DIR / "data"))
DATABASE_PATH = Path(os.getenv("SUPER_EXCEL_DB", DATA_DIR / "super_excel.db"))
MAX_WORKBOOK_BYTES = 5 * 1024 * 1024

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
app.config["MAX_CONTENT_LENGTH"] = MAX_WORKBOOK_BYTES + 512 * 1024


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS workbooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def parse_workbook_payload(body: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    name = str(body.get("name", "")).strip()
    payload = body.get("data")

    if not name:
        raise ValueError("Informe um nome para a planilha.")
    if len(name) > 120:
        raise ValueError("O nome pode ter no máximo 120 caracteres.")
    if not isinstance(payload, dict):
        raise ValueError("Os dados da planilha são inválidos.")

    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > MAX_WORKBOOK_BYTES:
        raise ValueError("A planilha excede o limite de 5 MB.")

    return name, payload


@app.get("/")
def index() -> str:
    return render_template("index.html")


@app.get("/api/health")
def health() -> Any:
    return jsonify(
        {
            "status": "ok",
            "app": "Super Excel",
            "database": str(DATABASE_PATH),
            "mode": "online" if os.getenv("PORT") else "local",
        }
    )


@app.get("/api/workbooks")
def list_workbooks() -> Any:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, name, created_at, updated_at FROM workbooks ORDER BY updated_at DESC"
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.get("/api/workbooks/<int:workbook_id>")
def get_workbook(workbook_id: int) -> Any:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, name, payload, created_at, updated_at FROM workbooks WHERE id = ?",
            (workbook_id,),
        ).fetchone()

    if row is None:
        return jsonify({"error": "Planilha não encontrada."}), 404

    result = dict(row)
    result["data"] = json.loads(result.pop("payload"))
    return jsonify(result)


@app.post("/api/workbooks")
def save_workbook() -> Any:
    body = request.get_json(silent=True) or {}
    try:
        name, payload = parse_workbook_payload(body)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    workbook_id = body.get("id")
    timestamp = utc_now()
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    try:
        with get_connection() as connection:
            if workbook_id is not None:
                cursor = connection.execute(
                    """
                    UPDATE workbooks
                    SET name = ?, payload = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (name, encoded, timestamp, int(workbook_id)),
                )
                if cursor.rowcount == 0:
                    return jsonify({"error": "Planilha não encontrada."}), 404
                saved_id = int(workbook_id)
            else:
                cursor = connection.execute(
                    """
                    INSERT INTO workbooks (name, payload, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (name, encoded, timestamp, timestamp),
                )
                saved_id = int(cursor.lastrowid)
            connection.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Já existe uma planilha com esse nome."}), 409

    return jsonify({"id": saved_id, "name": name, "updated_at": timestamp})


@app.delete("/api/workbooks/<int:workbook_id>")
def delete_workbook(workbook_id: int) -> Any:
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM workbooks WHERE id = ?", (workbook_id,))
        connection.commit()

    if cursor.rowcount == 0:
        return jsonify({"error": "Planilha não encontrada."}), 404
    return jsonify({"deleted": True})


@app.errorhandler(413)
def request_too_large(_: Exception) -> Any:
    return jsonify({"error": "Requisição muito grande."}), 413


init_database()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
