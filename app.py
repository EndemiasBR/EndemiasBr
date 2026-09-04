import os

import psycopg2
import streamlit as st

st.set_page_config(
    page_title="EndemiasBR",
    page_icon="🦟",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def obter_secret(chave, padrao=None):
    """Lê variável de ambiente ou Streamlit Secrets."""
    valor = os.getenv(chave)
    if valor not in (None, ""):
        return valor

    try:
        return st.secrets.get(chave, padrao)
    except Exception:
        return padrao


def conectar_banco():
    """Conecta ao PostgreSQL hospedado no Supabase."""
    try:
        host = obter_secret("DB_HOST")
        porta = obter_secret("DB_PORT", "6543")
        banco = obter_secret("DB_NAME", "postgres")
        usuario = obter_secret("DB_USER")
        senha = obter_secret("DB_PASSWORD")

        if not all([host, porta, banco, usuario, senha]):
            st.error(
                "Configuração incompleta do banco. Verifique os Secrets: "
                "DB_HOST, DB_PORT, DB_NAME, DB_USER e DB_PASSWORD."
            )
            return None

        return psycopg2.connect(
            host=host,
            port=int(porta),
            dbname=banco,
            user=usuario,
            password=senha,
            client_encoding="UTF8",
            connect_timeout=20,
            sslmode="require",
        )
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None


st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #eef9f1 0%, #ffffff 55%, #eaf7ef 100%);
    }

    .manutencao-box {
        max-width: 760px;
        margin: 13vh auto 0 auto;
        padding: 46px 38px;
        text-align: center;
        background: white;
        border: 1px solid #cce7d5;
        border-radius: 20px;
        box-shadow: 0 10px 28px rgba(0, 95, 59, 0.14);
    }

    .manutencao-box h1 {
        margin: 0;
        color: #006b3f;
        font-size: 42px;
        font-weight: 800;
    }

    .manutencao-box p {
        margin: 16px 0 0 0;
        color: #315443;
        font-size: 22px;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="manutencao-box">
        <h1>🦟 EndemiasBR</h1>
        <p>Estamos em manutenção.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
