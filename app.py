import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path
from db_utils import init_db, insert_sales_from_csv, get_sales
from auth_utils import authenticate, get_user_profile, load_users, save_users
from interface_blocks import (
    login_block, pagina_admin_usuarios, pagina_usuario, dashboard_diario,
    dashboard_clientes, dashboard_temporal, dashboard_devolucoes, dashboard_transportadoras, dashboard_condicao_pagamento,
    sidebar_customizada
)

# =====================
# Inicialização do banco de dados
# =====================
init_db()

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
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'dashboard'
if 'dashboard' not in st.session_state:
    st.session_state.dashboard = 'Relatório Diário'

# =====================
# Interface Principal
# =====================
if not st.session_state.logado:
    login_block()
else:
    perfil = get_user_profile(st.session_state.usuario)
    sidebar_customizada(perfil)
    # Renderização das páginas
    if st.session_state.pagina == "admin_usuarios" and perfil == "admin":
        pagina_admin_usuarios()
    elif st.session_state.pagina == "usuario":
        pagina_usuario()
    else:
        dash = st.session_state.dashboard
        if dash == "Relatório Diário":
            dashboard_diario(perfil)
        elif dash == "Clientes":
            dashboard_clientes()
        elif dash == "Temporal":
            dashboard_temporal()
        elif dash == "Devoluções":
            dashboard_devolucoes()
        elif dash == "Transportadoras":
            dashboard_transportadoras()
        elif dash == "Condição de Pagamento":
            dashboard_condicao_pagamento()
