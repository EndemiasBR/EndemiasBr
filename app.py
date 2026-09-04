import streamlit as st
import psycopg2
import pandas as pd
from datetime import date
import os
import re
import hashlib
import base64
import secrets
import json
from datetime import timedelta, datetime
import extra_streamlit_components as stx

# =========================================================
# CONTROLE CENTRAL DA SIMULACAO
# =========================================================

MODO_SIMULACAO = True

st.set_page_config(
    page_title="EndemiasBR",
    page_icon="🦟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# SESSAO PERSISTENTE DE LOGIN (COOKIES)
# =========================================================

COOKIES = stx.CookieManager()
NOME_COOKIE_SESSAO = "endemiasbr_session"
DIAS_SESSAO = 30
NOME_COOKIE_NAVEGACAO = "endemiasbr_navigation"

CHAVES_NAVEGACAO_PERSISTENTE = (
    "pagina", "modulo", "modulo_inicio", "config_aberta", "atividades_aberta",
    "atividade_aba", "contato_aberto", "contato_aba", "menu_sisloc", "pcdch_menu",
    "pcdch_sub", "pce_menu", "pce_group", "pce_rel_sub", "pce_sub", "cad_aux_menu",
    "cad_aux_item", "pcl_doenca", "pcl_menu", "pcl_sub",
)

# =========================================================
# CSS - BOTONES MODERNOS E VISUAL OTIMIZADO
# =========================================================

st.markdown(
    """
    <style>
    /* Sidebar - Visual Moderno com Gradiente */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #005f3b 0%, #00452c 100%);
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Botoes principais - Gradiente moderno com sombra 3D */
    [data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #00c853, #009688) !important;
        color: white !important;
        border: 1.5px solid #ffd700 !important;
        border-radius: 10px !important;
        height: 48px !important;
        font-weight: 700 !important;
        text-align: left !important;
        padding-left: 18px !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15), 0 2px 4px rgba(0,0,0,0.1) !important;
        transition: all 0.2s ease !important;
        margin-bottom: 6px !important;
        font-size: 14px !important;
    }
    
    /* Hover effect - Levanta e brilha */
    [data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(135deg, #00e676, #00bfa5) !important;
        border-color: #ffe082 !important;
        color: white !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 14px rgba(0,0,0,0.2), 0 3px 6px rgba(0,0,0,0.12) !important;
    }
    
    /* Submenus - Hierarquia visual clara */
    [data-testid="stSidebar"] .sidebar-submenu .stButton > button {
        background: linear-gradient(135deg, #008f36, #007b31) !important;
        height: 40px !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        border-color: rgba(255,215,0,0.75) !important;
        padding-left: 14px !important;
        margin-bottom: 5px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    [data-testid="stSidebar"] .sidebar-submenu .stButton > button:hover {
        background: linear-gradient(135deg, #00a63c, #008f36) !important;
        border-color: #ffd700 !important;
        transform: translateY(-1px) !important;
    }
    
    /* Elementos da sidebar */
    .sidebar-brand {
        font-size: 24px;
        font-weight: 800;
        letter-spacing: 0.4px;
        padding: 8px 10px 4px 10px;
        color: #ffd700 !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .sidebar-user {
        padding: 8px 10px 14px 10px;
        border-bottom: 1px solid rgba(255,255,255,0.15);
        margin-bottom: 14px;
        background: rgba(255,255,255,0.05);
        border-radius: 8px;
    }
    
    .sidebar-user strong {
        display: block;
        font-size: 15px;
        font-weight: 700;
    }
    
    .sidebar-user span {
        display: block;
        font-size: 12px;
        opacity: 0.85;
        margin-top: 4px;
        color: #c8e6c9 !important;
    }
    
    .sidebar-section {
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 1.4px;
        opacity: 0.65;
        padding: 14px 12px 8px 12px;
        text-transform: uppercase;
    }
    
    .sidebar-submenu {
        margin: 4px 0 10px 10px;
        padding-left: 12px;
        border-left: 2px solid rgba(255,215,0,0.7);
    }
    
    .sidebar-module-active {
        font-size: 19px;
        font-weight: 800;
        padding: 10px 12px 16px 12px;
        border-bottom: 1px solid rgba(255,255,255,0.15);
        margin-bottom: 12px;
        color: #ffd700 !important;
    }
    
    .sidebar-spacer {
        min-height: 140px;
    }
    
    .sidebar-footer-line {
        height: 1px;
        background: rgba(255,255,255,0.15);
        margin: 10px 0 12px 0;
    }
    
    /* Area principal */
    .main {
        background: linear-gradient(180deg, #f0fff4 0%, #ffffff 100%);
    }
    
    h1, h2, h3 {
        color: #006B3F !important;
    }
    
    .module-header {
        padding: 20px 26px;
        border-radius: 14px;
        margin-bottom: 22px;
        background: linear-gradient(135deg, #006B3F, #009C3B);
        border-left: 7px solid #FFD700;
        box-shadow: 0 3px 8px rgba(0,0,0,0.12);
    }
    
    .module-header h1 {
        color: white !important;
        margin: 0;
        font-size: 30px;
        font-weight: 800;
    }
    
    .module-header p {
        margin: 6px 0 0 0;
        font-size: 16px;
        color: #FFE082 !important;
    }
    
    .card-header {
        padding: 18px 12px;
        text-align: center;
        font-size: 23px;
        font-weight: 700;
        color: #1a1a1a;
        border-radius: 14px 14px 0 0;
        background: linear-gradient(135deg, #FFD700, #F4C430);
        border-bottom: 4px solid #006B3F;
    }
    
    .card-subtitle {
        text-align: center;
        font-size: 17px;
        font-weight: 700;
        margin: 12px 0 8px 0;
        color: #006B3F;
    }
    
    .card-text {
        text-align: justify;
        font-size: 15px;
        line-height: 1.6;
        color: #333;
        padding: 14px 16px;
        border-radius: 0 0 14px 14px;
        min-height: 180px;
        background: linear-gradient(180deg, #e8f8ee, #c8ecd4);
        border: 1px solid #a8d5b5;
        border-top: none;
        box-sizing: border-box;
    }
    
    .auth-box {
        background: #f7fbf8;
        border: 1px solid #c8e6d0;
        border-radius: 10px;
        padding: 14px 18px;
        margin: 14px 0 20px 0;
        font-size: 15px;
        color: #333;
        line-height: 1.7;
    }
    
    .diario-box {
        background: #eef6f0;
        border: 1px solid #b7d9c2;
        border-radius: 12px;
        padding: 16px 18px;
        margin: 12px 0 18px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# CONEXAO COM BANCO DE DADOS - CONFIGURACAO ORIGINAL
# =========================================================

def obter_senha_banco():
    """Obtem senha do banco via environment ou secrets."""
    senha = os.getenv("DB_PASSWORD")
    if not senha:
        try:
            senha = st.secrets["DB_PASSWORD"]
        except Exception:
            senha = None
    if not senha:
        raise RuntimeError("DB_PASSWORD nao foi configurada nas Secrets do Streamlit.")
    return senha


def conectar_banco():
    try:
        return psycopg2.connect(
            host="localhost", database="endemiasbr", user="postgres",
            password="Amor2806", port="5432", client_encoding="UTF8"
        )
    except Exception as e:
        st.error(f"Erro ao conectar: {e}")
        return None


def hash_token_sessao(token):
    """Gera hash SHA256 do token de sessao."""
    return hashlib.sha256(str(token).encode("utf-8")).hexdigest()


def criar_sessao_persistente(usuario):
    """Cria sessao persistente com token em cookie e hash no banco."""
    token = secrets.token_urlsafe(48)
    conn = conectar_banco()
    if not conn:
        return None
    cur = None
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM sessoes_login WHERE expira_em <= CURRENT_TIMESTAMP")
        cur.execute(
            "INSERT INTO sessoes_login (responsavel_id, token_hash, expira_em) VALUES (%s, %s, %s)",
            (int(usuario["id"]), hash_token_sessao(token), datetime.utcnow() + timedelta(days=DIAS_SESSAO))
        )
        conn.commit()
        COOKIES.set(
            NOME_COOKIE_SESSAO,
            token,
            expires_at=datetime.now() + timedelta(days=DIAS_SESSAO),
            path="/",
            secure=True,
            same_site="lax"
        )
        return token
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        st.error(f"Nao foi possivel criar a sessao persistente: {e}")
        return None
    finally:
        if cur:
            cur.close()
        conn.close()


def ler_cookie_sessao():
    """Le token de sessao do cookie."""
    try:
        token = st.context.cookies.get(NOME_COOKIE_SESSAO)
        if token:
            return token
    except Exception:
        pass
    try:
        token = COOKIES.get(NOME_COOKIE_SESSAO)
        if token:
            return token
    except Exception:
        pass
    return None


def restaurar_sessao_persistente():
    """Restaura sessao valida a partir do cookie."""
    token = ler_cookie_sessao()
    if not token:
        return None, None
    conn = conectar_banco()
    if not conn:
        return None, token
    cur = None
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT r.*, e.nome AS estado_nome, e.sigla AS estado_sigla
            FROM sessoes_login s
            JOIN responsaveis r ON r.id = s.responsavel_id
            LEFT JOIN estados e ON e.id = r.estado_id
            WHERE s.token_hash = %s
              AND s.expira_em > CURRENT_TIMESTAMP
              AND r.ativo = TRUE
            LIMIT 1
        """, (hash_token_sessao(token),))
        registro = cur.fetchone()
        if not registro:
            return None, token
        return dict(zip([d[0] for d in cur.description], registro)), token
    except Exception as e:
        print(f"Erro ao restaurar sessao: {e}")
        return None, token
    finally:
        if cur:
            cur.close()
        conn.close()


def encerrar_sessao_persistente(token=None):
    """Encerra sessao removendo token do banco e cookie."""
    if token:
        conn = conectar_banco()
        if conn:
            cur = None
            try:
                cur = conn.cursor()
                cur.execute("DELETE FROM sessoes_login WHERE token_hash=%s", (hash_token_sessao(token),))
                conn.commit()
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass
            finally:
                if cur:
                    cur.close()
                conn.close()
    try:
        COOKIES.delete(NOME_COOKIE_SESSAO)
    except Exception:
        pass
def garantir_tabela_colecoes_hidricas(conn):
    """Garante a tabela usada exclusivamente pelo cadastro PCE-102A."""
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS public.colecoes_hidricas (
                id BIGSERIAL PRIMARY KEY,
                localidade_id BIGINT NOT NULL,
                nome VARCHAR(200) NOT NULL,
                tipo VARCHAR(100),
                status VARCHAR(30) DEFAULT 'Ativa',
                observacao TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def so_numeros(t):
    """Remove caracteres nao numericos."""
    return re.sub(r"\D", "", str(t or ""))


def formatar_cpf(cpf):
    """Formata CPF no padrao brasileiro."""
    n = so_numeros(cpf)
    return f"{n[:3]}.{n[3:6]}.{n[6:9]}-{n[9:]}" if len(n) == 11 else str(cpf or "")


def hash_senha(senha, cpf):
    """Gera hash SHA256 da senha com CPF."""
    return hashlib.sha256((str(senha) + so_numeros(cpf)).encode("utf-8")).hexdigest()


def senha_valida(senha):
    """Valida requisitos minimos da senha."""
    if len(str(senha or "")) < 6:
        return False, "A senha deve ter pelo menos 6 caracteres."
    return True, ""


def buscar_usuario_por_cpf(cpf):
    """Busca usuario por CPF no banco."""
    conn = conectar_banco()
    if not conn:
        return None
    try:
        df = pd.read_sql("""
            SELECT r.*, e.nome as estado_nome, e.sigla as estado_sigla
            FROM responsaveis r
            LEFT JOIN estados e ON e.id = r.estado_id
            WHERE regexp_replace(r.cpf, '[^0-9]', '', 'g') = %s
              AND r.ativo = TRUE
        """, conn, params=(so_numeros(cpf),))
        return None if df.empty else df.iloc[0].to_dict()
    except Exception as e:
        st.error(f"Erro ao buscar usuario: {e}")
        return None
    finally:
        conn.close()


def buscar_usuario_simulacao(nome_usuario):
    """Busca a conta especial usada apenas no ambiente de simulacao."""
    conn = conectar_banco()
    if not conn:
        return None
    try:
        df = pd.read_sql("""
            SELECT r.*, e.nome as estado_nome, e.sigla as estado_sigla
            FROM responsaveis r
            LEFT JOIN estados e ON e.id = r.estado_id
            WHERE LOWER(TRIM(r.nome)) = LOWER(TRIM(%s))
              AND r.ativo = TRUE
            ORDER BY r.id
            LIMIT 1
        """, conn, params=(str(nome_usuario),))
        return None if df.empty else df.iloc[0].to_dict()
    except Exception as e:
        st.error(f"Erro ao buscar usuario de simulacao: {e}")
        return None
    finally:
        conn.close()


def carregar_estados_todos(conn):
    """Carrega todos os estados."""
    return pd.read_sql("SELECT id, nome, sigla FROM estados ORDER BY nome", conn)


def carregar_estados_cadastro(conn, usuario):
    """Carrega estados permitidos para cadastro conforme nivel."""
    if usuario.get("nivel") == "Federal":
        return carregar_estados_todos(conn)
    estado_id = usuario.get("estado_id")
    if estado_id is None or (isinstance(estado_id, float) and pd.isna(estado_id)):
        return pd.DataFrame(columns=["id", "nome", "sigla"])
    return pd.read_sql(
        "SELECT id, nome, sigla FROM estados WHERE id = %s",
        conn,
        params=(int(estado_id),)
    )


# =========================================================
# HIERARQUIA DE VISUALIZACAO E ESCOPO DE CADASTRO
# =========================================================

def nivel_usuario(usuario):
    """Retorna nivel hierarquico do usuario."""
    return str(usuario.get("nivel") or "").strip()


def obter_regional_id_usuario(conn, usuario):
    """Obtem regional do usuario.
    
    Preferimos regional_id gravado no responsavel.
    Como compatibilidade, se o usuario possuir municipio_id,
    descobrimos a regional pelo municipio.
    """
    rid = usuario.get("regional_id")
    if rid is not None and not (isinstance(rid, float) and pd.isna(rid)):
        try:
            return int(rid)
        except Exception:
            pass

    mid = usuario.get("municipio_id")
    if mid is not None and not (isinstance(mid, float) and pd.isna(mid)):
        try:
            df = pd.read_sql(
                "SELECT regional_id FROM municipios WHERE id=%s",
                conn,
                params=(int(mid),)
            )
            if not df.empty and pd.notna(df.iloc[0]["regional_id"]):
                return int(df.iloc[0]["regional_id"])
        except Exception:
            pass

    return None


def municipios_para_cadastro(conn, usuario, incluir_arquivados=False, estado_id=None):
    """
    Retorna somente os municipios que o usuario pode CADASTRAR/EDITAR.

    REGRA GERAL DO SISTEMA:
      Se estado_id for informado pela tela, somente municipios daquele Estado
      podem ser retornados. Isso vale para qualquer modulo/tela que utilize
      esta funcao, independentemente do nivel do usuario.

    Visualizacao e cadastro sao conceitos diferentes:
      Federal  -> todos os municipios
      Estadual -> todos os municipios do proprio estado
      Regional -> somente municipios da propria regional
      Municipal -> somente o proprio municipio
    """
    nivel = nivel_usuario(usuario)

    sql = """
        SELECT m.id, m.nome, m.codigo_ibge, m.status,
               r.nome AS regional, e.nome AS estado, e.sigla
        FROM municipios m
        LEFT JOIN regionais_saude r ON r.id = m.regional_id
        LEFT JOIN estados e ON e.id = r.estado_id
        WHERE 1=1
    """
    params = []

    if nivel == "Federal":
        pass

    elif nivel == "Estadual":
        estado_id = usuario.get("estado_id")
        if estado_id is None or (isinstance(estado_id, float) and pd.isna(estado_id)):
            return pd.DataFrame(columns=["id", "nome", "codigo_ibge", "status", "regional", "estado", "sigla"])
        sql += " AND r.estado_id = %s"
        params.append(int(estado_id))

    elif nivel == "Regional":
        regional_id = obter_regional_id_usuario(conn, usuario)
        if regional_id is None:
            return pd.DataFrame(columns=["id", "nome", "codigo_ibge", "status", "regional", "estado", "sigla"])
        sql += " AND m.regional_id = %s"
        params.append(int(regional_id))

    elif nivel == "Municipal":
        municipio_id = usuario.get("municipio_id")
        if municipio_id is None or (isinstance(municipio_id, float) and pd.isna(municipio_id)):
            return pd.DataFrame(columns=["id", "nome", "codigo_ibge", "status", "regional", "estado", "sigla"])
        sql += " AND m.id = %s"
        params.append(int(municipio_id))

    else:
        return pd.DataFrame(columns=["id", "nome", "codigo_ibge", "status", "regional", "estado", "sigla"])

    # REGRA GERAL: depois que a tela define um Estado, a lista de municipios
    # fica obrigatoriamente restrita ao estado selecionado.
    if estado_id is not None:
        try:
            sql += " AND r.estado_id = %s"
            params.append(int(estado_id))
        except (TypeError, ValueError):
            pass

    if not incluir_arquivados:
        sql += " AND (m.status IS NULL OR m.status = 'Ativo')"

    sql += " ORDER BY e.nome, m.nome"
    return pd.read_sql(sql, conn, params=tuple(params))


def municipio_esta_no_escopo(conn, usuario, municipio_id):
    """Validacao final antes de qualquer gravacao municipal."""
    try:
        df = municipios_para_cadastro(conn, usuario, True)
        return not df[df["id"].astype(int) == int(municipio_id)].empty
    except Exception:
        return False


def mostrar_escopo_usuario(usuario):
    """Exibe mensagem de escopo territorial conforme nivel."""
    nivel = nivel_usuario(usuario)
    textos = {
        "Federal": "Cadastro/execucao territorial: **todos os estados e municipios**.",
        "Estadual": "Cadastro/execucao territorial: **somente o proprio estado**. Visualizacao: **todo o Brasil**.",
        "Regional": "Cadastro/execucao territorial: **somente a propria regional**. Visualizacao: **todo o Brasil**.",
        "Municipal": "Cadastro/execucao territorial: **somente o proprio municipio**. Visualizacao: **todo o Brasil**.",
    }
    if nivel == "Regional" and usuario.get("regional_id") is None:
        texto = textos[nivel] + " ⚠️ A regional sera localizada pelo municipio quando possivel."
    else:
        texto = textos.get(nivel, "Escopo nao identificado.")
    st.caption(texto)


def garantir_tabela_responsavel_programas(conn):
    """Garante a tabela de vinculos entre responsaveis e programas."""
    cur = None
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS responsavel_programas (
                id SERIAL PRIMARY KEY,
                responsavel_id INTEGER NOT NULL REFERENCES responsaveis(id) ON DELETE CASCADE,
                programa VARCHAR(20) NOT NULL,
                esfera VARCHAR(20),
                ativo BOOLEAN NOT NULL DEFAULT TRUE,
                UNIQUE(responsavel_id, programa)
            )
        """)
        cur.execute(
            "ALTER TABLE responsavel_programas "
            "ADD COLUMN IF NOT EXISTS esfera VARCHAR(20)"
        )
        cur.execute(
            "ALTER TABLE responsavel_programas "
            "ADD COLUMN IF NOT EXISTS ativo BOOLEAN NOT NULL DEFAULT TRUE"
        )
        conn.commit()
        return True
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        st.error(f"Erro ao preparar os vinculos de responsaveis: {e}")
        return False
    finally:
        if cur:
            cur.close()


# =========================================================
# FUNCOES DE IMAGENS E CARDS
# =========================================================

def localizar_imagem_modulo(*palavras):
    """Localiza imagens do modulo de forma recursiva e tolerante."""
    import unicodedata

    def normalizar(valor):
        valor = str(valor).lower()
        valor = unicodedata.normalize("NFKD", valor)
        valor = "".join(ch for ch in valor if not unicodedata.combining(ch))
        return valor

    base = os.path.dirname(os.path.abspath(__file__))
    pastas = [
        os.path.join(base, "assets"),
        os.path.join(base, "imagens"),
        os.path.join(base, "img"),
        base,
    ]
    extensoes = {".png", ".jpg", ".jpeg", ".webp"}
    palavras_norm = [normalizar(p) for p in palavras if str(p).strip()]

    candidatos = []
    vistos = set()

    for pasta in pastas:
        if not os.path.isdir(pasta):
            continue
        for raiz, _, arquivos in os.walk(pasta):
            for nome in sorted(arquivos):
                caminho = os.path.join(raiz, nome)
                caminho_real = os.path.realpath(caminho)
                if caminho_real in vistos:
                    continue
                vistos.add(caminho_real)

                if os.path.splitext(nome)[1].lower() not in extensoes:
                    continue

                nome_norm = normalizar(nome)
                if any(p in nome_norm for p in palavras_norm):
                    candidatos.append(caminho)

    if candidatos:
        return sorted(candidatos)[0]
    return None


def caminho_imagem(*nomes):
    """Retorna caminho de imagem se existir."""
    for pasta in ["imagens", "img", "assets", "."]:
        for nome in nomes:
            p = os.path.join(pasta, nome)
            if os.path.exists(p):
                return p
    return None


def imagem_card(caminho, altura=220):
    """Gera HTML de imagem em base64 para card."""
    if not caminho or not os.path.exists(caminho):
        return f'<div style="width:100%;height:{altura}px;background:#e8f8ee;"></div>'
    with open(caminho, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ext = caminho.lower().rsplit(".", 1)[-1]
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext
    return f'<img src="data:image/{mime};base64,{b64}" style="width:100%;height:{altura}px;object-fit:cover;object-position:center;display:block;" />'


# =========================================================
# FUNCOES DE DADOS TERRITORIAIS
# =========================================================

def municipios_por_estado(conn, estado_id, incluir_arquivados=True):
    """Carrega municipios de um estado."""
    sql = """
        SELECT m.id, m.nome, m.codigo_ibge, m.status, r.nome as regional
        FROM municipios m
        LEFT JOIN regionais_saude r ON r.id = m.regional_id
        WHERE r.estado_id = %s
    """
    if not incluir_arquivados:
        sql += " AND (m.status IS NULL OR m.status = 'Ativo')"
    sql += " ORDER BY m.nome"
    return pd.read_sql(sql, conn, params=(int(estado_id),))


def carregar_nacional(conn):
    """Carrega configuracoes nacionais."""
    try:
        df = pd.read_sql(
            "SELECT presidente, ministro_saude FROM config_nacional ORDER BY id LIMIT 1",
            conn
        )
        if df.empty:
            return {"presidente": "—", "ministro_saude": "—"}
        return {
            "presidente": df.iloc[0]["presidente"] or "—",
            "ministro_saude": df.iloc[0]["ministro_saude"] or "—"
        }
    except Exception:
        return {"presidente": "—", "ministro_saude": "—"}


def carregar_estado_info(conn, estado_id):
    """Carrega informacoes do estado."""
    try:
        df = pd.read_sql("""
            SELECT nome, sigla, capital, governador, secretario_saude, secretaria_nome
            FROM estados WHERE id = %s
        """, conn, params=(int(estado_id),))
        if df.empty:
            return None
        r = df.iloc[0]
        return {
            "nome": r["nome"],
            "sigla": r["sigla"],
            "capital": r["capital"] or "—",
            "governador": r["governador"] or "—",
            "secretario_saude": r["secretario_saude"] or "—",
            "secretaria_nome": r["secretaria_nome"] or "—"
        }
    except Exception:
        return None


def carregar_municipio_info(conn, mun_id):
    """Carrega informacoes do municipio."""
    try:
        df = pd.read_sql(
            "SELECT nome, prefeito, secretario_saude, status FROM municipios WHERE id = %s",
            conn,
            params=(int(mun_id),)
        )
        if df.empty:
            return None
        r = df.iloc[0]
        return {
            "nome": r["nome"],
            "prefeito": r["prefeito"] or "—",
            "secretario_saude": r["secretario_saude"] or "—",
            "status": r["status"] or "Ativo"
        }
    except Exception:
        return None


def pesquisas_da_localidade(conn, localidade_id):
    """Carrega pesquisas de uma localidade."""
    return pd.read_sql("""
        SELECT id, data_pesquisa, tipo_pesquisa, status
        FROM pesquisas_entomologicas
        WHERE localidade_id = %s
          AND (status IS NULL OR status = 'Ativa')
        ORDER BY data_pesquisa DESC, id DESC
    """, conn, params=(int(localidade_id),))


def imoveis_da_localidade(conn, localidade_id):
    """Carrega imoveis de uma localidade."""
    return pd.read_sql("""
        SELECT id, identificacao, quarteirao, lado, sequencia, numero, tipo
        FROM imoveis
        WHERE localidade_id = %s
          AND (ativo IS NULL OR ativo = TRUE)
        ORDER BY quarteirao, sequencia, id
    """, conn, params=(int(localidade_id),))


def obter_proximo_etiqueta(conn, municipio_id):
    """Obtem proximo numero de etiqueta para municipio."""
    try:
        df = pd.read_sql(
            "SELECT proximo_numero FROM etiquetas_controle WHERE municipio_id = %s",
            conn,
            params=(int(municipio_id),)
        )
        if df.empty:
            return 1
        return int(df.iloc[0]["proximo_numero"] or 1)
    except Exception:
        return 1


def lista_especies_triatomineo(conn):
    """Carrega lista de especies de triatomineos."""
    try:
        df = pd.read_sql(
            "SELECT nome_cientifico FROM triatominios WHERE ativo IS NULL OR ativo = TRUE ORDER BY nome_cientifico",
            conn
        )
        lista = df["nome_cientifico"].tolist() if not df.empty else []
    except Exception:
        lista = []
    if not lista:
        lista = [
            "Triatoma infestans",
            "Panstrongylus megistus",
            "Triatoma brasiliensis",
            "Triatoma sordida",
            "Rhodnius neglectus"
        ]
    if "Outra" not in lista:
        lista = lista + ["Outra"]
    return lista
def garantir_tabela_pits_pcdch(conn):
    """Garante tabela de PIT do PCDCh."""
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pits_pcdch (
                id SERIAL PRIMARY KEY,
                municipio_id INTEGER NOT NULL REFERENCES municipios(id),
                localidade_id INTEGER NOT NULL REFERENCES localidades(id),
                numero_pit INTEGER NOT NULL,
                nome TEXT NOT NULL,
                codigo_notificante TEXT,
                nome_notificante TEXT,
                ativo BOOLEAN DEFAULT TRUE,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (municipio_id, numero_pit)
            )
        """)
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        st.error(f"Erro ao preparar a tabela de PIT: {e}")
        return False


def garantir_tabela_exames_pcdch(conn):
    """Garante tabela de exames do PCDCh."""
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS exames_pcdch (
                id SERIAL PRIMARY KEY,
                diario_id INTEGER NOT NULL REFERENCES diario_pcdch(id) ON DELETE CASCADE,
                municipio_id INTEGER NOT NULL,
                localidade_id INTEGER NOT NULL,
                etiqueta INTEGER NOT NULL,
                sequencia INTEGER NOT NULL,
                especie TEXT,
                local_captura TEXT,
                estagio TEXT,
                resultado TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (diario_id, sequencia)
            )
        """)
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        st.error(f"Erro ao preparar a tabela de Exame: {e}")
        return False


def garantir_tabelas_programacao_pcdch(conn):
    """Cria tabelas modernas de planejamento do PCDCh, se ainda nao existirem."""
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS programacao_pcdch_anual (
                id SERIAL PRIMARY KEY,
                municipio_id INTEGER NOT NULL REFERENCES municipios(id),
                agente_id INTEGER REFERENCES agentes(id),
                ano INTEGER NOT NULL,
                ud_existentes INTEGER NOT NULL DEFAULT 0,
                pits_existentes INTEGER NOT NULL DEFAULT 0,
                dias_pit INTEGER NOT NULL DEFAULT 0,
                dias_burocraticos INTEGER NOT NULL DEFAULT 0,
                dias_borrifacao_imprevistos INTEGER NOT NULL DEFAULT 0,
                dias_pesquisa_mes INTEGER NOT NULL DEFAULT 0,
                media_ud_homem_dia NUMERIC(8,2) NOT NULL DEFAULT 0,
                ud_pesquisar_mes INTEGER NOT NULL DEFAULT 0,
                ud_pesquisar_q1 INTEGER NOT NULL DEFAULT 0,
                ud_pesquisar_q2 INTEGER NOT NULL DEFAULT 0,
                ud_pesquisar_q3 INTEGER NOT NULL DEFAULT 0,
                rg_localidades TEXT,
                observacao TEXT,
                status TEXT NOT NULL DEFAULT 'Ativa',
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (municipio_id, ano, agente_id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS programacao_pcdch_mensal (
                id SERIAL PRIMARY KEY,
                programacao_anual_id INTEGER REFERENCES programacao_pcdch_anual(id) ON DELETE SET NULL,
                municipio_id INTEGER NOT NULL REFERENCES municipios(id),
                localidade_id INTEGER REFERENCES localidades(id),
                agente_id INTEGER REFERENCES agentes(id),
                ano INTEGER NOT NULL,
                mes INTEGER NOT NULL,
                data_programada DATE,
                atividade TEXT NOT NULL,
                ud_programadas INTEGER NOT NULL DEFAULT 0,
                ud_realizadas INTEGER NOT NULL DEFAULT 0,
                pit_programados INTEGER NOT NULL DEFAULT 0,
                pit_realizados INTEGER NOT NULL DEFAULT 0,
                dias_programados NUMERIC(6,2) NOT NULL DEFAULT 0,
                dias_realizados NUMERIC(6,2) NOT NULL DEFAULT 0,
                observacao TEXT,
                status TEXT NOT NULL DEFAULT 'Programada',
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_prog_anual_municipio_ano ON programacao_pcdch_anual(municipio_id, ano)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_prog_mensal_municipio_ano_mes ON programacao_pcdch_mensal(municipio_id, ano, mes)")
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        st.error(f"Erro ao preparar as tabelas de Programacao do PCDCh: {e}")
        return False


def calcular_parametros_programacao(ud_existentes, pits_existentes, dias_pit, dias_buro, dias_borr, media_ud):
    """Calcula os parametros basicos do plano anual."""
    dias_pesquisa = max(0, 20 - int(dias_pit) - int(dias_buro) - int(dias_borr))
    ud_mes = max(0, int(round(dias_pesquisa * float(media_ud or 0))))
    return dias_pesquisa, ud_mes


def atividade_programacao_pcdch():
    """Retorna lista de atividades de programacao PCDCh."""
    return [
        "Pesquisa entomologica regular",
        "Visita a PIT",
        "Borrifacao",
        "Atividade burocratica",
        "Educacao em saude",
        "Outras atividades",
    ]


def garantir_tabela_desalojantes(conn):
    """Cria a tabela auxiliar de desalojantes, caso ainda nao exista."""
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS desalojantes (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(150) NOT NULL UNIQUE,
                ativo BOOLEAN NOT NULL DEFAULT TRUE,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        st.error(f"Erro ao preparar tabela de desalojantes: {e}")
        return False


def lista_desalojantes(conn):
    """Carrega lista de desalojantes."""
    try:
        garantir_tabela_desalojantes(conn)
        df = pd.read_sql(
            "SELECT nome FROM desalojantes WHERE ativo=TRUE ORDER BY nome",
            conn
        )
        return df["nome"].tolist()
    except Exception:
        return []


def lista_inseticidas(conn):
    """Carrega lista de inseticidas."""
    try:
        df = pd.read_sql(
            "SELECT nome FROM inseticidas WHERE ativo IS NULL OR ativo = TRUE ORDER BY nome",
            conn
        )
        return df["nome"].tolist() if not df.empty else ["K-Othrine", "Demand", "Actellic", "Ficam", "Outro"]
    except Exception:
        return ["K-Othrine", "Demand", "Actellic", "Ficam", "Outro"]


def form_campos_imovel(prefixo, valores=None):
    """Gera campos de formulario para imovel."""
    v = valores or {}
    identificacao = st.text_input("Identificacao / Endereco *", value=str(v.get("identificacao") or ""), key=f"{prefixo}_ident")
    c1, c2, c3 = st.columns(3)
    with c1:
        quarteirao = st.text_input("Quarteirao", value=str(v.get("quarteirao") or ""), key=f"{prefixo}_q")
    with c2:
        lados = ["", "Par", "Impar", "Unico", "A", "B"]
        lado_atual = str(v.get("lado") or "")
        idx_lado = lados.index(lado_atual) if lado_atual in lados else 0
        lado = st.selectbox("Lado", lados, index=idx_lado, key=f"{prefixo}_lado")
    with c3:
        seq_val = int(v["sequencia"]) if v.get("sequencia") not in (None, "") else 0
        sequencia = st.number_input("Sequencia", min_value=0, value=seq_val, key=f"{prefixo}_seq")
    c4, c5 = st.columns(2)
    with c4:
        numero = st.text_input("Numero", value=str(v.get("numero") or ""), key=f"{prefixo}_num")
    with c5:
        complemento = st.text_input("Complemento", value=str(v.get("complemento") or ""), key=f"{prefixo}_comp")
    tipos = ["Residencia", "Comercio", "Escola", "Igreja", "Anexo", "Terreno baldio", "Outro"]
    tipo_atual = str(v.get("tipo") or "Residencia")
    tipo = st.selectbox("Tipo de imovel", tipos, index=tipos.index(tipo_atual) if tipo_atual in tipos else 0, key=f"{prefixo}_tipo")
    consts = ["Alvenaria", "Madeira", "Mista", "Taipa", "Outro", ""]
    tc_atual = str(v.get("tipo_construcao") or "")
    tipo_const = st.selectbox("Tipo de construcao", consts, index=consts.index(tc_atual) if tc_atual in consts else 0, key=f"{prefixo}_tconst")
    sits = ["Existente", "Fechado", "Desabitado", "Em construcao", "Demolido"]
    sit_atual = str(v.get("situacao") or "Existente")
    situacao = st.selectbox("Situacao", sits, index=sits.index(sit_atual) if sit_atual in sits else 0, key=f"{prefixo}_sit")
    obs = st.text_area("Observacoes", value=str(v.get("observacao") or ""), key=f"{prefixo}_obs")
    return {
        "identificacao": identificacao.strip() if identificacao else "",
        "quarteirao": quarteirao.strip() or None,
        "lado": lado or None,
        "sequencia": int(sequencia) if sequencia else None,
        "numero": numero.strip() or None,
        "complemento": complemento.strip() or None,
        "tipo": tipo,
        "tipo_construcao": tipo_const or None,
        "situacao": situacao,
        "observacao": obs.strip() or None,
    }


def garantir_tabelas_pcl(conn):
    """Prepara toda a estrutura persistente do PCL no PostgreSQL."""
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pcl_lv_humana (
                id BIGSERIAL PRIMARY KEY,
                estado_id BIGINT,
                municipio_id BIGINT,
                localidade_id BIGINT,
                notificacao VARCHAR(60),
                nome VARCHAR(200) NOT NULL,
                data_nascimento DATE,
                sexo VARCHAR(30),
                data_notificacao DATE,
                municipio_infeccao VARCHAR(200),
                local_provavel TEXT,
                sintomas TEXT,
                diagnostico VARCHAR(120),
                resultado VARCHAR(120),
                data_diagnostico DATE,
                tratamento VARCHAR(200),
                evolucao VARCHAR(80),
                observacao TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS pcl_lv_canina (
                id BIGSERIAL PRIMARY KEY,
                estado_id BIGINT,
                municipio_id BIGINT,
                localidade_id BIGINT,
                nome_animal VARCHAR(120),
                responsavel VARCHAR(200),
                sexo VARCHAR(20),
                idade_anos NUMERIC(5,2),
                raca VARCHAR(100),
                data_coleta DATE,
                tipo_exame VARCHAR(120),
                resultado VARCHAR(120),
                situacao VARCHAR(100),
                observacao TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS pcl_lv_entomologia (
                id BIGSERIAL PRIMARY KEY,
                estado_id BIGINT,
                municipio_id BIGINT,
                localidade_id BIGINT,
                data_coleta DATE,
                ponto_coleta VARCHAR(200),
                ambiente VARCHAR(150),
                metodo VARCHAR(150),
                quantidade INTEGER DEFAULT 0,
                especie VARCHAR(150),
                sexo VARCHAR(30),
                resultado VARCHAR(150),
                observacao TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS pcl_lv_investigacoes (
                id BIGSERIAL PRIMARY KEY,
                estado_id BIGINT,
                municipio_id BIGINT,
                localidade_id BIGINT,
                tipo VARCHAR(120),
                data_investigacao DATE,
                referencia VARCHAR(120),
                local_provavel TEXT,
                achados TEXT,
                medidas_adotadas TEXT,
                responsavel VARCHAR(200),
                status VARCHAR(60) DEFAULT 'Em andamento',
                observacao TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS pcl_lv_acoes (
                id BIGSERIAL PRIMARY KEY,
                estado_id BIGINT,
                municipio_id BIGINT,
                localidade_id BIGINT,
                data_acao DATE,
                tipo VARCHAR(150),
                publico_alvo VARCHAR(150),
                quantidade INTEGER DEFAULT 0,
                descricao TEXT,
                responsavel VARCHAR(200),
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS pcl_lv_obitos (
                id BIGSERIAL PRIMARY KEY,
                estado_id BIGINT,
                municipio_id BIGINT,
                localidade_id BIGINT,
                nome VARCHAR(200),
                data_obito DATE,
                comunicacao DATE,
                unidade_investigacao VARCHAR(200),
                investigacao_ubs TEXT,
                investigacao_internacao TEXT,
                entrevista_domiciliar TEXT,
                conclusao TEXT,
                status VARCHAR(80) DEFAULT 'Em investigacao',
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS pcl_lt_casos (
                id BIGSERIAL PRIMARY KEY,
                estado_id BIGINT,
                municipio_id BIGINT,
                localidade_id BIGINT,
                nome VARCHAR(200) NOT NULL,
                data_nascimento DATE,
                sexo VARCHAR(30),
                data_notificacao DATE,
                forma_clinica VARCHAR(120),
                local_infeccao TEXT,
                diagnostico VARCHAR(150),
                resultado VARCHAR(120),
                tratamento VARCHAR(200),
                evolucao VARCHAR(100),
                observacao TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS pcl_lt_investigacoes (
                id BIGSERIAL PRIMARY KEY,
                estado_id BIGINT,
                municipio_id BIGINT,
                localidade_id BIGINT,
                data_investigacao DATE,
                referencia VARCHAR(120),
                local_provavel TEXT,
                achados TEXT,
                medidas_adotadas TEXT,
                responsavel VARCHAR(200),
                status VARCHAR(60) DEFAULT 'Em andamento',
                observacao TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS pcl_lt_acompanhamentos (
                id BIGSERIAL PRIMARY KEY,
                caso_id BIGINT,
                data_acompanhamento DATE,
                tratamento VARCHAR(200),
                evolucao VARCHAR(100),
                resultado VARCHAR(120),
                observacao TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS pcl_lt_entomologia (
                id BIGSERIAL PRIMARY KEY,
                estado_id BIGINT,
                municipio_id BIGINT,
                localidade_id BIGINT,
                data_coleta DATE,
                ponto_coleta VARCHAR(200),
                ambiente VARCHAR(150),
                metodo VARCHAR(150),
                quantidade INTEGER DEFAULT 0,
                especie VARCHAR(150),
                sexo VARCHAR(30),
                resultado VARCHAR(150),
                observacao TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS pcl_lt_acoes (
                id BIGSERIAL PRIMARY KEY,
                estado_id BIGINT,
                municipio_id BIGINT,
                localidade_id BIGINT,
                data_acao DATE,
                tipo VARCHAR(150),
                descricao TEXT,
                responsavel VARCHAR(200),
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS pcl_lt_obitos (
                id BIGSERIAL PRIMARY KEY,
                estado_id BIGINT,
                municipio_id BIGINT,
                localidade_id BIGINT,
                nome VARCHAR(200),
                data_obito DATE,
                comunicacao DATE,
                unidade_investigacao VARCHAR(200),
                investigacao TEXT,
                entrevista_domiciliar TEXT,
                conclusao TEXT,
                status VARCHAR(80) DEFAULT 'Em investigacao',
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        indices = [
            ("idx_pcl_lv_humana_estado_municipio", "pcl_lv_humana(estado_id, municipio_id)"),
            ("idx_pcl_lv_humana_localidade", "pcl_lv_humana(localidade_id)"),
            ("idx_pcl_lv_humana_data", "pcl_lv_humana(data_notificacao)"),
            ("idx_pcl_lv_canina_estado_municipio", "pcl_lv_canina(estado_id, municipio_id)"),
            ("idx_pcl_lv_canina_localidade", "pcl_lv_canina(localidade_id)"),
            ("idx_pcl_lv_entomo_estado_municipio", "pcl_lv_entomologia(estado_id, municipio_id)"),
            ("idx_pcl_lv_entomo_localidade", "pcl_lv_entomologia(localidade_id)"),
            ("idx_pcl_lv_invest_estado_municipio", "pcl_lv_investigacoes(estado_id, municipio_id)"),
            ("idx_pcl_lv_invest_localidade", "pcl_lv_investigacoes(localidade_id)"),
            ("idx_pcl_lv_acoes_estado_municipio", "pcl_lv_acoes(estado_id, municipio_id)"),
            ("idx_pcl_lv_acoes_localidade", "pcl_lv_acoes(localidade_id)"),
            ("idx_pcl_lv_obitos_estado_municipio", "pcl_lv_obitos(estado_id, municipio_id)"),
            ("idx_pcl_lt_casos_estado_municipio", "pcl_lt_casos(estado_id, municipio_id)"),
            ("idx_pcl_lt_casos_localidade", "pcl_lt_casos(localidade_id)"),
            ("idx_pcl_lt_invest_estado_municipio", "pcl_lt_investigacoes(estado_id, municipio_id)"),
            ("idx_pcl_lt_acomp_caso", "pcl_lt_acompanhamentos(caso_id)"),
            ("idx_pcl_lt_entomo_estado_municipio", "pcl_lt_entomologia(estado_id, municipio_id)"),
            ("idx_pcl_lt_acoes_estado_municipio", "pcl_lt_acoes(estado_id, municipio_id)"),
            ("idx_pcl_lt_obitos_estado_municipio", "pcl_lt_obitos(estado_id, municipio_id)"),
        ]
        for nome_idx, alvo in indices:
            cur.execute(f"CREATE INDEX IF NOT EXISTS {nome_idx} ON {alvo}")

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


# =========================================================
# NAVEGACAO PERSISTENTE
# =========================================================

def salvar_navegacao_persistente():
    """Salva somente a rota da tela; nao salva campos, dados pessoais ou credenciais."""
    try:
        rota = {chave: st.session_state.get(chave) for chave in CHAVES_NAVEGACAO_PERSISTENTE}
        COOKIES.set(
            NOME_COOKIE_NAVEGACAO,
            json.dumps(rota, separators=(",", ":")),
            expires_at=datetime.now() + timedelta(days=DIAS_SESSAO),
            path="/",
            secure=True,
            same_site="lax"
        )
    except Exception:
        pass


def ler_navegacao_persistente():
    """Le rota da tela do cookie."""
    valor = None
    try:
        valor = st.context.cookies.get(NOME_COOKIE_NAVEGACAO)
    except Exception:
        pass
    if not valor:
        try:
            valor = COOKIES.get(NOME_COOKIE_NAVEGACAO)
        except Exception:
            pass
    if not valor:
        return {}
    try:
        rota = json.loads(valor)
        return rota if isinstance(rota, dict) else {}
    except Exception:
        return {}


def restaurar_navegacao_persistente():
    """Restaura navegacao do cookie se pagina valida."""
    rota = ler_navegacao_persistente()
    paginas_validas = {
        "Inicio", "Atividades", "Configuracao", "CentralAtividades",
        "CadastrosAuxiliares", "Responsaveis", "TrocarSenha", "Contato",
        "Sisloc", "PCDCh", "PCE", "PCL", "Offline"
    }
    if rota.get("pagina") not in paginas_validas:
        return False
    for chave in CHAVES_NAVEGACAO_PERSISTENTE:
        if chave in rota:
            st.session_state[chave] = rota[chave]
    return True


def limpar_navegacao_persistente():
    """Limpa navegacao e reseta para valores padrao."""
    try:
        COOKIES.delete(NOME_COOKIE_NAVEGACAO)
    except Exception:
        pass
    for k, v in {
        "usuario": None,
        "pagina": "Inicio",
        "modulo": None,
        "modulo_inicio": False,
        "forcar_troca_senha": False,
        "config_aberta": False,
        "atividades_aberta": False,
        "atividade_aba": "Gestao de Atividades",
        "contato_aberto": False,
        "contato_aba": "Inicio",
        "menu_sisloc": "Navegacao Hierarquica",
        "pcdch_menu": "Cadastro",
        "pce_menu": None,
        "pce_group": None,
        "pce_rel_sub": "PCE-101 Detalhado",
        "pce_sub": "Inclusao",
        "cad_aux_menu": "PCDCh",
        "cad_aux_item": "Desalojantes",
        "pcl_doenca": None,
        "pcl_menu": None,
        "pcl_sub": None,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v


# =========================================================
# INICIALIZACAO DA SESSAO
# =========================================================

if st.session_state.usuario is None:
    usuario_restaurado, token_restaurado = restaurar_sessao_persistente()
    if usuario_restaurado is not None:
        st.session_state.usuario = usuario_restaurado
        st.session_state.session_token = token_restaurado
        st.session_state.forcar_troca_senha = bool(usuario_restaurado.get("deve_trocar_senha"))
        if not st.session_state.forcar_troca_senha:
            if not restaurar_navegacao_persistente():
                st.session_state.pagina = "Inicio"
                st.session_state.modulo = None

if st.session_state.usuario is None and not st.session_state.forcar_troca_senha:
    # Tela de login
    st.markdown(
        """
        <div style="text-align:center; padding: 60px 0;">
            <h1 style="color:#006B3F; font-size:42px; margin-bottom:10px;">EndemiasBR</h1>
            <p style="color:#00452c; font-size:18px; margin-bottom:40px;">Sistema de Apoio à Vigilancia de Endemias</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            cpf = st.text_input("CPF", placeholder="000.000.000-00")
            senha = st.text_input("Senha", type="password")
            submit = st.form_submit_button("Entrar", use_container_width=True)

            if submit:
                cpf_limpo = so_numeros(cpf)
                if len(cpf_limpo) != 11:
                    st.error("Informe um CPF com 11 numeros.")
                else:
                    if MODO_SIMULACAO and cpf_limpo == "00000000100":
                        usuario_simulacao = buscar_usuario_simulacao("SIMULACAO FEDERAL")
                        if usuario_simulacao:
                            st.session_state.usuario = usuario_simulacao
                            st.session_state.pagina = "Inicio"
                            st.session_state.modulo = None
                            st.session_state.modulo_inicio = False
                            st.rerun()
                        else:
                            st.error("Usuario de simulacao nao encontrado no banco.")
                    else:
                        usuario = buscar_usuario_por_cpf(cpf_limpo)
                        if not usuario:
                            st.error("CPF nao encontrado ou responsavel inativo.")
                        else:
                            hash_informado = hash_senha(senha, cpf_limpo)
                            if hash_informado != (usuario.get("senha_hash") or "").lower():
                                st.error("Senha incorreta.")
                            else:
                                st.session_state.usuario = usuario
                                st.session_state.pagina = "Inicio"
                                st.session_state.modulo = None
                                st.session_state.modulo_inicio = False
                                if not usuario.get("deve_trocar_senha"):
                                    criar_sessao_persistente(usuario)
                                st.rerun()

    st.markdown("---")
    st.caption("EndemiasBR - Sistema de Apoio à Vigilancia de Endemias")
    st.stop()
with st.sidebar:
    # Identificacao do usuario
    st.markdown('<div class="sidebar-brand">EndemiasBR</div>', unsafe_allow_html=True)
    estado_sigla = usuario.get("estado_sigla", "")
    info_estado = f"({estado_sigla})" if estado_sigla else ""
    st.markdown(
        f"""
        <div class="sidebar-user">
            <strong>{usuario.get("nome", "Usuario")}</strong>
            <span>{nivel} {info_estado}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Botao INICIO
    if st.button("INICIO", key="nav_inicio", use_container_width=True):
        st.session_state.modulo = None
        st.session_state.config_aberta = False
        st.session_state.pagina = "Inicio"
        salvar_navegacao_persistente()
        st.rerun()

    st.markdown('<div class="sidebar-section">MODULOS</div>', unsafe_allow_html=True)

    # --------------------------------------------------
    # MENU SISLOC
    # --------------------------------------------------
    if st.button("SISLOC", key="nav_sisloc", use_container_width=True):
        st.session_state.modulo = "Sisloc"
        st.session_state.pagina = "Sisloc"
        st.session_state.modulo_inicio = True
        st.session_state.menu_sisloc = "Navegacao Hierarquica"
        salvar_navegacao_persistente()
        st.rerun()

    # --------------------------------------------------
    # MENU PCDCh
    # --------------------------------------------------
    if st.button("PCDCh", key="nav_pcdch", use_container_width=True):
        st.session_state.modulo = "PCDCh"
        st.session_state.pagina = "PCDCh"
        st.session_state.modulo_inicio = True
        st.session_state.pcdch_menu = "Cadastro"
        salvar_navegacao_persistente()
        st.rerun()

    # --------------------------------------------------
    # MENU PCE
    # --------------------------------------------------
    if st.button("PCE", key="nav_pce", use_container_width=True):
        st.session_state.modulo = "PCE"
        st.session_state.pagina = "PCE"
        st.session_state.modulo_inicio = True
        st.session_state.pce_menu = None
        st.session_state.pce_group = None
        salvar_navegacao_persistente()
        st.rerun()

    # --------------------------------------------------
    # MENU PCL
    # --------------------------------------------------
    if st.button("PCL", key="nav_pcl", use_container_width=True):
        st.session_state.modulo = "PCL"
        st.session_state.pagina = "PCL"
        st.session_state.modulo_inicio = True
        st.session_state.pcl_doenca = None
        st.session_state.pcl_menu = None
        st.session_state.pcl_sub = None
        salvar_navegacao_persistente()
        st.rerun()

    # --------------------------------------------------
    # BOTAO OFFLINE - NOVO
    # --------------------------------------------------
    if st.button("📱 OFFLINE", key="nav_offline", use_container_width=True):
        st.session_state.modulo = None
        st.session_state.pagina = "Offline"
        salvar_navegacao_persistente()
        st.rerun()

    # --------------------------------------------------
    # SISTEMA - ATIVIDADES, CONTATO, CONFIGURACAO
    # --------------------------------------------------
    st.markdown('<div class="sidebar-section">SISTEMA</div>', unsafe_allow_html=True)

    if st.button("📋 ATIVIDADES", key="nav_atividades", use_container_width=True):
        st.session_state.modulo = None
        st.session_state.pagina = "Atividades"
        st.session_state.atividades_aberta = True
        salvar_navegacao_persistente()
        st.rerun()

    if st.button("📇 CONTATO", key="nav_contato", use_container_width=True):
        st.session_state.modulo = None
        st.session_state.pagina = "Contato"
        st.session_state.contato_aberto = True
        salvar_navegacao_persistente()
        st.rerun()

    if st.button("⚙️ CONFIGURACAO", key="nav_config", use_container_width=True):
        st.session_state.modulo = None
        st.session_state.pagina = "Configuracao"
        st.session_state.config_aberta = True
        salvar_navegacao_persistente()
        st.rerun()

    # Espaco e rodape
    st.markdown('<div class="sidebar-spacer"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-footer-line"></div>', unsafe_allow_html=True)

    if st.button("🚪 SAIR", key="nav_sair", use_container_width=True):
        encerrar_sessao_persistente(st.session_state.get("session_token"))
        limpar_navegacao_persistente()
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# =========================================================
# FLUXO PRINCIPAL - PAGINAS E MODULOS
# =========================================================

# Guarda a rota atual de forma nao sensivel para restaura-la apos F5.
salvar_navegacao_persistente()

if st.session_state.pagina == "Inicio":
    imagem_inicio = localizar_imagem_modulo("endemiasbr", "endemia")
    if imagem_inicio:
        st.image(imagem_inicio, use_container_width=True)
        st.markdown("---")
    st.title("EndemiasBR")
    st.markdown("### Sistema de Apoio à Vigilancia de Endemias")
    st.write(f"Ola, **{usuario['nome']}** — **{nivel}**")
    mostrar_escopo_usuario(usuario)

elif st.session_state.pagina == "Offline":
    # Imagem do modulo Offline
    imagem_offline = localizar_imagem_modulo("offline", "mobile", "celular")
    if imagem_offline:
        st.image(imagem_offline, use_container_width=True)
    
    st.markdown(
        '<div class="module-header">'
        '<h1>📱 Modo Offline</h1>'
        '<p>Trabalhe sem internet e sincronize depois</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    
    st.info("""
    ### 🚀 Módulo Offline em Desenvolvimento
    
    **Funcionalidades previstas:**
    - 📝 Criar registros sem internet (Diario PCDCh, Pesquisas, etc.)
    - 💾 Armazenamento local no navegador
    - 🔄 Sincronizar quando voltar online
    - 📋 Ver histórico de registros offline
    
    **Como usar:**
    1. Acesse o módulo offline antes de sair de casa (com internet)
    2. Preencha os formulá¡´rios no campo (sem internet)
    3. Ao retornar, clique em "Sincronizar Todos"
    4. Os dados serão enviados ao banco de dados
    
    ---
    
    *Em breve: integração completa com offline_utils.py e offline.py*
    """)

elif st.session_state.pagina == "Atividades":
    imagem_atividades = localizar_imagem_modulo("atividades", "atividade")
    if imagem_atividades:
        st.image(imagem_atividades, use_container_width=True)
    
    st.markdown(
        '<div class="module-header">'
        '<h1>📋 Atividades</h1>'
        '<p>Gestao, acompanhamento e historico das atividades desenvolvidas.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.info("Selecione uma opcao no menu lateral para acessar Gestao de Atividades, Recebimentos ou Historico.")

elif st.session_state.pagina == "Configuracao":
    imagem_configuracao = localizar_imagem_modulo("configuracao", "config")
    if imagem_configuracao:
        st.image(imagem_configuracao, use_container_width=True)
    
    st.markdown(
        '<div class="module-header">'
        '<h1>⚙️ Configuracao</h1>'
        '<p>Administracao e seguranca do sistema</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.info("Selecione uma opcao no menu lateral para acessar as configuracoes disponiveis.")

elif st.session_state.pagina == "Contato":
    st.markdown(
        '<div class="module-header">'
        '<h1>📇 Contato</h1>'
        '<p>Contatos institucionais por esfera de atuacao</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.info("Selecione uma opcao no menu lateral para consultar os contatos da esfera Federal, Estadual, dos Nucleos ou Municipal.")

elif st.session_state.pagina == "Sisloc":
    st.markdown(
        '<div class="module-header">'
        '<h1>🗺️ SISLOC</h1>'
        '<p>Reconhecimento Geografico</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.info("Modulo SISLOC em desenvolvimento. Selecione uma opcao no menu lateral.")

elif st.session_state.pagina == "PCDCh":
    st.markdown(
        '<div class="module-header">'
        '<h1>🔬 PCDCh</h1>'
        '<p>Pesquisas, Capturas e Diario</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.info("Modulo PCDCh em desenvolvimento. Selecione uma opcao no menu lateral.")

elif st.session_state.pagina == "PCE":
    st.markdown(
        '<div class="module-header">'
        '<h1>💧 PCE</h1>'
        '<p>Programa de Controle da Esquistossomose</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.info("Modulo PCE em desenvolvimento. Selecione uma opcao no menu lateral.")

elif st.session_state.pagina == "PCL":
    st.markdown(
        '<div class="module-header">'
        '<h1>🦠 PCL</h1>'
        '<p>Programa de Controle da Leishmaniose</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.info("Modulo PCL em desenvolvimento. Selecione uma opcao no menu lateral.")

elif st.session_state.pagina == "CentralAtividades":
    st.markdown(
        '<div class="module-header">'
        '<h1>📋 Central de Atividades</h1>'
        '<p>Planejamento, recebimento, validacao e acompanhamento das atividades</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.info("Central de Atividades em desenvolvimento.")

elif st.session_state.pagina == "CadastrosAuxiliares":
    st.markdown(
        '<div class="module-header">'
        '<h1>⚙️ Cadastros Auxiliares</h1>'
        '<p>Cadastros de apoio aos modulos do EndemiasBR</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.info("Cadastros Auxiliares em desenvolvimento.")

elif st.session_state.pagina == "Responsaveis":
    st.markdown(
        '<div class="module-header">'
        '<h1>👥 Responsaveis</h1>'
        '<p>Gerenciamento dos responsaveis e seus vinculos com os programas</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.info("Gestao de Responsaveis em desenvolvimento.")

elif st.session_state.pagina == "TrocarSenha":
    st.markdown(
        '<div class="module-header">'
        '<h1>🔑 Trocar Senha</h1>'
        '<p>Altere sua senha de acesso ao sistema</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.info("Troca de senha em desenvolvimento.")
