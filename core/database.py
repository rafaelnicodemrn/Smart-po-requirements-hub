# core/database.py
import sqlite3
import os
from typing import List, Dict

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT_DIR, "hub_database.db")

def _get_connection() -> sqlite3.Connection:
    """Abre uma conexão com o SQLite e ativa o modo WAL para concorrência segura."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def inicializar_banco() -> None:
    """Cria a tabela inbox_demandas se não existir."""
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS inbox_demandas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                linha INTEGER,
                assunto TEXT,
                corpo TEXT,
                status TEXT DEFAULT 'Pendente'
            );
        """)
        conn.commit()

def salvar_demandas(lista_demandas: List[Dict[str, str]]) -> None:
    """Salva uma lista de novas demandas no banco com status 'Pendente'."""
    if not lista_demandas:
        return
    with _get_connection() as conn:
        cursor = conn.cursor()
        for demanda in lista_demandas:
            linha = demanda.get("row")
            assunto = demanda.get("assunto")
            corpo = demanda.get("corpo")
            if assunto and corpo:
                cursor.execute(
                    "INSERT INTO inbox_demandas (linha, assunto, corpo, status) VALUES (?, ?, ?, 'Pendente')",
                    (linha, assunto, corpo)
                )
        conn.commit()

def listar_pendentes() -> List[Dict]:
    """Retorna todas as demandas da caixa de entrada com status 'Pendente'."""
    with _get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, assunto, corpo, status FROM inbox_demandas WHERE status = 'Pendente'")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def marcar_como_processado(demanda_id: int) -> None:
    """Altera o status da demanda informada para 'Processado'."""
    with _get_connection() as conn:
        conn.execute("UPDATE inbox_demandas SET status = 'Processado' WHERE id = ?", (demanda_id,))
        conn.commit()
