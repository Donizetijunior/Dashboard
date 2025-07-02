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
            valor REAL
        )
    """)
    conn.commit()
    conn.close()

def insert_sales_from_csv(df):
    # Espera colunas padronizadas: data_competencia, numero_venda, parceiro, valor
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    inseridos = 0
    for _, row in df.iterrows():
        try:
            cursor.execute("""
                INSERT INTO vendas (data_competencia, numero_venda, parceiro, valor)
                VALUES (?, ?, ?, ?)
            """, (
                str(row.get('data_competencia', '')),
                str(row.get('numero_venda', '')),
                str(row.get('parceiro', '')),
                float(str(row.get('valor', 0)).replace(',', '.'))
            ))
            inseridos += 1
        except Exception as e:
            print(f"Erro ao inserir linha: {row.to_dict()} - Erro: {e}")
            continue
    conn.commit()
    conn.close()
    print(f"Total de vendas inseridas: {inseridos}")

def get_sales():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM vendas", conn)
    conn.close()
    return df 