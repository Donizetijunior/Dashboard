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
import numpy as np

def login_block():
    st.title("🔐 Login")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if authenticate(username, password):
            st.session_state.logado = True
            st.session_state.usuario = username
            # Usar st.rerun() se disponível, senão fallback para st.experimental_rerun()
            try:
                st.rerun()
            except AttributeError:
                try:
                    st.experimental_rerun()
                except AttributeError:
                    pass
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
    # Mapeamento completo para todos os campos do CSV
    col_map = {
        'data_competencia': 'data_competencia',
        'hora': 'hora',
        'no_venda': 'numero_venda',
        'no_nf': 'numero_nf',
        'codigo': 'codigo_produto',
        'codigo_1': 'codigo_aux1',
        'codigo_2': 'codigo_aux2',
        'parceiro': 'parceiro',
        'quantidade': 'quantidade',
        'qtd': 'quantidade',
        'acrescimo': 'acrescimo',
        'desconto': 'desconto',
        'total': 'total',
        'desp_acess': 'desp_acess',
        'valor_frete_cif': 'valor_frete_cif',
        'valor_seguro': 'valor_seguro',
        'valor_seguro_1': 'valor_seguro_1',
        'total_venda': 'total_venda',
        'percentual_desc': 'percentual_desc',
        'total_preco_base': 'total_preco_base',
        'operacao': 'operacao',
        'n_d': 'n_d',
        'n_e': 'n_e',
        'c': 'c',
        'no_c_fiscal': 'numero_c_fiscal',
        'no_vendedor': 'numero_vendedor',
        'vendedor': 'vendedor',
        'tipo_da_condicao': 'tipo_da_condicao',
        'tipodacondicao': 'tipo_da_condicao',
        'tipo_condicao': 'tipo_da_condicao',
        'tipo_da_condicao_1': 'tipo_da_condicao',
        'data_saida': 'data_saida',
        'forma': 'forma_pagamento',
        'transportadora': 'transportadora',
        'tipo_frete': 'tipo_frete',
        'valor_frete': 'valor_frete',
        'placa': 'placa',
        'uf_placa': 'uf_placa',
        'especie': 'especie',
        'marca': 'marca',
        'quantidade_volume': 'quantidade_volume',
        'peso_bruto': 'peso_bruto',
        'peso_liquido': 'peso_liquido',
        'obs': 'obs',
        'no_loja_cf': 'numero_loja_cf',
        'no_cx_cf': 'numero_cx_cf',
        'no_serie_imp_cf': 'numero_serie_imp_cf',
        'endereco_entrega': 'endereco_entrega',
        'bairro_entrega': 'bairro_entrega',
        'cidade_entrega': 'cidade_entrega',
        'cep_entrega': 'cep_entrega',
        'uf_entrega': 'uf_entrega',
        'filial': 'filial',
        'operador': 'operador',
        'operador_cancelamento': 'operador_cancelamento',
        'cod': 'cod',
        'nome_motorista': 'nome_motorista',
        'operador_entrega': 'operador_entrega',
        'data_entrega': 'data_entrega',
        'nome_autorizado': 'nome_autorizado',
        'sit_email': 'sit_email',
        'n_pedido': 'numero_pedido',
        'obra': 'obra',
        'desc_obra': 'desc_obra',
        'no_despacho': 'numero_despacho',
        # Adicione outros campos conforme necessário
    }
    df = df.rename(columns={c: col_map.get(c, c) for c in df.columns})
    # Garante que todas as colunas do mapeamento existam, mesmo que vazias
    for col in col_map.values():
        if col not in df.columns:
            df[col] = ''
    return df

def sidebar_customizada(perfil):
    st.sidebar.markdown("""
    <style>
    .sidebar-title { font-size: 18px; font-weight: bold; margin-bottom: 8px; }
    .sidebar-section { margin-bottom: 18px; }
    </style>
    """, unsafe_allow_html=True)
    st.sidebar.markdown(f"<div style='background:#198754;padding:10px;border-radius:8px;color:#fff;font-weight:bold;'>✅ <b>👤 Logado como:</b> {st.session_state.usuario}</div>", unsafe_allow_html=True)
    st.sidebar.divider()
    st.sidebar.markdown('<div class="sidebar-title">📊 Dashboards</div>', unsafe_allow_html=True)
    dashboards = [
        ("Relatório Diário", "📅"),
        ("Clientes", "👥"),
        ("Temporal", "⏳"),
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
    <style>
    .kpi-card {
        background: #23272f;
        border-radius: 12px;
        padding: 24px 16px 16px 16px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px #0002;
        text-align: center;
        color: #fff;
    }
    .kpi-title {
        font-size: 16px;
        color: #b0b8c1;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: bold;
        margin-bottom: 0;
    }
    .kpi-icon {
        font-size: 2rem;
        margin-bottom: 4px;
        display: block;
    }
    .card-section {
        background: #23272f;
        border-radius: 12px;
        padding: 18px 18px 10px 18px;
        margin-bottom: 18px;
        box-shadow: 0 2px 8px #0002;
        color: #fff;
    }
    .section-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 10px;
        color: #f8f9fa;
    }
    </style>
    <h1 style='text-align: left; margin-bottom: 0; color:#fff;'>📊 DASHBOARD DE VENDAS</h1>
    <p style='text-align: left; color: #b0b8c1; margin-top: 0;'>Acompanhe as vendas do dia de forma visual e interativa</p>
    """, unsafe_allow_html=True)
    st.divider()

    if perfil == "admin":
        with st.expander("📁 Upload de novo CSV", expanded=False):
            uploaded_file = st.file_uploader("Selecione um arquivo .csv", type="csv")
            if uploaded_file:
                df_novo = pd.read_csv(uploaded_file, sep=';', encoding='latin1')
                df_novo = padronizar_colunas(df_novo)
                insert_sales_from_csv(df_novo)
                st.success("Arquivo carregado e dados inseridos com sucesso!")

    df = get_sales()
    if df.empty:
        st.warning("Nenhum dado disponível. Faça upload de um CSV.")
        return
    df = padronizar_colunas(df)
    # Garantir que data_competencia é datetime antes de usar .dt
    df['data_competencia'] = pd.to_datetime(df['data_competencia'], errors='coerce')

    # KPIs em cards
    kpi1, kpi2, kpi3 = st.columns(3)
    faturamento_total = pd.to_numeric(df['valor'], errors='coerce').fillna(0).sum() if 'valor' in df.columns else 0
    qtd_produtos = pd.to_numeric(df['quantidade'], errors='coerce').fillna(0).sum() if 'quantidade' in df.columns else 0
    ticket_medio = faturamento_total / max(df['numero_venda'].nunique(), 1)
    with kpi1:
        st.markdown(f"""
        <div class='kpi-card'>
            <span class='kpi-icon'>💰</span>
            <div class='kpi-title'>Faturamento Total</div>
            <div class='kpi-value'>R$ {faturamento_total:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""
        <div class='kpi-card'>
            <span class='kpi-icon'>📦</span>
            <div class='kpi-title'>Produtos Vendidos</div>
            <div class='kpi-value'>{int(qtd_produtos)}</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"""
        <div class='kpi-card'>
            <span class='kpi-icon'>🧾</span>
            <div class='kpi-title'>Ticket Médio</div>
            <div class='kpi-value'>R$ {ticket_medio:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráficos em cards
    colg1, colg2 = st.columns(2)
    with colg1:
        st.markdown("<div class='card-section'><div class='section-title'>Faturamento Mensal x Meta</div>", unsafe_allow_html=True)
        # Garantir datetime antes de usar .dt
        df['data_competencia'] = pd.to_datetime(df['data_competencia'], errors='coerce')
        df['mes'] = df['data_competencia'].dt.strftime('%b')
        fat_mes = df.groupby('mes')['valor'].sum().reindex(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']).fillna(0)
        meta = [faturamento_total/len(fat_mes)]*len(fat_mes) if len(fat_mes) > 0 else []
        chart_fat = pd.DataFrame({'Faturamento': fat_mes, 'Meta': meta})
        st.bar_chart(chart_fat, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with colg2:
        st.markdown("<div class='card-section'><div class='section-title'>Vendas de Produtos</div>", unsafe_allow_html=True)
        df['quantidade_num'] = pd.to_numeric(df['quantidade'], errors='coerce').fillna(0)
        prod_pizza = df.groupby('codigo_produto')['quantidade_num'].sum()
        prod_pizza = prod_pizza[prod_pizza > 0]
        if not prod_pizza.empty:
            st.pyplot(plt.pie(prod_pizza, labels=prod_pizza.index, autopct='%1.0f%%')[0].figure)
        else:
            st.info('Nenhum dado de produto para exibir.')
        st.markdown("</div>", unsafe_allow_html=True)

    colg3, colg4 = st.columns(2)
    with colg3:
        st.markdown("<div class='card-section'><div class='section-title'>Vendas por Clientes</div>", unsafe_allow_html=True)
        top_clientes = df.groupby('parceiro')['valor'].sum().sort_values(ascending=False).head(10)
        if not top_clientes.empty:
            st.bar_chart(top_clientes, use_container_width=True)
        else:
            st.info('Nenhum dado de cliente para exibir.')
        st.markdown("</div>", unsafe_allow_html=True)
    with colg4:
        st.markdown("<div class='card-section'><div class='section-title'>Faturamento por Vendedor</div>", unsafe_allow_html=True)
        if 'vendedor' in df.columns:
            fat_vend = df.groupby('vendedor')['valor'].sum().sort_values(ascending=False)
            if not fat_vend.empty:
                st.bar_chart(fat_vend, use_container_width=True)
            else:
                st.info('Nenhum dado de vendedor para exibir.')
        else:
            st.info('Nenhum dado de vendedor para exibir.')
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card-section'><div class='section-title'>Faturamento Mensal</div>", unsafe_allow_html=True)
    # Garantir datetime antes de usar .dt
    df['data_competencia'] = pd.to_datetime(df['data_competencia'], errors='coerce')
    fat_mensal = df.groupby(df['data_competencia'].dt.month)['valor'].sum()
    if not fat_mensal.empty:
        st.line_chart(fat_mensal, use_container_width=True)
    else:
        st.info('Nenhum dado mensal para exibir.')
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card-section'><div class='section-title'>Tabela de Vendas</div>", unsafe_allow_html=True)
    st.dataframe(df[['data_competencia','numero_venda','parceiro','valor','quantidade','vendedor','tipo_da_condicao','forma_pagamento','cidade_entrega','filial']].head(30), use_container_width=True, height=350)
    st.markdown("</div>", unsafe_allow_html=True)

    # Botão para gerar PDF
    if st.button("⬇️ Baixar Relatório em PDF"):
        kpis = {
            'total_vendas': df['numero_venda'].nunique(),
            'clientes_unicos': df['parceiro'].nunique(),
            'ticket_medio': ticket_medio,
            'total_vendido': faturamento_total
        }
        pdf_bytes = gerar_pdf_dashboard_diario(df, kpis, chart_fat, fat_mensal)
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
    df['is_devolucao'] = (pd.to_numeric(df['quantidade'], errors='coerce').fillna(0) < 0) | (df['operacao'].str.upper().str.contains('DEVOLUCAO'))
    df_dev = df[df['is_devolucao']]
    k1, k2 = st.columns(2)
    k1.metric("Total de Devoluções", len(df_dev))
    k2.metric("Valor Devolvido", f"R$ {pd.to_numeric(df_dev['valor'], errors='coerce').fillna(0).sum():,.2f}")
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
    if df.empty or ('tipo_da_condicao' not in df.columns and 'forma_pagamento' not in df.columns):
        st.warning("Nenhum dado disponível.")
        return
    st.markdown("<h4>Distribuição por Tipo de Condição</h4>", unsafe_allow_html=True)
    if 'tipo_da_condicao' in df.columns and df['tipo_da_condicao'].str.strip().any():
        cond = df['tipo_da_condicao'].value_counts().reset_index()
        cond.columns = ['Tipo da Condição', 'Quantidade']
        st.bar_chart(cond.set_index('Tipo da Condição'))
    else:
        st.info("Nenhum dado para 'Tipo da Condição'.")
    st.divider()
    st.markdown("<h4>Distribuição por Forma de Pagamento</h4>", unsafe_allow_html=True)
    if 'forma_pagamento' in df.columns and df['forma_pagamento'].str.strip().any():
        forma = df['forma_pagamento'].value_counts().reset_index()
        forma.columns = ['Forma de Pagamento', 'Quantidade']
        st.bar_chart(forma.set_index('Forma de Pagamento'))
    else:
        st.info("Nenhum dado para 'Forma de Pagamento'.")
    st.divider()
    st.markdown("<h4>Ticket Médio por Condição</h4>", unsafe_allow_html=True)
    if 'tipo_da_condicao' in df.columns and df['tipo_da_condicao'].str.strip().any():
        ticket = df.groupby('tipo_da_condicao')['valor'].mean().sort_values(ascending=False).reset_index()
        st.dataframe(ticket, use_container_width=True) 