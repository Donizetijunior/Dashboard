import sqlite3
import pandas as pd
from pathlib import Path

DB_FILE = Path("data/vendas.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_competencia TEXT,
            numero_venda TEXT,
            parceiro TEXT,
            valor REAL,
            UNIQUE(numero_venda)
        )
    """)
    conn.commit()
    conn.close()

def insert_sales_from_csv(df):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    for _, row in df.iterrows():
        try:
            cursor.execute("""
                INSERT INTO vendas (data_competencia, numero_venda, parceiro, valor)
                VALUES (?, ?, ?, ?)
            """, (
                str(row.get('Data Competência', row.get('data_competencia', ''))),
                str(row.get('Nº Venda', row.get('numero_venda', ''))),
                str(row.get('Parceiro', row.get('parceiro', ''))),
                float(str(row.get('Valor', row.get('valor', 0))).replace(',', '.'))
            ))
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()

def get_sales():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM vendas", conn)
    conn.close()
    return df 