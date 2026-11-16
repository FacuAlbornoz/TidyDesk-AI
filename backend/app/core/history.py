import json
from pathlib import Path
from typing import List, Optional
from app.config import HISTORY_FILE
from app.schemas.organize import TransactionRecord

def load_history() -> List[dict]:
    """Carga todas las transacciones históricas registradas."""
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def save_transaction(transaction: TransactionRecord) -> None:
    """Guarda una nueva transacción al inicio del archivo histórico."""
    history = load_history()
    history.insert(0, transaction.model_dump())
    # Mantener las últimas 100 transacciones
    history = history[:100]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def get_transaction(transaction_id: str) -> Optional[dict]:
    """Busca una transacción específica por su ID."""
    history = load_history()
    for tx in history:
        if tx.get("transaction_id") == transaction_id:
            return tx
    return None

def mark_transaction_reverted(transaction_id: str) -> bool:
    """Marca una transacción como revertida (deshecha)."""
    history = load_history()
    updated = False
    for tx in history:
        if tx.get("transaction_id") == transaction_id:
            tx["reverted"] = True
            updated = True
            break
    if updated:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    return updated
