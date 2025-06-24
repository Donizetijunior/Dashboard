# 📊 Dashboard de Vendas

Um dashboard profissional para análise de vendas, desenvolvido em **Python** com **Streamlit**, pronto para uso local ou em produção (VPS/Cloud). Permite upload diário de arquivos CSV, gestão de usuários e visualização de relatórios executivos.

---

## 🚀 Funcionalidades
- **Login seguro** (admin e usuário comum)
- **Upload diário de CSV** (acumula dados no banco SQLite)
- **Indicadores e gráficos dinâmicos**
- **Gestão de usuários** (admin)
- **Resumo executivo** (dados do PDF)
- **Download do relatório PDF**

---

## 🗂️ Estrutura do Projeto
```
Dash/
├── app.py                  # Interface principal Streamlit
├── db_utils.py             # Funções do banco de dados (SQLite)
├── auth_utils.py           # Funções de autenticação e usuários
├── interface_blocks.py     # Blocos de interface (login, dashboards, admin)
├── README.md               # Este arquivo
├── requirements.txt        # Dependências do projeto
├── data/
│   ├── vendas.db           # Banco de dados SQLite (gerado automaticamente)
│   └── usuarios.json       # Usuários cadastrados
├── Diario 23-06.csv        # Exemplo de CSV diário
└── Relatório de Vendas - Análise Completa.pdf  # Relatório executivo
```

---

## ⚙️ Instalação Local
1. **Clone o repositório:**
   ```bash
   git clone https://github.com/....
   cd pasta-clonada
   ```
2. **Crie o ambiente virtual:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Rode o app:**
   ```bash
   streamlit run app.py
   ```
5. **Acesse:**
   - Local: [http://localhost:8501](http://localhost:8501)

---

## ☁️ Deploy em VPS/Cloud
1. **Suba os arquivos para a VPS** (via Git, SFTP, SCP, etc)
2. **Siga os passos de instalação acima**
3. **Rode o Streamlit para acesso externo:**
   ```bash
   streamlit run app.py --server.address 0.0.0.0 --server.port 8501
   ```
4. **Libere a porta 8501 no firewall**
5. **Acesse pelo navegador:**
   - http://SEU_IP:8501

---

## 📥 Exemplo de CSV Aceito
O CSV deve conter pelo menos as colunas:
- `Data Competência`, `Nº Venda`, `Parceiro`, `Valor`

---

## 👤 Usuários Padrão
- **admin** / admin123  (acesso total)
- **usuario** / usuario123  (acesso comum)

---


 
