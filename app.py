import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path
from db_utils import init_db, insert_sales_from_csv, get_sales
from auth_utils import authenticate, get_user_profile, load_users, save_users
from interface_blocks import login_block, admin_block, dashboard_diario, dashboard_total

# =====================
# Configurações Gerais
# =====================
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
USERS_FILE = DATA_DIR / "usuarios.json"
DB_FILE = DATA_DIR / "vendas.db"
PDF_FILE = "Relatório de Vendas - Análise Completa.pdf"

# =====================
# Usuários Iniciais
# =====================
USERS_DEFAULT = {
    "admin": {"senha": "admin123", "perfil": "admin"},
    "usuario": {"senha": "usuario123", "perfil": "comum"}
}

# =====================
# Sessão Streamlit
# =====================
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario = ''

# =====================
# Interface Principal
# =====================
if not st.session_state.logado:
    login_block()
else:
    st.sidebar.success(f"Logado como: {st.session_state.usuario}")
    perfil = get_user_profile(st.session_state.usuario)
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.session_state.usuario = ''
        st.experimental_rerun()
    menu = st.sidebar.selectbox("Escolha o relatório", ["Relatório Diário", "Relatório Total"])
    if menu == "Relatório Diário":
        dashboard_diario(perfil)
    elif menu == "Relatório Total":
        dashboard_total()
