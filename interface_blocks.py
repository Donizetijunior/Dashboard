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