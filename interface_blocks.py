import streamlit as st
import pandas as pd
from db_utils import insert_sales_from_csv, get_sales
from auth_utils import load_users, save_users, authenticate, get_user_profile
import os
import altair as alt
import tempfile
import pdfkit
import matplotlib.pyplot as plt
import base64
import shutil
from altair_saver import save as altair_save

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

def gerar_pdf_dashboard_diario(df_filtrado, kpis, chart_top_clientes, chart_vendas_tempo):
    # Salva gráficos como imagens temporárias
    tempdir = tempfile.mkdtemp()
    img_top_clientes = os.path.join(tempdir, 'top_clientes.png')
    img_vendas_tempo = os.path.join(tempdir, 'vendas_tempo.png')
    altair_save(chart_top_clientes, img_top_clientes, method='selenium')
    altair_save(chart_vendas_tempo, img_vendas_tempo, method='selenium')

    # Gera HTML estilizado
    html = f'''
    <html>
    <head>
    <style>
    body {{ font-family: Arial, sans-serif; margin: 40px; }}
    h1 {{ text-align: center; }}
    .kpis {{ display: flex; justify-content: space-around; margin-bottom: 30px; }}
    .kpi {{ background: #f2f2f2; border-radius: 10px; padding: 20px; text-align: center; width: 22%; }}
    .section {{ margin-bottom: 30px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; }}
    th {{ background: #eee; }}
    </style>
    </head>
    <body>
    <h1>Relatório Diário de Vendas</h1>
    <div class="kpis">
        <div class="kpi"><b>Total de Vendas</b><br>{kpis['total_vendas']}</div>
        <div class="kpi"><b>Clientes Únicos</b><br>{kpis['clientes_unicos']}</div>
        <div class="kpi"><b>Ticket Médio</b><br>R$ {kpis['ticket_medio']:,.2f}</div>
        <div class="kpi"><b>Total Vendido</b><br>R$ {kpis['total_vendido']:,.2f}</div>
    </div>
    <div class="section">
        <h2>Top 10 Clientes</h2>
        <img src="data:image/png;base64,{base64.b64encode(open(img_top_clientes, 'rb').read()).decode()}" width="700"/>
    </div>
    <div class="section">
        <h2>Vendas ao Longo do Tempo</h2>
        <img src="data:image/png;base64,{base64.b64encode(open(img_vendas_tempo, 'rb').read()).decode()}" width="700"/>
    </div>
    <div class="section">
        <h2>Tabela de Vendas Filtradas</h2>
        {df_filtrado.head(30).to_html(index=False)}
        <p style="font-size:12px;color:#888;">Exibindo as 30 primeiras linhas.</p>
    </div>
    </body>
    </html>
    '''
    # Salva HTML temporário
    html_path = os.path.join(tempdir, 'relatorio.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    # Gera PDF
    pdf_path = os.path.join(tempdir, 'relatorio.pdf')
    pdfkit.from_file(html_path, pdf_path)
    # Lê PDF para download
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    # Limpa arquivos temporários
    shutil.rmtree(tempdir)
    return pdf_bytes

def dashboard_diario(perfil):
    st.markdown("""
    <h1 style='text-align: center; margin-bottom: 0;'>📊 Dashboard Diário de Vendas</h1>
    <p style='text-align: center; color: #888; margin-top: 0;'>Acompanhe as vendas do dia de forma visual e interativa</p>
    """, unsafe_allow_html=True)
    st.divider()

    if perfil == "admin":
        with st.expander("📁 Upload de novo CSV", expanded=False):
            uploaded_file = st.file_uploader("Selecione um arquivo .csv", type="csv")
            if uploaded_file:
                df_novo = pd.read_csv(uploaded_file, sep=';', encoding='latin1')
                insert_sales_from_csv(df_novo)
                st.success("Arquivo carregado e dados inseridos com sucesso!")

    df = get_sales()
    if df.empty:
        st.warning("Nenhum dado disponível. Faça upload de um CSV.")
        return

    st.markdown("<h4>📅 Filtros</h4>", unsafe_allow_html=True)
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

    st.divider()

    # KPIs em cards
    st.markdown("<h4 style='margin-bottom:0;'>📌 Indicadores</h4>", unsafe_allow_html=True)
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total de Vendas", f"{df_filtrado['numero_venda'].nunique()}", help="Quantidade de vendas únicas no período filtrado.")
    kpi2.metric("Clientes Únicos", f"{df_filtrado['parceiro'].nunique()}", help="Quantidade de clientes diferentes.")
    ticket_medio = df_filtrado['valor'].sum() / max(df_filtrado['numero_venda'].nunique(), 1)
    kpi3.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}", help="Valor médio por venda.")
    kpi4, kpi5, kpi6 = st.columns(3)
    kpi4.metric("Total Vendido", f"R$ {df_filtrado['valor'].sum():,.2f}")
    kpi5.metric("Total Desconto", f"R$ {df_filtrado['Desconto'].astype(str).str.replace(',', '.').astype(float).sum():,.2f}")
    kpi6.metric("Total Acréscimo", f"R$ {df_filtrado['Acréscimo'].astype(str).str.replace(',', '.').astype(float).sum():,.2f}")
    st.write("")

    st.divider()

    # Gráfico: Top Clientes
    st.markdown("<h4>👥 Top 10 Clientes</h4>", unsafe_allow_html=True)
    top_clientes = df_filtrado.groupby('parceiro')['valor'].sum().sort_values(ascending=False).head(10).reset_index()
    if not top_clientes.empty:
        chart = alt.Chart(top_clientes).mark_bar().encode(
            x=alt.X('valor:Q', title='Valor Total'),
            y=alt.Y('parceiro:N', sort='-x', title='Cliente'),
            color=alt.value('#4F8DFD')
        ).properties(height=350)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Não há dados suficientes para exibir o gráfico de Top Clientes.")

    st.divider()

    # Gráfico: Evolução temporal
    st.markdown("<h4>📈 Vendas ao Longo do Tempo</h4>", unsafe_allow_html=True)
    vendas_tempo = df_filtrado.groupby('data_competencia')['valor'].sum().reset_index()
    if not vendas_tempo.empty:
        chart2 = alt.Chart(vendas_tempo).mark_line(point=True).encode(
            x=alt.X('data_competencia:T', title='Data'),
            y=alt.Y('valor:Q', title='Valor Total'),
            tooltip=['data_competencia', 'valor']
        ).properties(height=350)
        st.altair_chart(chart2, use_container_width=True)
    else:
        st.info("Não há dados suficientes para exibir o gráfico de evolução temporal.")

    st.divider()

    # Tabela de dados filtrados
    st.markdown("<h4>📄 Tabela de Vendas Filtradas</h4>", unsafe_allow_html=True)
    st.dataframe(df_filtrado, use_container_width=True, height=350)

    # Botão para gerar PDF
    if st.button("Baixar Relatório em PDF"):
        kpis = {
            'total_vendas': df_filtrado['numero_venda'].nunique(),
            'clientes_unicos': df_filtrado['parceiro'].nunique(),
            'ticket_medio': ticket_medio,
            'total_vendido': df_filtrado['valor'].sum()
        }
        pdf_bytes = gerar_pdf_dashboard_diario(df_filtrado, kpis, chart, chart2)
        st.download_button("Download do PDF", pdf_bytes, file_name="relatorio_diario.pdf", mime="application/pdf")

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
    st.markdown("""
    <h1 style='text-align: center; margin-bottom: 0;'>↩️ Dashboard de Devoluções</h1>
    <p style='text-align: center; color: #888; margin-top: 0;'>Acompanhe devoluções e cancelamentos</p>
    """, unsafe_allow_html=True)
    st.divider()
    df = get_sales()
    if df.empty:
        st.warning("Nenhum dado disponível.")
        return
    # Considera devolução se quantidade negativa ou operação contém DEVOLUCAO
    df['is_devolucao'] = (df['Quantidade'].astype(str).str.replace(',', '.').astype(float) < 0) | (df['Operação'].str.upper().str.contains('DEVOLUCAO'))
    df_dev = df[df['is_devolucao']]
    k1, k2 = st.columns(2)
    k1.metric("Total de Devoluções", len(df_dev))
    k2.metric("Valor Devolvido", f"R$ {df_dev['valor'].sum():,.2f}")
    st.divider()
    st.markdown("<h4>Devoluções ao Longo do Tempo</h4>", unsafe_allow_html=True)
    devolucoes_tempo = df_dev.groupby('data_competencia')['valor'].sum().reset_index()
    if not devolucoes_tempo.empty:
        chart = alt.Chart(devolucoes_tempo).mark_line(point=True, color='red').encode(
            x=alt.X('data_competencia:T', title='Data'),
            y=alt.Y('valor:Q', title='Valor Devolvido')
        )
        st.altair_chart(chart, use_container_width=True)
    st.divider()
    st.markdown("<h4>Top Clientes que Devolvem</h4>", unsafe_allow_html=True)
    top_dev = df_dev.groupby('parceiro')['valor'].sum().sort_values(ascending=False).head(10).reset_index()
    st.dataframe(top_dev, use_container_width=True)

# Dashboard de Transportadoras

def dashboard_transportadoras():
    st.markdown("""
    <h1 style='text-align: center; margin-bottom: 0;'>🚚 Dashboard de Transportadoras</h1>
    <p style='text-align: center; color: #888; margin-top: 0;'>Acompanhe o desempenho das transportadoras</p>
    """, unsafe_allow_html=True)
    st.divider()
    df = get_sales()
    if df.empty or 'Transportadora' not in df.columns:
        st.warning("Nenhum dado disponível.")
        return
    top_transp = df.groupby('Transportadora')['valor'].sum().sort_values(ascending=False).head(10).reset_index()
    st.markdown("<h4>Top Transportadoras por Valor</h4>", unsafe_allow_html=True)
    st.bar_chart(top_transp.set_index('Transportadora'))
    st.divider()
    st.markdown("<h4>Quantidade de Entregas por Transportadora</h4>", unsafe_allow_html=True)
    entregas = df['Transportadora'].value_counts().head(10)
    st.bar_chart(entregas)

# Dashboard de Condição de Pagamento

def dashboard_condicao_pagamento():
    st.markdown("""
    <h1 style='text-align: center; margin-bottom: 0;'>💳 Dashboard de Condição de Pagamento</h1>
    <p style='text-align: center; color: #888; margin-top: 0;'>Acompanhe as formas e condições de pagamento</p>
    """, unsafe_allow_html=True)
    st.divider()
    df = get_sales()
    if df.empty or 'Tipo da Condição' not in df.columns:
        st.warning("Nenhum dado disponível.")
        return
    st.markdown("<h4>Distribuição por Tipo de Condição</h4>", unsafe_allow_html=True)
    cond = df['Tipo da Condição'].value_counts().reset_index()
    cond.columns = ['Tipo da Condição', 'Quantidade']
    st.bar_chart(cond.set_index('Tipo da Condição'))
    st.divider()
    st.markdown("<h4>Ticket Médio por Condição</h4>", unsafe_allow_html=True)
    ticket = df.groupby('Tipo da Condição')['valor'].mean().sort_values(ascending=False).reset_index()
    st.dataframe(ticket, use_container_width=True) 