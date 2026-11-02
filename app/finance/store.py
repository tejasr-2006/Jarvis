"""Local-only personal finance ledger; amounts are stored as integer minor units."""
from __future__ import annotations
import sqlite3
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from app.config import settings


def _db_path() -> Path:
    path = Path(settings.JARVIS_DATA_DIR).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path / "finance_ledger.db"


class FinanceStore:
    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path) if db_path else _db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY, kind TEXT NOT NULL CHECK(kind IN ('income','expense')),
                amount_minor INTEGER NOT NULL CHECK(amount_minor > 0),
                currency TEXT NOT NULL, category TEXT NOT NULL, description TEXT NOT NULL,
                transaction_date TEXT NOT NULL, created_at TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS budgets (
                id TEXT PRIMARY KEY, category TEXT NOT NULL, amount_minor INTEGER NOT NULL,
                currency TEXT NOT NULL, month TEXT NOT NULL,
                UNIQUE(category, currency, month))""")

    def _connect(self):
        db=sqlite3.connect(self.db_path,timeout=10)
        db.row_factory=sqlite3.Row
        return db

    @staticmethod
    def _tx(row):
        if not row: return None
        d=dict(row)
        d["amount"]=d.pop("amount_minor")/100
        return d

    def add_transaction(self, kind, amount_minor, currency, category, description, transaction_date):
        item={"id":uuid.uuid4().hex,"kind":kind,"amount_minor":amount_minor,
              "currency":currency,"category":category,"description":description,
              "transaction_date":transaction_date,
              "created_at":datetime.now(timezone.utc).isoformat(timespec="seconds")}
        with self._connect() as db:
            db.execute("INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?)",
              tuple(item[k] for k in ("id","kind","amount_minor","currency","category","description","transaction_date","created_at")))
        return self._tx(item)

    def list_transactions(self, month: str | None = None, limit: int = 100):
        query="SELECT * FROM transactions"
        args=[]
        if month:
            query+=" WHERE transaction_date LIKE ?";args.append(month+"%")
        query+=" ORDER BY transaction_date DESC, created_at DESC LIMIT ?";args.append(max(1,min(limit,500)))
        with self._connect() as db: rows=db.execute(query,args).fetchall()
        return [self._tx(r) for r in rows]

    def delete_transaction(self, tx_id: str) -> bool:
        with self._connect() as db:
            cur=db.execute("DELETE FROM transactions WHERE id=?",(tx_id,))
            return cur.rowcount>0

    def set_budget(self, category, amount_minor, currency, month):
        with self._connect() as db:
            db.execute("""INSERT INTO budgets(id,category,amount_minor,currency,month) VALUES(?,?,?,?,?)
                ON CONFLICT(category,currency,month) DO UPDATE SET amount_minor=excluded.amount_minor""",
                (uuid.uuid4().hex,category,amount_minor,currency,month))
            row=db.execute("SELECT * FROM budgets WHERE category=? AND currency=? AND month=?",(category,currency,month)).fetchone()
        return self._budget(row)

    @staticmethod
    def _budget(row):
        if not row:return None
        d=dict(row);d["amount"]=d.pop("amount_minor")/100
        return d

    def budgets(self, month: str):
        with self._connect() as db:
            rows=db.execute("SELECT * FROM budgets WHERE month=? ORDER BY category",(month,)).fetchall()
        return [self._budget(r) for r in rows]

    def summary(self, month: str, currency: str):
        with self._connect() as db:
            rows=db.execute("""SELECT kind, COALESCE(SUM(amount_minor),0) total
                FROM transactions WHERE transaction_date LIKE ? AND currency=? GROUP BY kind""",(month+"%",currency)).fetchall()
            category_rows=db.execute("""SELECT category, SUM(amount_minor) total FROM transactions
                WHERE transaction_date LIKE ? AND currency=? AND kind='expense' GROUP BY category""",(month+"%",currency)).fetchall()
        totals={r["kind"]:r["total"]/100 for r in rows}
        budgets=self.budgets(month)
        expenses={r["category"]:r["total"]/100 for r in category_rows}
        return {"month":month,"currency":currency,"income":totals.get("income",0.0),
                "expenses":totals.get("expense",0.0),
                "net":round(totals.get("income",0.0)-totals.get("expense",0.0),2),
                "expenses_by_category":expenses,
                "budgets":[{**b,"spent":expenses.get(b["category"],0.0),
                            "remaining":round(b["amount"]-expenses.get(b["category"],0.0),2)}
                           for b in budgets]}
