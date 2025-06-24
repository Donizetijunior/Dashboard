import streamlit as st
import pandas as pd
from db_utils import insert_sales_from_csv, get_sales
from auth_utils import load_users, save_users, authenticate, get_user_profile
import os

def login_block():
    st.title("🔐 Login")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if authenticate(username, password):
            st.session_state.logado = True
            st.session_state.usuario = username
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos.")

def pagina_usuario():
    st.title("👤 Meu Perfil")
    usuario = st.session_state.usuario
    perfil = get_user_profile(usuario)
    st.markdown(f"**Usuário:** `{usuario}`")
    st.markdown(f"**Perfil:** `{perfil}`")
    st.info("Entre em contato com o administrador para alterar seus dados.")

def pagina_admin_usuarios():
    st.title("👤 Gerenciar Usuários")
    users = load_users()
    st.markdown("**Usuários cadastrados:**")
    for user, info in users.items():
        st.markdown(f"- **{user}** ({info['perfil']})")
    st.divider()
    st.subheader("Adicionar novo usuário")
    new_user = st.text_input("Novo usuário")
    new_pass = st.text_input("Senha", type="password")
    new_profile = st.selectbox("Perfil", ["admin", "comum"])
    if st.button("Adicionar usuário"):
        if new_user in users:
            st.warning("Usuário já existe.")
        else:
            users[new_user] = {"senha": new_pass, "perfil": new_profile}
            save_users(users)
            st.success("Usuário adicionado com sucesso!")

def dashboard_diario(perfil):
    st.title("📊 Dashboard de Vendas - Diário")
    if perfil == "admin":
        st.subheader("📁 Upload de novo CSV")
        uploaded_file = st.file_uploader("Selecione um arquivo .csv", type="csv")
        if uploaded_file:
            df_novo = pd.read_csv(uploaded_file, sep=';', encoding='latin1')
            insert_sales_from_csv(df_novo)
            st.success("Arquivo carregado e dados inseridos com sucesso!")

    df = get_sales()
    if df.empty:
        st.warning("Nenhum dado disponível. Faça upload de um CSV.")
        return

    st.subheader("📅 Filtros")
    col1, col2 = st.columns(2)
    datas = pd.to_datetime(df['data_competencia'], errors='coerce')
    data_min, data_max = datas.min(), datas.max()
    data_inicio = col1.date_input("Data inicial", value=data_min, min_value=data_min, max_value=data_max)
    data_fim = col2.date_input("Data final", value=data_max, min_value=data_min, max_value=data_max)

    parceiros = df['parceiro'].dropna().unique()
    parceiro_sel = st.multiselect("Filtrar por cliente (opcional)", parceiros)

    df['data_competencia'] = pd.to_datetime(df['data_competencia'], errors='coerce')
    df_filtrado = df[(df['data_competencia'] >= pd.to_datetime(data_inicio)) &
                     (df['data_competencia'] <= pd.to_datetime(data_fim))]
    if parceiro_sel:
        df_filtrado = df_filtrado[df_filtrado['parceiro'].isin(parceiro_sel)]

    st.subheader("📌 Indicadores")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Vendas", f"{df_filtrado['numero_venda'].nunique()}")
    col2.metric("Clientes Únicos", f"{df_filtrado['parceiro'].nunique()}")
    ticket_medio = df_filtrado['valor'].sum() / max(df_filtrado['numero_venda'].nunique(), 1)
    col3.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")

    st.subheader("👥 Top Clientes")
    top_clientes = df_filtrado.groupby('parceiro')['valor'].sum().sort_values(ascending=False).head(10)
    st.bar_chart(top_clientes)

    st.subheader("📈 Vendas ao longo do tempo")
    vendas_tempo = df_filtrado.groupby('data_competencia')['valor'].sum()
    st.line_chart(vendas_tempo)

    st.subheader("📄 Tabela de Vendas")
    st.dataframe(df_filtrado)

    # Botão para acessar a página de administração de usuários (apenas admin)
    if perfil == "admin":
        st.divider()
        if st.button("Ir para Gerenciar Usuários"):
            st.session_state.pagina = "admin_usuarios"
    else:
        if st.button("Ver meu perfil"):
            st.session_state.pagina = "usuario"

def dashboard_total():
    st.title("Resumo Executivo")
    resumo = {
        "total_vendas": 680,
        "clientes_unicos": 157,
        "valor_total": 2308260.56,
        "ticket_medio": 3394.50,
        "ticket_primeira": 2522.56,
        "clientes_novos_mes": {
            "Janeiro 2025": 6,
            "Fevereiro 2025": 16,
            "Março 2025": 29,
            "Abril 2025": 42,
            "Maio 2025": 47,
            "Junho 2025": 17
        }
    }
    st.metric("Total de Vendas", resumo["total_vendas"])
    st.metric("Clientes Únicos", resumo["clientes_unicos"])
    st.metric("Valor Total de Vendas", f'R$ {resumo["valor_total"]:,.2f}')
    st.metric("Ticket Médio Geral", f'R$ {resumo["ticket_medio"]:,.2f}')
    st.metric("Ticket Médio Primeira Compra", f'R$ {resumo["ticket_primeira"]:,.2f}')
    st.subheader("Leads Novos por Mês")
    st.table(pd.DataFrame(list(resumo["clientes_novos_mes"].items()), columns=["Mês", "Novos Clientes"]))
    st.info("Para mais detalhes, consulte o PDF completo.")
    if os.path.exists('Relatório de Vendas - Análise Completa.pdf'):
        with open('Relatório de Vendas - Análise Completa.pdf', 'rb') as pdf_file:
            st.download_button("Baixar Relatório Completo (PDF)", pdf_file, file_name='Relatório de Vendas - Análise Completa.pdf')
    else:
        st.warning("Arquivo PDF não encontrado.")

# ========== Dashboards Temáticos ==========

def dashboard_clientes():
    st.title("👥 Dashboard de Clientes")
    df = get_sales()
    if df.empty:
        st.warning("Nenhum dado disponível.")
        return
    st.metric("Clientes Únicos", df['parceiro'].nunique())
    st.metric("Novos Clientes (estimado)", df['parceiro'].value_counts().loc[lambda x: x == 1].count())
    st.subheader("Novos Clientes por Data")
    novos = df.groupby('data_competencia')['parceiro'].nunique()
    st.line_chart(novos)
    st.subheader("Top Clientes")
    st.bar_chart(df.groupby('parceiro')['valor'].sum().sort_values(ascending=False).head(10))


def dashboard_produtos():
    st.title("📦 Dashboard de Produtos")
    st.info("Este dashboard depende de dados de produtos no CSV. Adapte conforme necessário.")
    st.warning("Colunas de produto não encontradas no banco de dados.")


def dashboard_vendedores():
    st.title("🧑‍💼 Dashboard de Vendedores")
    st.info("Este dashboard depende de dados de vendedor no CSV. Adapte conforme necessário.")
    st.warning("Colunas de vendedor não encontradas no banco de dados.")


def dashboard_localizacao():
    st.title("🌎 Dashboard de Localização")
    st.info("Este dashboard depende de dados de localização no CSV. Adapte conforme necessário.")
    st.warning("Colunas de localização não encontradas no banco de dados.")


def dashboard_temporal():
    st.title("📅 Dashboard Temporal")
    df = get_sales()
    if df.empty:
        st.warning("Nenhum dado disponível.")
        return
    st.subheader("Vendas por Dia")
    vendas_dia = df.groupby('data_competencia')['valor'].sum()
    st.line_chart(vendas_dia)
    st.subheader("Vendas por Mês")
    df['mes'] = pd.to_datetime(df['data_competencia'], errors='coerce').dt.to_period('M')
    vendas_mes = df.groupby('mes')['valor'].sum()
    st.bar_chart(vendas_mes)


def dashboard_devolucoes():
    st.title("↩️ Dashboard de Devoluções/Cancelamentos")
    st.info("Este dashboard depende de dados de devolução/cancelamento no CSV. Adapte conforme necessário.")
    st.warning("Colunas de devolução/cancelamento não encontradas no banco de dados.")


def dashboard_pagamento():
    st.title("💳 Dashboard de Formas de Pagamento")
    st.info("Este dashboard depende de dados de pagamento no CSV. Adapte conforme necessário.")
    st.warning("Colunas de forma de pagamento não encontradas no banco de dados.")


def dashboard_campanhas():
    st.title("📢 Dashboard de Campanhas/Promoções")
    st.info("Este dashboard depende de dados de campanhas no CSV. Adapte conforme necessário.")
    st.warning("Colunas de campanha/promoção não encontradas no banco de dados.") 