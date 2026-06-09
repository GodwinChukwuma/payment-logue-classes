from __future__ import annotations

import os
import sqlite3
import threading
from contextlib import contextmanager
from typing import Optional, Any

_local = threading.local()
_DB_PATH = ":memory:"  # Default to in-memory database

def _get_connection() -> sqlite3.connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        _local.conn = conn
    return _local.conn

@contextmanager
def get_db():
    conn = _get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise

def init_db(db_path: str = ":memory:") -> None:
    global _DB_PATH
    _DB_PATH = db_path
    _local.conn = None
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_ref TEXT NOT NULL UNIQUE,
                pan_encrypted TEXT NOT NULL,
                pan_hmac TEXT NOT NULL,
                pan_masked TEXT NOT NULL,
                expiry_encrypted TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                client_ip TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
    """)
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_pan_hmac ON transactions(pan_hmac)""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_ref ON transactions(transaction_ref)""")

def insert_transaction(
        transaction_ref: str,
        pan_encrypted: str,
        pan_hmac: str,
        pan_masked: str,
        expiry_encrypted: str,
        amount: float,
        status: str,
        client_ip: Optional[str],
        created_at: str,
) -> int:
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO transactions
              (transaction_ref, pan_encrypted, pan_hmac, pan_masked, expiry_encrypted, amount, status, client_ip, created_at)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (transaction_ref, pan_encrypted, pan_hmac, pan_masked, expiry_encrypted, amount, status, client_ip, created_at)
        )
        return cursor.lastrowid

def get_transaction_by_ref(ref: str) -> Optional[sqlite3.Row]:
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM transactions WHERE transaction_ref = ?", (ref,))
        return cursor.fetchone()
    
def get_connetcion_info() -> dict:
    return {
        "engine":os.environ.get("DB_ENGINE", "sqlite"),
        "host":os.environ.get("DB_HOST", "localhost"),
        "port":os.environ.get("DB_PORT", "5432"),
        "database":os.environ.get("DB_NAME", "pci_transactions")
    }


