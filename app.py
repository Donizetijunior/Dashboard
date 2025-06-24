import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path
from db_utils import init_db, insert_sales_from_csv, get_sales
from auth_utils import authenticate, get_user_profile, load_users, save_users
from interface_blocks import (
    login_block, pagina_admin_usuarios, pagina_usuario, dashboard_diario, dashboard_total,
    dashboard_clientes, dashboard_produtos, dashboard_vendedores, dashboard_localizacao,
    dashboard_temporal, dashboard_devolucoes, dashboard_pagamento, dashboard_campanhas
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
    st.sidebar.success(f"Logado como: {st.session_state.usuario}")
    perfil = get_user_profile(st.session_state.usuario)
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.session_state.usuario = ''
        st.session_state.pagina = 'dashboard'
        st.experimental_rerun()

    dashboards = [
        "Relatório Diário",
        "Relatório Total",
        "Clientes",
        "Produtos",
        "Vendedores",
        "Localização",
        "Temporal",
        "Devoluções",
        "Formas de Pagamento",
        "Campanhas"
    ]
    st.sidebar.markdown("### Dashboards")
    for dash in dashboards:
        if st.sidebar.button(dash, key=f"btn_{dash}"):
            st.session_state.dashboard = dash
            st.session_state.pagina = 'dashboard'

    if perfil == "admin":
        st.sidebar.markdown("### Administração")
        if st.sidebar.button("Gerenciar Usuários", key="btn_admin_usuarios"):
            st.session_state.pagina = "admin_usuarios"
        if st.sidebar.button("Meu Perfil", key="btn_meu_perfil"):
            st.session_state.pagina = "usuario"
    else:
        st.sidebar.markdown("### Conta")
        if st.sidebar.button("Meu Perfil", key="btn_meu_perfil"):
            st.session_state.pagina = "usuario"

    # Renderização das páginas
    if st.session_state.pagina == "admin_usuarios" and perfil == "admin":
        pagina_admin_usuarios()
    elif st.session_state.pagina == "usuario":
        pagina_usuario()
    else:
        dash = st.session_state.dashboard
        if dash == "Relatório Diário":
            dashboard_diario(perfil)
        elif dash == "Relatório Total":
            dashboard_total()
        elif dash == "Clientes":
            dashboard_clientes()
        elif dash == "Produtos":
            dashboard_produtos()
        elif dash == "Vendedores":
            dashboard_vendedores()
        elif dash == "Localização":
            dashboard_localizacao()
        elif dash == "Temporal":
            dashboard_temporal()
        elif dash == "Devoluções":
            dashboard_devolucoes()
        elif dash == "Formas de Pagamento":
            dashboard_pagamento()
        elif dash == "Campanhas":
            dashboard_campanhas()
