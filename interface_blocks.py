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
import unicodedata

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

def padronizar_colunas(df):
    # Remove acentos e caracteres especiais, deixa tudo minúsculo e sem espaços
    def clean(col):
        col = unicodedata.normalize('NFKD', col).encode('ASCII', 'ignore').decode('ASCII')
        return col.strip().lower().replace(' ', '_').replace('.', '').replace('(', '_').replace(')', '_')
    cols = [clean(c) for c in df.columns]
    # Renomear duplicadas
    seen = {}
    new_cols = []
    for c in cols:
        if c not in seen:
            seen[c] = 0
            new_cols.append(c)
        else:
            seen[c] += 1
            new_cols.append(f"{c}_{seen[c]}")
    df.columns = new_cols
    # Mapeamento para garantir compatibilidade com o banco
    col_map = {
        'data_competencia': 'data_competencia',
        'data': 'data_competencia',
        'no_venda': 'numero_venda',
        'parceiro': 'parceiro',
        'valor': 'valor',
        'quantidade': 'quantidade',
        'vendedor': 'vendedor',
        'codigo': 'codigo',
        'operacao': 'operacao',
        'tipo_da_condicao': 'tipo_da_condicao',
        'transportadora': 'transportadora',
        'cidade_entrega': 'cidade_entrega',
        'uf_entrega': 'uf_entrega',
        'filial': 'filial',
        # ... adicione outros conforme necessário ...
    }
    df = df.rename(columns={c: col_map.get(c, c) for c in df.columns})
    return df

def sidebar_customizada(perfil):
    st.sidebar.markdown("""
    <style>
    .sidebar-title { font-size: 18px; font-weight: bold; margin-bottom: 8px; }
    .sidebar-section { margin-bottom: 18px; }
    </style>
    """, unsafe_allow_html=True)
    st.sidebar.success(f"<b>👤 Logado como:</b> <span style='color:#fff'>{st.session_state.usuario}</span>", icon="✅")
    st.sidebar.divider()
    st.sidebar.markdown('<div class="sidebar-title">📊 Dashboards</div>', unsafe_allow_html=True)
    dashboards = [
        ("Relatório Diário", "📅"),
        ("Clientes", "👥"),
        ("Temporal", "⏳"),
        ("Devoluções", "↩️"),
        ("Transportadoras", "🚚"),
        ("Condição de Pagamento", "💳")
    ]
    for dash, icone in dashboards:
        if st.sidebar.button(f"{icone} {dash}", key=f"btn_{dash}"):
            st.session_state.dashboard = dash
            st.session_state.pagina = 'dashboard'
    st.sidebar.divider()
    if perfil == "admin":
        st.sidebar.markdown('<div class="sidebar-title">⚙️ Administração</div>', unsafe_allow_html=True)
        if st.sidebar.button("👤 Gerenciar Usuários", key="btn_admin_usuarios"):
            st.session_state.pagina = "admin_usuarios"
        if st.sidebar.button("📝 Meu Perfil", key="btn_meu_perfil"):
            st.session_state.pagina = "usuario"
    else:
        st.sidebar.markdown('<div class="sidebar-title">👤 Conta</div>', unsafe_allow_html=True)
        if st.sidebar.button("📝 Meu Perfil", key="btn_meu_perfil"):
            st.session_state.pagina = "usuario"
    st.sidebar.divider()
    if st.sidebar.button("🚪 Sair", key="btn_sair"):
        st.session_state.logado = False
        st.session_state.usuario = ''
        st.session_state.pagina = 'dashboard'
        st.experimental_rerun()

def dashboard_diario(perfil):
    st.markdown("""
    <h1 style='text-align: left; margin-bottom: 0;'>📊 DASHBOARD DE VENDAS</h1>
    <p style='text-align: left; color: #888; margin-top: 0;'>Acompanhe as vendas do dia de forma visual e interativa</p>
    """, unsafe_allow_html=True)
    st.divider()

    if perfil == "admin":
        with st.expander("📁 Upload de novo CSV", expanded=False):
            uploaded_file = st.file_uploader("Selecione um arquivo .csv", type="csv")
            if uploaded_file:
                df_novo = pd.read_csv(uploaded_file, sep=';', encoding='latin1')
                df_novo = padronizar_colunas(df_novo)
                st.info(f"Colunas detectadas no CSV: {list(df_novo.columns)}")
                st.dataframe(df_novo.head(10), use_container_width=True)
                insert_sales_from_csv(df_novo)
                st.success("Arquivo carregado e dados inseridos com sucesso!")

    df = get_sales()
    if df.empty:
        st.warning("Nenhum dado disponível. Faça upload de um CSV.")
        return
    df = padronizar_colunas(df)
    st.info(f"Colunas no DataFrame após importação: {list(df.columns)}")
    st.dataframe(df.head(10), use_container_width=True)

    # Filtros laterais
    with st.sidebar:
        st.markdown("<b>Filtros</b>", unsafe_allow_html=True)
        anos = pd.to_datetime(df['data_competencia'], errors='coerce').dt.year.dropna().unique()
        ano_sel = st.selectbox("Ano", sorted(anos, reverse=True))
        meses = pd.to_datetime(df['data_competencia'], errors='coerce').dt.month_name(locale='pt_BR').unique()
        mes_sel = st.selectbox("Mês", meses)
        vendedores = df['vendedor'].dropna().unique() if 'vendedor' in df.columns else []
        vendedor_sel = st.multiselect("Vendedor", vendedores)
        clientes = df['parceiro'].dropna().unique()
        cliente_sel = st.multiselect("Cliente", clientes)
        produtos = df['codigo'].dropna().unique() if 'codigo' in df.columns else []
        produto_sel = st.multiselect("Produto", produtos)

    # Aplicar filtros
    df['data_competencia'] = pd.to_datetime(df['data_competencia'], errors='coerce')
    df = df[df['data_competencia'].dt.year == ano_sel]
    df = df[df['data_competencia'].dt.month_name(locale='pt_BR') == mes_sel]
    if vendedor_sel:
        df = df[df['vendedor'].isin(vendedor_sel)]
    if cliente_sel:
        df = df[df['parceiro'].isin(cliente_sel)]
    if produto_sel:
        df = df[df['codigo'].isin(produto_sel)]

    # KPIs
    col_kpi1, col_kpi2 = st.columns(2)
    faturamento_total = df['valor'].sum()
    qtd_produtos = df['quantidade'].astype(float).sum() if 'quantidade' in df.columns else 0
    col_kpi1.metric("Faturamento Total", f"R$ {faturamento_total:,.2f}")
    col_kpi2.metric("QTD Produtos Vendidos", f"{int(qtd_produtos)}")

    # Gráfico: Faturamento mensal x Meta
    st.markdown("<h4>Faturamento mensal x Meta</h4>", unsafe_allow_html=True)
    df['mes'] = df['data_competencia'].dt.strftime('%b')
    fat_mes = df.groupby('mes')['valor'].sum().reindex(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']).fillna(0)
    meta = [faturamento_total/len(fat_mes)]*len(fat_mes) if len(fat_mes) > 0 else []
    chart_fat = pd.DataFrame({'Faturamento': fat_mes, 'Meta': meta})
    st.bar_chart(chart_fat)

    # Gráfico: Vendas por produto (pizza)
    if 'codigo' in df.columns:
        st.markdown("<h4>Vendas de Produtos</h4>", unsafe_allow_html=True)
        prod_pizza = df.groupby('codigo')['quantidade'].sum().sort_values(ascending=False)
        st.pyplot(plt.pie(prod_pizza, labels=prod_pizza.index, autopct='%1.0f%%')[0].figure)

    # Gráfico: Vendas por cliente (barra horizontal)
    st.markdown("<h4>Vendas por clientes</h4>", unsafe_allow_html=True)
    top_clientes = df.groupby('parceiro')['valor'].sum().sort_values(ascending=False).head(10)
    st.bar_chart(top_clientes)

    # Gráfico: Faturamento por vendedor (barra horizontal)
    if 'vendedor' in df.columns:
        st.markdown("<h4>Faturamento por Vendedor</h4>", unsafe_allow_html=True)
        fat_vend = df.groupby('vendedor')['valor'].sum().sort_values(ascending=False)
        st.bar_chart(fat_vend)

    # Gráfico: Faturamento mensal (linha)
    st.markdown("<h4>Faturamento mensal</h4>", unsafe_allow_html=True)
    fat_mensal = df.groupby(df['data_competencia'].dt.month)['valor'].sum()
    st.line_chart(fat_mensal)

    st.divider()

    # KPIs em cards
    st.markdown("<h4 style='margin-bottom:0;'>📌 Indicadores</h4>", unsafe_allow_html=True)
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total de Vendas", f"{df['numero_venda'].nunique()}", help="Quantidade de vendas únicas no período filtrado.")
    kpi2.metric("Clientes Únicos", f"{df['parceiro'].nunique()}", help="Quantidade de clientes diferentes.")
    ticket_medio = df['valor'].sum() / max(df['numero_venda'].nunique(), 1)
    kpi3.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}", help="Valor médio por venda.")
    kpi4, kpi5, kpi6 = st.columns(3)
    total_vendido = df['valor'].sum()
    total_desconto = df['desconto'].astype(str).str.replace(',', '.').astype(float).sum() if 'desconto' in df.columns else 0
    total_acrescimo = df['acrescimo'].astype(str).str.replace(',', '.').astype(float).sum() if 'acrescimo' in df.columns else 0
    kpi4.metric("Total Vendido", f"R$ {total_vendido:,.2f}")
    kpi5.metric("Total Desconto", f"R$ {total_desconto:,.2f}")
    kpi6.metric("Total Acréscimo", f"R$ {total_acrescimo:,.2f}")
    st.write("")

    st.divider()

    # Gráfico: Top Clientes
    st.markdown("<h4>👥 Top 10 Clientes</h4>", unsafe_allow_html=True)
    top_clientes = df.groupby('parceiro')['valor'].sum().sort_values(ascending=False).head(10).reset_index()
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
    vendas_tempo = df.groupby('data_competencia')['valor'].sum().reset_index()
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
    st.dataframe(df, use_container_width=True, height=350)

    # Botão para gerar PDF
    if st.button("⬇️ Baixar Relatório em PDF"):
        kpis = {
            'total_vendas': df['numero_venda'].nunique(),
            'clientes_unicos': df['parceiro'].nunique(),
            'ticket_medio': ticket_medio,
            'total_vendido': total_vendido
        }
        pdf_bytes = gerar_pdf_dashboard_diario(df, kpis, chart, chart2)
        st.download_button("Download do PDF", pdf_bytes, file_name="relatorio_diario.pdf", mime="application/pdf")

    if perfil == "admin":
        st.divider()
        if st.button("👤 Ir para Gerenciar Usuários"):
            st.session_state.pagina = "admin_usuarios"
    else:
        if st.button("👤 Ver meu perfil"):
            st.session_state.pagina = "usuario"

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