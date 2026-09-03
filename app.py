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
# CONTROLE CENTRAL DA SIMULAÇÃO
# =========================================================

MODO_SIMULACAO = True

st.set_page_config(page_title="EndemiasBR", page_icon="mosquito", layout="wide", initial_sidebar_state="expanded")

# =========================================================
# SESSÃO PERSISTENTE DE LOGIN
# =========================================================
# O login não depende apenas de st.session_state. Um token aleatório
# é mantido em cookie e sua versão com hash é guardada no Supabase.
# Assim, F5/atualização da página não obriga novo login.
# A senha nunca é armazenada no cookie.
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

def conectar_banco():
    try:
        return psycopg2.connect(
            host="aws-0-sa-east-1.pooler.supabase.com",
            database="postgres",
            user="postgres.gwperarqwoflsmowaxgs",
            password=st.secrets["DB_PASSWORD"],
            port="6543",
            client_encoding="UTF8"
        )
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None


def hash_token_sessao(token):
    return hashlib.sha256(str(token).encode("utf-8")).hexdigest()


def criar_sessao_persistente(usuario):
    token = secrets.token_urlsafe(48)
    conn = conectar_banco()
    if not conn:
        return None
    cur = None
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM sessoes_login WHERE expira_em <= CURRENT_TIMESTAMP")
        cur.execute("INSERT INTO sessoes_login (responsavel_id, token_hash, expira_em) VALUES (%s, %s, %s)", (int(usuario["id"]), hash_token_sessao(token), datetime.utcnow() + timedelta(days=DIAS_SESSAO)))
        conn.commit()
        COOKIES.set(NOME_COOKIE_SESSAO, token, expires_at=datetime.now() + timedelta(days=DIAS_SESSAO), path="/", secure=True, same_site="lax")
        return token
    except Exception as e:
        try: conn.rollback()
        except Exception: pass
        st.error(f"Não foi possível criar a sessão persistente: {e}")
        return None
    finally:
        if cur: cur.close()
        conn.close()


def ler_cookie_sessao():
    try:
        token = st.context.cookies.get(NOME_COOKIE_SESSAO)
        if token: return token
    except Exception: pass
    try:
        token = COOKIES.get(NOME_COOKIE_SESSAO)
        if token: return token
    except Exception: pass
    return None


def restaurar_sessao_persistente():
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
            FROM sessoes_login s JOIN responsaveis r ON r.id = s.responsavel_id
            LEFT JOIN estados e ON e.id = r.estado_id
            WHERE s.token_hash = %s AND s.expira_em > CURRENT_TIMESTAMP AND r.ativo = TRUE
            LIMIT 1
        """, (hash_token_sessao(token),))
        registro = cur.fetchone()
        if not registro: return None, token
        return dict(zip([d[0] for d in cur.description], registro)), token
    except Exception as e:
        print(f"Erro ao restaurar sessão: {e}")
        return None, token
    finally:
        if cur: cur.close()
        conn.close()


def encerrar_sessao_persistente(token=None):
    if token:
        conn = conectar_banco()
        if conn:
            cur = None
            try:
                cur = conn.cursor()
                cur.execute("DELETE FROM sessoes_login WHERE token_hash=%s", (hash_token_sessao(token),))
                conn.commit()
            except Exception:
                try: conn.rollback()
                except Exception: pass
            finally:
                if cur: cur.close()
                conn.close()
    try: COOKIES.delete(NOME_COOKIE_SESSAO)
    except Exception: pass

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
    return re.sub(r"\D", "", str(t or ""))

def formatar_cpf(cpf):
    n = so_numeros(cpf)
    return f"{n[:3]}.{n[3:6]}.{n[6:9]}-{n[9:]}" if len(n) == 11 else str(cpf or "")

def hash_senha(senha, cpf):
    return hashlib.sha256((str(senha) + so_numeros(cpf)).encode("utf-8")).hexdigest()

def senha_valida(senha):
    # O sistema aceita senha simples, conforme a regra definida para o EndemiasBR.
    # Na primeira troca, apenas orienta o usuário a preferir uma senha mais forte.
    if len(str(senha or "")) < 6:
        return False, "A senha deve ter pelo menos 6 caracteres."
    return True, ""

def buscar_usuario_por_cpf(cpf):
    conn = conectar_banco()
    if not conn: return None
    try:
        df = pd.read_sql("""
            SELECT r.*, e.nome as estado_nome, e.sigla as estado_sigla
            FROM responsaveis r LEFT JOIN estados e ON e.id = r.estado_id
            WHERE regexp_replace(r.cpf, '[^0-9]', '', 'g') = %s AND r.ativo = TRUE
        """, conn, params=(so_numeros(cpf),))
        return None if df.empty else df.iloc[0].to_dict()
    except Exception as e:
        st.error(f"Erro ao buscar usuário: {e}")
        return None
    finally:
        conn.close()

def buscar_usuario_simulacao(nome_usuario):
    """Busca a conta especial usada apenas no ambiente de simulação."""
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
        st.error(f"Erro ao buscar usuário de simulação: {e}")
        return None
    finally:
        conn.close()


def carregar_estados_todos(conn):
    return pd.read_sql("SELECT id, nome, sigla FROM estados ORDER BY nome", conn)

def carregar_estados_cadastro(conn, usuario):
    if usuario.get("nivel") == "Federal":
        return carregar_estados_todos(conn)
    estado_id = usuario.get("estado_id")
    if estado_id is None or (isinstance(estado_id, float) and pd.isna(estado_id)):
        return pd.DataFrame(columns=["id", "nome", "sigla"])
    return pd.read_sql("SELECT id, nome, sigla FROM estados WHERE id = %s", conn, params=(int(estado_id),))

# ==========================================================
# HIERARQUIA DE VISUALIZACAO E ESCOPO DE CADASTRO
# ==========================================================

def nivel_usuario(usuario):
    return str(usuario.get("nivel") or "").strip()


def obter_regional_id_usuario(conn, usuario):
    """Obtém a regional do usuário.

    Preferimos regional_id gravado no responsável.
    Como compatibilidade, se o usuário possuir municipio_id,
    descobrimos a regional pelo município.
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
                conn, params=(int(mid),)
            )
            if not df.empty and pd.notna(df.iloc[0]["regional_id"]):
                return int(df.iloc[0]["regional_id"])
        except Exception:
            pass

    return None


def municipios_para_cadastro(conn, usuario, incluir_arquivados=False, estado_id=None):
    """
    Retorna somente os municípios que o usuário pode CADASTRAR/EDITAR.

    REGRA GERAL DO SISTEMA:
      Se estado_id for informado pela tela, somente municípios daquele Estado
      podem ser retornados. Isso vale para qualquer módulo/tela que utilize
      esta função, independentemente do nível do usuário.

    Visualização e cadastro são conceitos diferentes:
      Federal  -> todos os municípios
      Estadual -> todos os municípios do próprio estado
      Regional -> somente municípios da própria regional
      Municipal -> somente o próprio município
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

    # REGRA GERAL: depois que a tela define um Estado, a lista de municípios
    # fica obrigatoriamente restrita ao estado selecionado. Assim, um usuário
    # Federal também não verá municípios de outros estados ao pesquisar.
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
    """Validação final antes de qualquer gravação municipal."""
    try:
        df = municipios_para_cadastro(conn, usuario, True)
        return not df[df["id"].astype(int) == int(municipio_id)].empty
    except Exception:
        return False


def mostrar_escopo_usuario(usuario):
    nivel = nivel_usuario(usuario)
    textos = {
        "Federal": "Cadastro/execução territorial: **todos os estados e municípios**.",
        "Estadual": "Cadastro/execução territorial: **somente o próprio estado**. Visualização: **todo o Brasil**.",
        "Regional": "Cadastro/execução territorial: **somente a própria regional**. Visualização: **todo o Brasil**.",
        "Municipal": "Cadastro/execução territorial: **somente o próprio município**. Visualização: **todo o Brasil**.",
    }
    if nivel == "Regional" and usuario.get("regional_id") is None:
        texto = textos[nivel] + " ⚠️ A regional será localizada pelo município quando possível."
    else:
        texto = textos.get(nivel, "Escopo não identificado.")
    st.caption(texto)


def garantir_tabela_responsavel_programas(conn):
    """Garante a tabela de vínculos entre responsáveis e programas."""
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
        st.error(f"Erro ao preparar os vínculos de responsáveis: {e}")
        return False
    finally:
        if cur:
            cur.close()


def localizar_imagem_modulo(*palavras):
    """Localiza imagens do módulo de forma recursiva e tolerante a
    maiúsculas/minúsculas e acentos, inclusive em subpastas do projeto.
    """
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
    for pasta in ["imagens", "img", "assets", "."]:
        for nome in nomes:
            p = os.path.join(pasta, nome)
            if os.path.exists(p):
                return p
    return None

def imagem_card(caminho, altura=220):
    if not caminho or not os.path.exists(caminho):
        return f'<div style="width:100%;height:{altura}px;background:#e8f8ee;"></div>'
    with open(caminho, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ext = caminho.lower().rsplit(".", 1)[-1]
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext
    return f'<img src="data:image/{mime};base64,{b64}" style="width:100%;height:{altura}px;object-fit:cover;object-position:center;display:block;" />'

def municipios_por_estado(conn, estado_id, incluir_arquivados=True):
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
    try:
        df = pd.read_sql("SELECT presidente, ministro_saude FROM config_nacional ORDER BY id LIMIT 1", conn)
        if df.empty:
            return {"presidente": "—", "ministro_saude": "—"}
        return {"presidente": df.iloc[0]["presidente"] or "—", "ministro_saude": df.iloc[0]["ministro_saude"] or "—"}
    except Exception:
        return {"presidente": "—", "ministro_saude": "—"}

def carregar_estado_info(conn, estado_id):
    try:
        df = pd.read_sql("""
            SELECT nome, sigla, capital, governador, secretario_saude, secretaria_nome
            FROM estados WHERE id = %s
        """, conn, params=(int(estado_id),))
        if df.empty: return None
        r = df.iloc[0]
        return {
            "nome": r["nome"], "sigla": r["sigla"], "capital": r["capital"] or "—",
            "governador": r["governador"] or "—", "secretario_saude": r["secretario_saude"] or "—",
            "secretaria_nome": r["secretaria_nome"] or "—"
        }
    except Exception:
        return None

def carregar_municipio_info(conn, mun_id):
    try:
        df = pd.read_sql("SELECT nome, prefeito, secretario_saude, status FROM municipios WHERE id = %s", conn, params=(int(mun_id),))
        if df.empty: return None
        r = df.iloc[0]
        return {"nome": r["nome"], "prefeito": r["prefeito"] or "—", "secretario_saude": r["secretario_saude"] or "—", "status": r["status"] or "Ativo"}
    except Exception:
        return None

def pesquisas_da_localidade(conn, localidade_id):
    return pd.read_sql("""
        SELECT id, data_pesquisa, tipo_pesquisa, status FROM pesquisas_entomologicas
        WHERE localidade_id = %s AND (status IS NULL OR status = 'Ativa')
        ORDER BY data_pesquisa DESC, id DESC
    """, conn, params=(int(localidade_id),))

def imoveis_da_localidade(conn, localidade_id):
    return pd.read_sql("""
        SELECT id, identificacao, quarteirao, lado, sequencia, numero, tipo
        FROM imoveis
        WHERE localidade_id = %s AND (ativo IS NULL OR ativo = TRUE)
        ORDER BY quarteirao, sequencia, id
    """, conn, params=(int(localidade_id),))

def obter_proximo_etiqueta(conn, municipio_id):
    try:
        df = pd.read_sql("SELECT proximo_numero FROM etiquetas_controle WHERE municipio_id = %s", conn, params=(int(municipio_id),))
        if df.empty:
            return 1
        return int(df.iloc[0]["proximo_numero"] or 1)
    except Exception:
        return 1

def lista_especies_triatomineo(conn):
    try:
        df = pd.read_sql(
            "SELECT nome_cientifico FROM triatominios WHERE ativo IS NULL OR ativo = TRUE ORDER BY nome_cientifico",
            conn
        )
        lista = df["nome_cientifico"].tolist() if not df.empty else []
    except Exception:
        lista = []
    if not lista:
        lista = ["Triatoma infestans", "Panstrongylus megistus", "Triatoma brasiliensis", "Triatoma sordida", "Rhodnius neglectus"]
    if "Outra" not in lista:
        lista = lista + ["Outra"]
    return lista

def garantir_tabela_pits_pcdch(conn):
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
    """Cria as tabelas modernas de planejamento do PCDCh, se ainda não existirem.

    A programação foi separada em:
      1) plano anual de parâmetros/produção; e
      2) programação mensal, que permite registrar o planejado e o realizado.
    """
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
        st.error(f"Erro ao preparar as tabelas de Programação do PCDCh: {e}")
        return False


def calcular_parametros_programacao(ud_existentes, pits_existentes, dias_pit, dias_buro, dias_borr, media_ud):
    """Calcula os parâmetros básicos do plano anual.

    O manual usa 20 dias úteis/mês como referência e orienta subtrair
    os dias de PIT, atividades burocráticas e borrifação/imprevistos.
    """
    dias_pesquisa = max(0, 20 - int(dias_pit) - int(dias_buro) - int(dias_borr))
    ud_mes = max(0, int(round(dias_pesquisa * float(media_ud or 0))))
    return dias_pesquisa, ud_mes


def atividade_programacao_pcdch():
    return [
        "Pesquisa entomológica regular",
        "Visita a PIT",
        "Borrifação",
        "Atividade burocrática",
        "Educação em saúde",
        "Outras atividades",
    ]


def garantir_tabela_desalojantes(conn):
    """Cria a tabela auxiliar de desalojantes, caso ainda não exista."""
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
        try: conn.rollback()
        except Exception: pass
        st.error(f"Erro ao preparar tabela de desalojantes: {e}")
        return False

def lista_desalojantes(conn):
    try:
        garantir_tabela_desalojantes(conn)
        df = pd.read_sql("SELECT nome FROM desalojantes WHERE ativo=TRUE ORDER BY nome", conn)
        return df["nome"].tolist()
    except Exception:
        return []

def lista_inseticidas(conn):
    try:
        df = pd.read_sql("SELECT nome FROM inseticidas WHERE ativo IS NULL OR ativo = TRUE ORDER BY nome", conn)
        return df["nome"].tolist() if not df.empty else ["K-Othrine", "Demand", "Actellic", "Ficam", "Outro"]
    except Exception:
        return ["K-Othrine", "Demand", "Actellic", "Ficam", "Outro"]

def form_campos_imovel(prefixo, valores=None):
    v = valores or {}
    identificacao = st.text_input("Identificação / Endereço *", value=str(v.get("identificacao") or ""), key=f"{prefixo}_ident")
    c1, c2, c3 = st.columns(3)
    with c1:
        quarteirao = st.text_input("Quarteirão", value=str(v.get("quarteirao") or ""), key=f"{prefixo}_q")
    with c2:
        lados = ["", "Par", "Ímpar", "Único", "A", "B"]
        lado_atual = str(v.get("lado") or "")
        idx_lado = lados.index(lado_atual) if lado_atual in lados else 0
        lado = st.selectbox("Lado", lados, index=idx_lado, key=f"{prefixo}_lado")
    with c3:
        seq_val = int(v["sequencia"]) if v.get("sequencia") not in (None, "") else 0
        sequencia = st.number_input("Sequência", min_value=0, value=seq_val, key=f"{prefixo}_seq")
    c4, c5 = st.columns(2)
    with c4:
        numero = st.text_input("Número", value=str(v.get("numero") or ""), key=f"{prefixo}_num")
    with c5:
        complemento = st.text_input("Complemento", value=str(v.get("complemento") or ""), key=f"{prefixo}_comp")
    tipos = ["Residência", "Comércio", "Escola", "Igreja", "Anexo", "Terreno baldio", "Outro"]
    tipo_atual = str(v.get("tipo") or "Residência")
    tipo = st.selectbox("Tipo de imóvel", tipos, index=tipos.index(tipo_atual) if tipo_atual in tipos else 0, key=f"{prefixo}_tipo")
    consts = ["Alvenaria", "Madeira", "Mista", "Taipa", "Outro", ""]
    tc_atual = str(v.get("tipo_construcao") or "")
    tipo_const = st.selectbox("Tipo de construção", consts, index=consts.index(tc_atual) if tc_atual in consts else 0, key=f"{prefixo}_tconst")
    sits = ["Existente", "Fechado", "Desabitado", "Em construção", "Demolido"]
    sit_atual = str(v.get("situacao") or "Existente")
    situacao = st.selectbox("Situação", sits, index=sits.index(sit_atual) if sit_atual in sits else 0, key=f"{prefixo}_sit")
    obs = st.text_area("Observações", value=str(v.get("observacao") or ""), key=f"{prefixo}_obs")
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
    """Prepara toda a estrutura persistente do PCL no PostgreSQL.

    A função é idempotente: pode ser executada toda vez que o módulo PCL
    abrir sem apagar dados existentes. As chaves territoriais apontam para
    a estrutura já existente do SISLOC por meio dos respectivos IDs.
    """
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
                status VARCHAR(80) DEFAULT 'Em investigação',
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

        # A LT também precisa ter seu próprio fluxo de vigilância do óbito.
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
                status VARCHAR(80) DEFAULT 'Em investigação',
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Índices para consultas por território e data. Não alteram dados.
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


def salvar_navegacao_persistente():
    """Salva somente a rota da tela; não salva campos, dados pessoais ou credenciais."""
    try:
        rota = {chave: st.session_state.get(chave) for chave in CHAVES_NAVEGACAO_PERSISTENTE}
        COOKIES.set(NOME_COOKIE_NAVEGACAO, json.dumps(rota, separators=(",", ":")), expires_at=datetime.now() + timedelta(days=DIAS_SESSAO), path="/", secure=True, same_site="lax")
    except Exception:
        pass


def ler_navegacao_persistente():
    valor = None
    try: valor = st.context.cookies.get(NOME_COOKIE_NAVEGACAO)
    except Exception: pass
    if not valor:
        try: valor = COOKIES.get(NOME_COOKIE_NAVEGACAO)
        except Exception: pass
    if not valor: return {}
    try:
        rota = json.loads(valor)
        return rota if isinstance(rota, dict) else {}
    except Exception:
        return {}


def restaurar_navegacao_persistente():
    rota = ler_navegacao_persistente()
    paginas_validas = {"Inicio", "Atividades", "Configuracao", "CentralAtividades", "CadastrosAuxiliares", "Responsaveis", "TrocarSenha", "Contato", "Sisloc", "PCDCh", "PCE", "PCL"}
    if rota.get("pagina") not in paginas_validas:
        return False
    for chave in CHAVES_NAVEGACAO_PERSISTENTE:
        if chave in rota:
            st.session_state[chave] = rota[chave]
    return True


def limpar_navegacao_persistente():
    try: COOKIES.delete(NOME_COOKIE_NAVEGACAO)
    except Exception: pass

for k, v in {
    "usuario": None,
    "pagina": "Inicio",
    "modulo": None,
    "modulo_inicio": False,
    "forcar_troca_senha": False,
    "config_aberta": False,
    "atividades_aberta": False,
    "atividade_aba": "Gestão de Atividades",
    "contato_aberto": False,
    "contato_aba": "Inicio",
    "menu_sisloc": "Navegação Hierárquica",
    "pcdch_menu": "Cadastro",
    "pce_menu": None,
    "pce_group": None,
    "pce_rel_sub": "PCE-101 Detalhado",
    "pce_sub": "Inclusão",
    "cad_aux_menu": "PCDCh",
    "cad_aux_item": "Desalojantes",
    "pcl_doenca": None,
    "pcl_menu": None,
    "pcl_sub": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Na primeira execução desta sessão, tenta recuperar o login persistente.
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
    st.markdown('<div class="module-header"><h1>EndemiasBR</h1><p>Sistema de Apoio à Vigilância de Endemias</p></div>', unsafe_allow_html=True)
    st.subheader("Acesso ao sistema")
    _, c2, _ = st.columns([1, 2, 1])
    with c2:
        identificacao_in = st.text_input("Usuário ou CPF" if MODO_SIMULACAO else "CPF")
        senha_in = st.text_input("Senha", type="password")
        if st.button("Entrar", type="primary", use_container_width=True):
            identificacao = str(identificacao_in or "").strip()

            # Conta especial exclusiva da simulação.
            # O usuário permanece Federal no banco para manter alcance nacional,
            # mas a interface de permissões será tratada como Municipal.
            if MODO_SIMULACAO and identificacao.casefold() == "endemias":
                u = buscar_usuario_simulacao("Endemias")
                if u is None:
                    st.error("A conta de simulação 'Endemias' ainda não foi cadastrada no banco.")
                elif hash_senha(senha_in, u["cpf"]) != (u.get("senha_hash") or "").lower():
                    st.error("Senha incorreta.")
                else:
                    # Mantém Federal no banco para o alcance territorial nacional.
                    u["nivel"] = "Federal"
                    st.session_state.usuario = u
                    st.session_state.forcar_troca_senha = False
                    st.session_state.session_token = criar_sessao_persistente(u)
                    st.session_state.pagina = "Inicio"
                    st.rerun()

            elif not so_numeros(identificacao) or not senha_in:
                st.warning("Informe usuário/CPF e senha.")
            else:
                u = buscar_usuario_por_cpf(identificacao)
                if u is None:
                    st.error("CPF não encontrado ou inativo.")
                elif hash_senha(senha_in, u["cpf"]) != (u.get("senha_hash") or "").lower():
                    st.error("Senha incorreta.")
                else:
                    st.session_state.usuario = u
                    st.session_state.forcar_troca_senha = bool(u.get("deve_trocar_senha"))
                    st.session_state.session_token = criar_sessao_persistente(u)
                    if not st.session_state.forcar_troca_senha:
                        st.session_state.pagina = "Inicio"
                    st.rerun()
    st.stop()

if st.session_state.forcar_troca_senha and st.session_state.usuario:
    u = st.session_state.usuario
    st.markdown('<div class="module-header"><h1>Troca de senha obrigatória</h1><p>Este é seu primeiro acesso. Antes de continuar, crie uma nova senha.</p></div>', unsafe_allow_html=True)
    st.info("🔐 Para maior segurança, recomendamos combinar letras maiúsculas e minúsculas, números e símbolos. Evite nomes, CPF, datas de nascimento e sequências fáceis de adivinhar.")
    n1 = st.text_input("Nova senha", type="password")
    n2 = st.text_input("Confirmar", type="password")
    if st.button("Salvar nova senha", type="primary"):
        ok, msg = senha_valida(n1)
        if not ok: st.warning(msg)
        elif n1 != n2: st.warning("Senhas não conferem.")
        elif n1 == "12345678": st.warning("Não use a senha padrão.")
        else:
            conn = conectar_banco()
            if conn:
                cur = conn.cursor()
                cur.execute("UPDATE responsaveis SET senha_hash=%s, deve_trocar_senha=FALSE WHERE id=%s",
                            (hash_senha(n1, u["cpf"]), int(u["id"])))
                conn.commit(); cur.close(); conn.close()
                st.session_state.forcar_troca_senha = False
                st.rerun()
    st.stop()

usuario = st.session_state.usuario

# O nível original continua sendo usado para ESCOPO territorial e consultas.
nivel = usuario.get("nivel", "")

# A conta Endemias, no ambiente de simulação, possui alcance Federal no banco,
# mas opera com interface e permissões de trabalho Municipal.
usuario_simulacao = (
    MODO_SIMULACAO
    and str(usuario.get("nome") or "").strip().casefold() == "endemias"
)
nivel_permissao = "Municipal" if usuario_simulacao else nivel

if MODO_SIMULACAO:
    st.info("🧪 AMBIENTE DE SIMULAÇÃO ATIVO")

# Bloqueio defensivo de páginas administrativas para a conta municipal simulada.
if usuario_simulacao and st.session_state.get("pagina") in {
    "CadastrosAuxiliares", "Responsaveis", "Autoridades"
}:
    st.session_state.pagina = "Inicio"
    st.session_state.config_aberta = False
    st.warning("Esta conta de simulação possui somente as rotinas de trabalho do nível Municipal.")
    st.rerun()

with st.sidebar:
    # ------------------------------------------------------
    # CABECALHO DO USUARIO
    # ------------------------------------------------------
    st.markdown("<div class='sidebar-brand'>EndemiasBR</div>", unsafe_allow_html=True)
    nivel_exibicao = "Municipal • Simulação nacional" if usuario_simulacao else nivel
    st.markdown(
        f"<div class='sidebar-user'><strong>{usuario['nome']}</strong><span>{nivel_exibicao}</span></div>",
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------
    # INICIO
    # ------------------------------------------------------
    if st.button("INÍCIO", key="nav_inicio", use_container_width=True):
        st.session_state.modulo = None
        st.session_state.config_aberta = False
        st.session_state.pagina = "Inicio"
        st.rerun()

    st.markdown("<div class='sidebar-section'>MÓDULOS</div>", unsafe_allow_html=True)

    # ------------------------------------------------------
    # ITENS ESPECIAIS ATIVOS — ficam logo abaixo de INÍCIO
    # ------------------------------------------------------
    especial_ativo = None
    if st.session_state.get("atividades_aberta", False):
        especial_ativo = "atividades"
    elif st.session_state.get("contato_aberto", False):
        especial_ativo = "contato"
    elif st.session_state.get("config_aberta", False):
        especial_ativo = "config"

    if especial_ativo == "atividades":
        if st.button("📋 ATIVIDADES", key="nav_atividades_top", use_container_width=True):
            st.session_state.atividades_aberta = False
            st.session_state.pagina = "Inicio"
            st.rerun()
        if st.button("Gestão de Atividades", key="nav_gestao_atividades_top", use_container_width=True):
            st.session_state.atividade_aba = "Gestão de Atividades"
            st.session_state.pagina = "CentralAtividades"
            st.rerun()
        if st.button("Recebimentos", key="nav_recebimentos_top", use_container_width=True):
            st.session_state.atividade_aba = "Recebimentos"
            st.session_state.pagina = "CentralAtividades"
            st.rerun()
        if st.button("Histórico", key="nav_historico_atividades_top", use_container_width=True):
            st.session_state.atividade_aba = "Histórico"
            st.session_state.pagina = "CentralAtividades"
            st.rerun()

    elif especial_ativo == "contato":
        if st.button("📇 CONTATO", key="nav_contato_top", use_container_width=True):
            st.session_state.contato_aberto = False
            st.session_state.pagina = "Inicio"
            st.rerun()
        if st.button("🇧🇷 Federal", key="nav_contato_federal_top", use_container_width=True):
            st.session_state.contato_aba = "Federal"
            st.session_state.pagina = "Contato"
            st.rerun()
        if st.button("🏛️ Estadual", key="nav_contato_estadual_top", use_container_width=True):
            st.session_state.contato_aba = "Estadual"
            st.session_state.pagina = "Contato"
            st.rerun()
        if st.button("🏢 Núcleos", key="nav_contato_nucleos_top", use_container_width=True):
            st.session_state.contato_aba = "Núcleos"
            st.session_state.pagina = "Contato"
            st.rerun()
        if st.button("🏘️ Municipal", key="nav_contato_municipal_top", use_container_width=True):
            st.session_state.contato_aba = "Municipal"
            st.session_state.pagina = "Contato"
            st.rerun()

    elif especial_ativo == "config":
        st.markdown("<div class='sidebar-section'>SISTEMA</div>", unsafe_allow_html=True)
        if st.button("CONFIGURAÇÃO", key="nav_config_top", use_container_width=True):
            st.session_state.config_aberta = False
            st.session_state.pagina = "Inicio"
            st.rerun()
        st.markdown("<div class='sidebar-submenu'>", unsafe_allow_html=True)
        if not usuario_simulacao:
            if st.button("GESTÃO", key="config_cad_aux_top", use_container_width=True):
                st.session_state.pagina = "CadastrosAuxiliares"
                st.session_state.cad_aux_menu = "PCDCh"
                st.session_state.cad_aux_item = "Desalojantes"
                st.rerun()
            if st.button("Responsáveis", key="config_responsaveis_top", use_container_width=True):
                st.session_state.pagina = "Responsaveis"
                st.rerun()
        if st.button("Trocar minha senha", key="config_senha_top", use_container_width=True):
            st.session_state.pagina = "TrocarSenha"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ------------------------------------------------------
    # MENU SISLOC
    # ------------------------------------------------------
    if st.session_state.modulo == "Sisloc":
        if st.button("SISLOC", key="nav_sisloc_active", use_container_width=True):
            st.session_state.modulo = None
            st.session_state.modulo_inicio = False
            st.session_state.pagina = "Inicio"
            st.rerun()

        st.markdown("<div class='sidebar-submenu'>", unsafe_allow_html=True)
        sisloc_opcoes = [
            "Navegação Hierárquica",
            "Localidades",
            "Cadastrar Localidade",
            "Editar / Arquivar Localidade",
            "Editar / Arquivar Município",
            "Imóveis",
            "Editar / Excluir Imóvel",
        ]
        for i, opcao in enumerate(sisloc_opcoes):
            if st.button(f"{i+1}. {opcao}", key=f"side_sisloc_{i}", use_container_width=True):
                st.session_state.menu_sisloc = opcao
                st.session_state.modulo_inicio = False
                st.session_state.pagina = "Sisloc"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("PCDCh", key="nav_pcdch_from_sisloc", use_container_width=True):
            st.session_state.modulo = "PCDCh"
            st.session_state.pagina = "PCDCh"
            st.session_state.modulo_inicio = True
            st.session_state.pcdch_menu = None
            st.rerun()
        if st.button("PCE", key="nav_pce_from_sisloc", use_container_width=True):
            st.session_state.modulo = "PCE"
            st.session_state.pagina = "PCE"
            st.session_state.modulo_inicio = True
            st.session_state.pce_menu = None
            st.session_state.pce_group = None
            st.rerun()
        if st.button("PCL", key="nav_pcl_from_sisloc", use_container_width=True):
            st.session_state.modulo = "PCL"
            st.session_state.pagina = "PCL"
            st.session_state.modulo_inicio = True
            st.session_state.pcl_doenca = None
            st.session_state.pcl_menu = None
            st.session_state.pcl_sub = None
            st.rerun()

    # ------------------------------------------------------
    # MENU PCDCh
    # ------------------------------------------------------
    elif st.session_state.modulo == "PCDCh":
        if st.button("PCDCh", key="nav_pcdch_active", use_container_width=True):
            st.session_state.modulo = None
            st.session_state.modulo_inicio = False
            st.session_state.pagina = "Inicio"
            st.rerun()

        st.markdown("<div class='sidebar-submenu'>", unsafe_allow_html=True)
        pcdch_opcoes = ["Programação", "Cadastro", "Pesquisa", "Captura", "Diário", "PIT", "Exame"]
        pcdch_atual = st.session_state.get("pcdch_menu", "Cadastro")
        pcdch_subitens = {
            "Cadastro": ["Agente", "Imóvel", "Etiqueta", "Triatomínio", "Inseticida"],
            "Pesquisa": ["Nova Pesquisa", "Listar", "Editar / Arquivar"],
            "Captura": ["Nova Captura", "Listar", "Editar / Arquivar"],
            "Diário": ["Novo (unidade domiciliar)", "Listar", "Arquivar"],
        }
        for i, opcao in enumerate(pcdch_opcoes):
            if st.button(f"{i+1}. {opcao}", key=f"side_pcdch_{i}", use_container_width=True):
                st.session_state.pcdch_menu = opcao
                st.session_state.pcdch_sub = None
                st.session_state.modulo_inicio = False
                st.session_state.pagina = "PCDCh"
                st.rerun()
            if pcdch_atual == opcao and opcao in pcdch_subitens:
                st.markdown(f"<div class='sidebar-module-active'>{opcao}</div>", unsafe_allow_html=True)
                for j, subop in enumerate(pcdch_subitens[opcao]):
                    if st.button(subop, key=f"side_pcdch_sub_{i}_{j}", use_container_width=True):
                        st.session_state.pcdch_sub = subop
                        st.session_state.pcdch_menu = opcao
                        st.session_state.modulo_inicio = False
                        st.session_state.pagina = "PCDCh"
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("SISLOC", key="nav_sisloc_from_pcdch", use_container_width=True):
            st.session_state.modulo = "Sisloc"
            st.session_state.pagina = "Sisloc"
            st.session_state.modulo_inicio = True
            st.session_state.menu_sisloc = "Navegação Hierárquica"
            st.rerun()
        if st.button("PCE", key="nav_pce_from_pcdch", use_container_width=True):
            st.session_state.modulo = "PCE"
            st.session_state.pagina = "PCE"
            st.session_state.modulo_inicio = True
            st.session_state.pce_menu = None
            st.session_state.pce_group = None
            st.rerun()
        if st.button("PCL", key="nav_pcl_from_pcdch", use_container_width=True):
            st.session_state.modulo = "PCL"
            st.session_state.pagina = "PCL"
            st.session_state.modulo_inicio = True
            st.session_state.pcl_doenca = None
            st.session_state.pcl_menu = None
            st.session_state.pcl_sub = None
            st.rerun()

    # ------------------------------------------------------
    # MENU PCE
    # ------------------------------------------------------
    elif st.session_state.modulo == "PCE":
        grupo_atual = st.session_state.get("pce_group")
        menu_atual = st.session_state.get("pce_menu")

        # NÍVEL 1: PCE -> Cadastro / Atividades / Relatórios
        if grupo_atual not in ("Cadastro", "Atividades", "Relatórios"):
            if st.button("PCE", key="nav_pce_active", use_container_width=True):
                st.session_state.modulo = None
                st.session_state.pagina = "Inicio"
                st.rerun()
            st.markdown("<div class='sidebar-submenu'>", unsafe_allow_html=True)
            for i, grupo in enumerate(["Cadastro", "Atividades", "Relatórios"]):
                if st.button(grupo, key=f"side_pce_group_{i}", use_container_width=True):
                    st.session_state.pce_group = grupo
                    st.session_state.pce_menu = grupo
                    st.session_state.pce_sub = None
                    st.session_state.modulo_inicio = False
                    if grupo == "Relatórios":
                        st.session_state.pce_rel_sub = "PCE-101 Detalhado"
                    st.session_state.pagina = "PCE"
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # NÍVEL 2: grupo escolhido
        else:
            # Se uma função foi aberta, mostramos SOMENTE ela e seus subitens.
            if menu_atual not in (None, grupo_atual):
                voltar = "← " + grupo_atual
                if st.button(voltar, key="nav_pce_back_group", use_container_width=True):
                    st.session_state.pce_menu = grupo_atual
                    st.session_state.pce_sub = None
                    st.rerun()
                st.markdown(f"<div class='sidebar-module-active'>{menu_atual.replace(' — Coproscopia/Tratamento','').replace(' — Pesquisa Malacológica','')}</div>", unsafe_allow_html=True)
                st.markdown("<div class='sidebar-submenu'>", unsafe_allow_html=True)

                if menu_atual == "PCE-101 — Coproscopia/Tratamento":
                    subitens = ["Inclusão", "Alteração", "Consulta"]
                elif menu_atual == "PCE-102 — Pesquisa Malacológica":
                    subitens = ["Nova", "Listar", "Arquivar"]
                elif menu_atual == "PCE-108 — Casos da Rede Básica":
                    subitens = ["Inclusão", "Alteração", "Consulta"]
                elif menu_atual == "Atividades Educativas":
                    subitens = ["Nova", "Listar"]
                elif menu_atual == "Atividades de Saneamento":
                    subitens = ["Nova", "Listar"]
                elif menu_atual == "PCE-102A — Coleção Hídrica":
                    subitens = ["Inclusão", "Alteração", "Consulta"]
                elif menu_atual == "Etiquetas":
                    subitens = ["Gerar etiquetas", "Consultar"]
                else:
                    subitens = []

                for i, sub in enumerate(subitens):
                    if st.button(sub, key=f"side_pce_sub_{i}", use_container_width=True):
                        st.session_state.pce_sub = sub
                        st.session_state.modulo_inicio = False
                        st.session_state.pagina = "PCE"
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            else:
                if st.button("← PCE", key="nav_pce_back", use_container_width=True):
                    st.session_state.pce_group = None
                    st.session_state.pce_menu = None
                    st.session_state.pce_sub = None
                    st.session_state.modulo_inicio = True
                    st.session_state.pagina = "PCE"
                    st.rerun()

                st.markdown(f"<div class='sidebar-module-active'>{grupo_atual}</div>", unsafe_allow_html=True)
                st.markdown("<div class='sidebar-submenu'>", unsafe_allow_html=True)

                if grupo_atual == "Cadastro":
                    opcoes = ["Coleção Hídrica", "Etiquetas"]
                elif grupo_atual == "Atividades":
                    opcoes = ["PCE-101", "PCE-108 — Casos da Rede Básica", "Pesquisa Malacológica", "Atividades Educativas", "Atividades de Saneamento"]
                else:
                    opcoes = ["PCE-101 Detalhado", "PCE-101 Resumo", "Malacologia", "Atividades Educativas", "Atividades de Saneamento", "Sinopse", "Localidade / Prevalência", "Casos da Rede Básica", "Relatórios Gerados"]

                for i, opcao in enumerate(opcoes):
                    if st.button(opcao, key=f"side_pce_item_{i}", use_container_width=True):
                        if grupo_atual == "Cadastro":
                            st.session_state.pce_menu = "PCE-102A — Coleção Hídrica" if opcao == "Coleção Hídrica" else "Etiquetas"
                        elif grupo_atual == "Atividades":
                            mapa = {
                                "PCE-101": "PCE-101 — Coproscopia/Tratamento",
                                "PCE-108 — Casos da Rede Básica": "PCE-108 — Casos da Rede Básica",
                                "Pesquisa Malacológica": "PCE-102 — Pesquisa Malacológica",
                                "Atividades Educativas": "Atividades Educativas",
                                "Atividades de Saneamento": "Atividades de Saneamento",
                            }
                            st.session_state.pce_menu = mapa[opcao]
                        else:
                            st.session_state.pce_menu = "Relatórios"
                            st.session_state.pce_rel_sub = opcao
                        st.session_state.pce_sub = None
                        st.session_state.modulo_inicio = False
                        st.session_state.pagina = "PCE"
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        if grupo_atual not in ("Cadastro", "Atividades", "Relatórios"):
            if st.button("SISLOC", key="nav_sisloc_from_pce", use_container_width=True):
                st.session_state.modulo = "Sisloc"
                st.session_state.pagina = "Sisloc"
                st.session_state.menu_sisloc = "Navegação Hierárquica"
                st.rerun()
            if st.button("PCDCh", key="nav_pcdch_from_pce", use_container_width=True):
                st.session_state.modulo = "PCDCh"
                st.session_state.pagina = "PCDCh"
                st.session_state.modulo_inicio = True
                st.session_state.pcdch_menu = None
                st.session_state.pcdch_group = None
                st.rerun()
            if st.button("PCL", key="nav_pcl_from_pce", use_container_width=True):
                st.session_state.modulo = "PCL"
                st.session_state.pagina = "PCL"
                st.session_state.modulo_inicio = True
                st.session_state.pcl_doenca = None
                st.session_state.pcl_menu = None
                st.session_state.pcl_sub = None
                st.rerun()


    # ------------------------------------------------------
    # MENU PCL — PROGRAMA DE CONTROLE DA LEISHMANIOSE
    #
    # Regra de navegação:
    #   • Ao abrir o PCL: somente o botão PCL aparece na lateral.
    #     A escolha LV/LT fica exclusivamente na área principal.
    #   • Depois de escolher LV ou LT: a lateral passa a mostrar
    #     somente as áreas de operação daquela modalidade.
    #     As mesmas opções NÃO são repetidas na área principal.
    # ------------------------------------------------------
    elif st.session_state.modulo == "PCL":
        if st.button("PCL", key="nav_pcl_active", use_container_width=True):
            st.session_state.pcl_doenca = None
            st.session_state.pcl_menu = None
            st.session_state.pcl_sub = None
            st.session_state.modulo = None
            st.session_state.modulo_inicio = False
            st.session_state.pagina = "Inicio"
            st.rerun()

        doenca = st.session_state.get("pcl_doenca")

        # Quando o PCL é aberto, a escolha da doença fica na lateral.
        # Depois de escolher LV/LT, mostramos as áreas de operação daquela doença.
        if not doenca:
            st.markdown("<div class='sidebar-submenu'>", unsafe_allow_html=True)
            if st.button("Leishmaniose Visceral (LV)", key="nav_pcl_lv", use_container_width=True):
                st.session_state.pcl_doenca = "LV"
                st.session_state.pcl_menu = None
                st.session_state.pcl_sub = None
                st.session_state.modulo_inicio = False
                st.session_state.pagina = "PCL"
                st.rerun()
            if st.button("Leishmaniose Tegumentar (LT)", key="nav_pcl_lt", use_container_width=True):
                st.session_state.pcl_doenca = "LT"
                st.session_state.pcl_menu = None
                st.session_state.pcl_sub = None
                st.session_state.modulo_inicio = False
                st.session_state.pagina = "PCL"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        else:
            titulo_doenca = "Leishmaniose Visceral (LV)" if doenca == "LV" else "Leishmaniose Tegumentar (LT)"
            st.markdown(f"<div class='sidebar-module-active'>{titulo_doenca}</div>", unsafe_allow_html=True)

            if st.button("← Voltar ao PCL", key="nav_pcl_back_module", use_container_width=True):
                st.session_state.pcl_doenca = None
                st.session_state.pcl_menu = None
                st.session_state.pcl_sub = None
                st.session_state.modulo_inicio = True
                st.session_state.pagina = "PCL"
                st.rerun()

            st.markdown("<div class='sidebar-submenu'>", unsafe_allow_html=True)
            opcoes_lv = [
                "Vigilância Humana", "Vigilância Canina", "Vigilância Entomológica",
                "Investigação", "Ações de Controle", "Vigilância do Óbito", "Relatórios e Indicadores"
            ]
            opcoes_lt = [
                "Vigilância de Casos", "Investigação", "Acompanhamento",
                "Vigilância Entomológica", "Ações de Controle", "Relatórios e Indicadores"
            ]
            opcoes = opcoes_lv if doenca == "LV" else opcoes_lt

            for i, opcao in enumerate(opcoes):
                if st.button(opcao, key=f"nav_pcl_{doenca}_{i}", use_container_width=True):
                    st.session_state.pcl_menu = opcao
                    st.session_state.pcl_sub = None
                    st.session_state.modulo_inicio = False
                    st.session_state.pagina = "PCL"
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        if st.button("SISLOC", key="nav_sisloc_from_pcl", use_container_width=True):
            st.session_state.modulo = "Sisloc"
            st.session_state.pagina = "Sisloc"
            st.session_state.modulo_inicio = True
            st.session_state.menu_sisloc = "Navegação Hierárquica"
            st.rerun()
        if st.button("PCDCh", key="nav_pcdch_from_pcl", use_container_width=True):
            st.session_state.modulo = "PCDCh"
            st.session_state.pagina = "PCDCh"
            st.session_state.modulo_inicio = True
            st.session_state.pcdch_menu = None
            st.rerun()
        if st.button("PCE", key="nav_pce_from_pcl", use_container_width=True):
            st.session_state.modulo = "PCE"
            st.session_state.pagina = "PCE"
            st.session_state.modulo_inicio = True
            st.session_state.pce_menu = None
            st.session_state.pce_group = None
            st.rerun()

 # --------------------------------------------------
    # BOTAO OFFLINE - NOVO
    # --------------------------------------------------
    if st.button("📱 OFFLINE", key="nav_offline", use_container_width=True):
        st.session_state.modulo = None
        st.session_state.pagina = "Offline"
        salvar_navegacao_persistente()
        st.rerun()

    # ------------------------------------------------------
    # NENHUM MODULO ABERTO
    # ------------------------------------------------------
    else:
        if st.button("SISLOC", key="nav_sisloc", use_container_width=True):
            st.session_state.modulo = "Sisloc"
            st.session_state.pagina = "Sisloc"
            st.session_state.modulo_inicio = True
            st.session_state.menu_sisloc = "Navegação Hierárquica"
            st.session_state.config_aberta = False
            st.rerun()
        if st.button("PCDCh", key="nav_pcdch", use_container_width=True):
            st.session_state.modulo = "PCDCh"
            st.session_state.pagina = "PCDCh"
            st.session_state.modulo_inicio = True
            st.session_state.pcdch_menu = None
            st.session_state.config_aberta = False
            st.rerun()
        if st.button("PCE", key="nav_pce", use_container_width=True):
            st.session_state.modulo = "PCE"
            st.session_state.pagina = "PCE"
            st.session_state.modulo_inicio = True
            st.session_state.pce_menu = None
            st.session_state.pce_group = None
            st.session_state.config_aberta = False
            st.rerun()

        if st.button("PCL", key="nav_pcl", use_container_width=True):
            st.session_state.modulo = "PCL"
            st.session_state.pagina = "PCL"
            st.session_state.modulo_inicio = True
            st.session_state.pcl_doenca = None
            st.session_state.pcl_menu = None
            st.session_state.pcl_sub = None
            st.session_state.config_aberta = False
            st.rerun()

    # ------------------------------------------------------
    # ATIVIDADES
    # ------------------------------------------------------
    if especial_ativo != "atividades" and not st.session_state.get("atividades_aberta", False):
        if st.button("📋 ATIVIDADES", key="nav_atividades", use_container_width=True):
            st.session_state.modulo = None
            st.session_state.config_aberta = False
            st.session_state.contato_aberto = False
            st.session_state.atividades_aberta = True
            st.session_state.atividade_aba = "Gestão de Atividades"
            st.session_state.pagina = "Atividades"
            st.rerun()
    elif especial_ativo != "atividades":
        if st.button("📋 ATIVIDADES", key="nav_atividades", use_container_width=True):
            st.session_state.atividades_aberta = False
            st.session_state.pagina = "Inicio"
            st.rerun()

        if st.button("Gestão de Atividades", key="nav_gestao_atividades", use_container_width=True):
            st.session_state.atividade_aba = "Gestão de Atividades"
            st.session_state.pagina = "CentralAtividades"
            st.rerun()

        if st.button("Recebimentos", key="nav_recebimentos", use_container_width=True):
            st.session_state.atividade_aba = "Recebimentos"
            st.session_state.pagina = "CentralAtividades"
            st.rerun()

        if st.button("Histórico", key="nav_historico_atividades", use_container_width=True):
            st.session_state.atividade_aba = "Histórico"
            st.session_state.pagina = "CentralAtividades"
            st.rerun()

    # ------------------------------------------------------
    # CONTATO
    # ------------------------------------------------------
    if especial_ativo != "contato" and not st.session_state.get("contato_aberto", False):
        if st.button("📇 CONTATO", key="nav_contato", use_container_width=True):
            st.session_state.modulo = None
            st.session_state.config_aberta = False
            st.session_state.atividades_aberta = False
            st.session_state.contato_aberto = True
            st.session_state.contato_aba = "Inicio"
            st.session_state.pagina = "Contato"
            st.rerun()
    elif especial_ativo != "contato":
        if st.button("📇 CONTATO", key="nav_contato", use_container_width=True):
            st.session_state.contato_aberto = False
            st.session_state.pagina = "Inicio"
            st.rerun()

        if st.button("🇧🇷 Federal", key="nav_contato_federal", use_container_width=True):
            st.session_state.contato_aba = "Federal"
            st.session_state.pagina = "Contato"
            st.rerun()

        if st.button("🏛️ Estadual", key="nav_contato_estadual", use_container_width=True):
            st.session_state.contato_aba = "Estadual"
            st.session_state.pagina = "Contato"
            st.rerun()

        if st.button("🏢 Núcleos", key="nav_contato_nucleos", use_container_width=True):
            st.session_state.contato_aba = "Núcleos"
            st.session_state.pagina = "Contato"
            st.rerun()

        if st.button("🏘️ Municipal", key="nav_contato_municipal", use_container_width=True):
            st.session_state.contato_aba = "Municipal"
            st.session_state.pagina = "Contato"
            st.rerun()

    # ------------------------------------------------------
    # CONFIGURAÇÃO
    # ------------------------------------------------------
    if especial_ativo != "config":
        st.markdown("<div class='sidebar-section'>SISTEMA</div>", unsafe_allow_html=True)

    if especial_ativo != "config" and st.button("CONFIGURAÇÃO", key="nav_config", use_container_width=True):
        if st.session_state.get("config_aberta", False):
            st.session_state.config_aberta = False
            st.session_state.pagina = "Inicio"
        else:
            st.session_state.modulo = None
            st.session_state.atividades_aberta = False
            st.session_state.contato_aberto = False
            st.session_state.config_aberta = True
            st.session_state.pagina = "Configuracao"
        st.rerun()

    if especial_ativo != "config" and st.session_state.get("config_aberta", False):
        st.markdown("<div class='sidebar-submenu'>", unsafe_allow_html=True)
        if not usuario_simulacao:
            if st.button("GESTÃO", key="config_cad_aux", use_container_width=True):
                st.session_state.pagina = "CadastrosAuxiliares"
                st.session_state.cad_aux_menu = "PCDCh"
                st.session_state.cad_aux_item = "Desalojantes"
                st.rerun()
            if st.button("Responsáveis", key="config_responsaveis", use_container_width=True):
                st.session_state.pagina = "Responsaveis"
                st.rerun()
        if st.button("Trocar minha senha", key="config_senha", use_container_width=True):
            st.session_state.pagina = "TrocarSenha"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='sidebar-spacer'></div>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-footer-line'></div>", unsafe_allow_html=True)
    if st.button("SAIR", key="nav_sair", use_container_width=True):
        encerrar_sessao_persistente(st.session_state.get("session_token"))
        limpar_navegacao_persistente()
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


# Guarda a rota atual de forma não sensível para restaurá-la após F5.
salvar_navegacao_persistente()

if st.session_state.pagina == "Inicio":
    imagem_inicio = localizar_imagem_modulo("endemiasbr", "endemia")
    if imagem_inicio:
        st.image(imagem_inicio, use_container_width=True)
        st.markdown("---")
    st.title("EndemiasBR")
    st.markdown("### Sistema de Apoio à Vigilância de Endemias")
    st.write(f"Olá, **{usuario['nome']}** — **{nivel}**")
    if nivel == "Federal":
        st.success("Escopo: **Nacional** (cadastro e visualização)")
    elif usuario.get("estado_nome"):
        st.success(f"Cadastro: **{usuario['estado_nome']}** · Visualização: **todos os estados**")

elif st.session_state.pagina == "Atividades":
    imagem_atividades = localizar_imagem_modulo("atividades", "atividade")
    if imagem_atividades:
        st.image(imagem_atividades, use_container_width=True)

    st.markdown(
        """
        <div class="module-header">
            <h1>📋 Atividades</h1>
            <p>Gestão, acompanhamento e histórico das atividades desenvolvidas.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info("Selecione uma opção no menu lateral para acessar Gestão de Atividades, Recebimentos ou Histórico.")

elif st.session_state.pagina == "Configuracao":
    imagem_configuracao = localizar_imagem_modulo("configuracao", "configuracao")
    if imagem_configuracao:
        st.image(imagem_configuracao, use_container_width=True)

    st.markdown(
        '<div class="module-header"><h1>Configuração</h1><p>Administração e segurança do sistema</p></div>',
        unsafe_allow_html=True,
    )
    st.info("Selecione uma opção no menu lateral para acessar as configurações disponíveis.")

elif st.session_state.pagina == "CentralAtividades":

    st.markdown(
        '<div class="module-header">'
        '<h1>📋 Central de Atividades</h1>'
        '<p>Planejamento, recebimento, validação e acompanhamento das atividades</p>'
        '</div>',
        unsafe_allow_html=True
    )

    conn = conectar_banco()

    if not conn:
        st.stop()

    if not garantir_tabela_responsavel_programas(conn):
        conn.close()
        st.stop()

    # ======================================================
    # PROGRAMAS AOS QUAIS O USUÁRIO TEM ACESSO
    # ======================================================

    programas_validos = ["SISLOC", "PCDCh", "PCE", "PCL"]

    try:
        df_programas = pd.read_sql(
            """
            SELECT programa
            FROM responsavel_programas
            WHERE responsavel_id = %s
              AND ativo = TRUE
            ORDER BY programa
            """,
            conn,
            params=(int(usuario["id"]),)
        )

        programas_usuario = (
            df_programas["programa"].tolist()
            if not df_programas.empty
            else []
        )

    except Exception as e:
        st.error(f"Erro ao carregar os programas do responsável: {e}")
        conn.close()
        st.stop()

    # ======================================================
    # IDENTIFICAÇÃO DA ESFERA
    # ======================================================

    esfera_atual = str(nivel or "").strip()

    if esfera_atual == "Federal":
        esfera_destino_padrao = "Estadual"

    elif esfera_atual == "Estadual":
        esfera_destino_padrao = "Regional"

    elif esfera_atual in ["Regional", "Núcleo", "NRS"]:
        esfera_destino_padrao = "Municipal"

    else:
        esfera_destino_padrao = None

    # ======================================================
    # CABEÇALHO DO USUÁRIO
    # ======================================================

    if programas_usuario:

        nomes_programas = ", ".join(programas_usuario)

        st.info(
            f"Responsável: **{usuario['nome']}**  \n"
            f"Esfera: **{esfera_atual}**  \n"
            f"Programa(s): **{nomes_programas}**"
        )

    else:

        st.warning(
            "Nenhum programa foi vinculado a este responsável ainda. "
            "O acesso aos programas será definido na área de Responsáveis."
        )

    # ======================================================
    # CONTROLE DA ÁREA SELECIONADA NO MENU LATERAL
    # ======================================================

    atividade_aba = st.session_state.get(
        "atividade_aba",
        "Gestão de Atividades"
    )

    # ======================================================
    # GESTÃO DE ATIVIDADES
    # ======================================================

    if atividade_aba == "Gestão de Atividades":

        st.subheader("Gestão de Atividades")

        if esfera_destino_padrao is None:

            st.info(
                "Na esfera Municipal, as atividades são recebidas "
                "da estrutura regional responsável."
            )

        elif not programas_usuario:

            st.warning(
                "Este responsável ainda não possui nenhum programa vinculado."
            )

        else:

            st.caption(
                f"Defina atividades, critérios, rotinas e prazos "
                f"para a esfera **{esfera_destino_padrao}**."
            )

            programa_selecionado = st.selectbox(
                "Programa",
                programas_usuario,
                key="central_programa_gestao"
            )

            with st.form("form_nova_atividade"):

                atividade = st.text_input(
                    "Nome da atividade"
                )

                competencia = st.text_input(
                    "Competência",
                    placeholder="Ex.: Setembro/2026"
                )

                col1, col2 = st.columns(2)

                with col1:
                    data_inicio = st.date_input(
                        "Data inicial"
                    )

                with col2:
                    data_final = st.date_input(
                        "Prazo final"
                    )

                criterios = st.text_area(
                    "Critérios",
                    placeholder=(
                        "Informe os critérios que deverão ser "
                        "observados na realização da atividade."
                    ),
                    height=120
                )

                orientacoes = st.text_area(
                    "Orientações e rotinas",
                    placeholder=(
                        "Informe as orientações para execução "
                        "da atividade."
                    ),
                    height=120
                )

                publicar = st.form_submit_button(
                    "PUBLICAR ATIVIDADE",
                    type="primary",
                    use_container_width=True
                )

            if publicar:

                if not atividade.strip():

                    st.warning(
                        "Informe o nome da atividade."
                    )

                elif data_final < data_inicio:

                    st.warning(
                        "A data final não pode ser anterior "
                        "à data inicial."
                    )

                else:

                    try:

                        estado_id = usuario.get("estado_id")
                        regional_id = usuario.get("regional_id")

                        cur = conn.cursor()

                        cur.execute(
                            """
                            INSERT INTO criterios_atividades (
                                programa,
                                atividade,
                                esfera_origem,
                                esfera_destino,
                                estado_id,
                                regional_id,
                                competencia,
                                data_inicio,
                                data_final,
                                criterios,
                                orientacoes,
                                criado_por,
                                ativo
                            )
                            VALUES (
                                %s, %s, %s, %s,
                                %s, %s, %s, %s,
                                %s, %s, %s, %s,
                                TRUE
                            )
                            """,
                            (
                                programa_selecionado,
                                atividade.strip(),
                                esfera_atual,
                                esfera_destino_padrao,
                                int(estado_id)
                                if estado_id is not None
                                else None,
                                int(regional_id)
                                if regional_id is not None
                                else None,
                                competencia.strip()
                                if competencia
                                else None,
                                data_inicio,
                                data_final,
                                criterios.strip()
                                if criterios
                                else None,
                                orientacoes.strip()
                                if orientacoes
                                else None,
                                int(usuario["id"])
                            )
                        )

                        conn.commit()

                        cur.close()

                        st.success(
                            "Atividade publicada com sucesso!"
                        )

                        st.rerun()

                    except Exception as e:

                        conn.rollback()

                        st.error(
                            f"Erro ao publicar atividade: {e}"
                        )

        st.markdown("---")

        st.subheader("Atividades publicadas")

        try:

            if esfera_atual == "Federal":

                sql_atividades = """
                    SELECT
                        id,
                        programa,
                        atividade,
                        competencia,
                        data_inicio,
                        data_final,
                        esfera_destino,
                        ativo
                    FROM criterios_atividades
                    WHERE esfera_origem = %s
                    ORDER BY criado_em DESC
                """

                params_atividades = (
                    esfera_atual,
                )

            else:

                estado_id = usuario.get("estado_id")

                sql_atividades = """
                    SELECT
                        id,
                        programa,
                        atividade,
                        competencia,
                        data_inicio,
                        data_final,
                        esfera_destino,
                        ativo
                    FROM criterios_atividades
                    WHERE esfera_origem = %s
                      AND (
                            estado_id = %s
                            OR estado_id IS NULL
                          )
                    ORDER BY criado_em DESC
                """

                params_atividades = (
                    esfera_atual,
                    int(estado_id)
                    if estado_id is not None
                    else None
                )

            df_atividades = pd.read_sql(
                sql_atividades,
                conn,
                params=params_atividades
            )

            if not df_atividades.empty:

                if programas_usuario:
                    df_atividades = df_atividades[
                        df_atividades["programa"].isin(
                            programas_usuario
                        )
                    ]

                st.dataframe(
                    df_atividades,
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.info(
                    "Nenhuma atividade publicada por esta esfera."
                )

        except Exception as e:

            st.error(
                f"Erro ao carregar atividades: {e}"
            )

    # ======================================================
    # RECEBIMENTOS
    # ======================================================

    if atividade_aba == "Recebimentos":

        st.subheader("📥 Recebimentos")

        if not programas_usuario:

            st.warning(
                "Nenhum programa foi vinculado a este responsável."
            )

        else:

            try:

                placeholders = ",".join(
                    ["%s"] * len(programas_usuario)
                )

                sql_recebimentos = f"""
                    SELECT
                        id,
                        programa,
                        atividade,
                        competencia,
                        status,
                        origem_esfera,
                        destino_esfera,
                        data_envio,
                        observacao
                    FROM atividades_fluxo
                    WHERE programa IN ({placeholders})
                      AND destino_esfera = %s
                    ORDER BY data_envio DESC NULLS LAST
                """

                params_recebimentos = (
                    *programas_usuario,
                    esfera_atual
                )

                df_recebimentos = pd.read_sql(
                    sql_recebimentos,
                    conn,
                    params=params_recebimentos
                )

                if df_recebimentos.empty:

                    st.info(
                        "Nenhuma atividade aguardando recebimento."
                    )

                else:

                    st.dataframe(
                        df_recebimentos,
                        use_container_width=True,
                        hide_index=True
                    )

            except Exception as e:

                st.error(
                    f"Erro ao carregar recebimentos: {e}"
                )

    # ======================================================
    # HISTÓRICO
    # ======================================================

    if atividade_aba == "Histórico":

        st.subheader("📜 Histórico de tramitação")

        try:

            if programas_usuario:

                placeholders = ",".join(
                    ["%s"] * len(programas_usuario)
                )

                sql_historico = f"""
                    SELECT
                        h.id,
                        f.programa,
                        f.atividade,
                        h.acao,
                        h.esfera_origem,
                        h.esfera_destino,
                        h.observacao,
                        h.data_acao
                    FROM atividades_fluxo_historico h
                    JOIN atividades_fluxo f
                        ON f.id = h.atividade_fluxo_id
                    WHERE f.programa IN ({placeholders})
                    ORDER BY h.data_acao DESC
                """

                df_historico = pd.read_sql(
                    sql_historico,
                    conn,
                    params=tuple(programas_usuario)
                )

                if df_historico.empty:

                    st.info(
                        "Ainda não existe histórico de tramitação."
                    )

                else:

                    st.dataframe(
                        df_historico,
                        use_container_width=True,
                        hide_index=True
                    )

            else:

                st.info(
                    "Nenhum programa vinculado a este responsável."
                )

        except Exception as e:

            st.error(
                f"Erro ao carregar histórico: {e}"
            )

    conn.close()

elif st.session_state.pagina == "CadastrosAuxiliares":
    st.markdown('<div class="module-header"><h1>Responsáveis</h1><p>Gerenciamento dos responsáveis e seus vínculos com os programas do EndemiasBR</p></div>', unsafe_allow_html=True)
    conn = conectar_banco()
    if not conn:
        st.stop()

    # ======================================================
    # GESTÃO DE RESPONSÁVEIS
    # ======================================================
    modulos_aux = ["SISLOC", "PCDCh", "PCE", "PCL"]

    try:
        if not garantir_tabela_responsavel_programas(conn):
            conn.close()
            st.stop()

        # --------------------------------------------------
        # QUEM JÁ ESTÁ CADASTRADO
        # --------------------------------------------------
        st.subheader("Responsáveis já cadastrados")
        st.caption("Selecione uma pessoa para visualizar os programas aos quais ela está vinculada.")

        df_responsaveis = pd.read_sql(
            "SELECT id, cpf, nome, nivel FROM responsaveis WHERE ativo=TRUE ORDER BY nome",
            conn
        )

        if df_responsaveis.empty:
            st.info("Ainda não existe nenhum responsável cadastrado.")
        else:
            opcoes_cadastrados = {
                f"{row['nome']} — CPF {formatar_cpf(row['cpf'])}": int(row['id'])
                for _, row in df_responsaveis.iterrows()
            }
            pessoa_escolhida = st.selectbox(
                "Responsável cadastrado",
                list(opcoes_cadastrados.keys()),
                key="responsavel_visualizar"
            )
            responsavel_id_escolhido = opcoes_cadastrados[pessoa_escolhida]

            df_vinculos = pd.read_sql(
                """
                SELECT programa
                FROM responsavel_programas
                WHERE responsavel_id=%s AND COALESCE(ativo, TRUE)=TRUE
                ORDER BY programa
                """,
                conn,
                params=(responsavel_id_escolhido,)
            )
            programas_vinculados = set(df_vinculos["programa"].tolist()) if not df_vinculos.empty else set()

            st.markdown("**Programas vinculados:**")
            st.caption("Marque ou desmarque os programas e depois clique em Salvar vínculos. Assim, uma pessoa já cadastrada pode receber novos programas.")
            c1, c2, c3, c4 = st.columns(4)
            programas_editados = []
            for coluna, programa in zip([c1, c2, c3, c4], modulos_aux):
                marcado = coluna.checkbox(
                    programa,
                    value=programa in programas_vinculados,
                    key=f"vinculo_edit_{responsavel_id_escolhido}_{programa}"
                )
                if marcado:
                    programas_editados.append(programa)

            col_salvar_vinculos, col_excluir_resp = st.columns([1, 1])
            with col_salvar_vinculos:
                salvar_vinculos = st.button(
                    "Salvar vínculos",
                    type="primary",
                    key=f"salvar_vinculos_{responsavel_id_escolhido}",
                    use_container_width=True
                )
            with col_excluir_resp:
                excluir_responsavel = st.button(
                    "Excluir responsável selecionado",
                    key=f"excluir_responsavel_{responsavel_id_escolhido}",
                    use_container_width=True
                )

            if salvar_vinculos:
                try:
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE responsavel_programas SET ativo=FALSE WHERE responsavel_id=%s",
                        (responsavel_id_escolhido,)
                    )
                    esfera_atual = df_responsaveis.loc[
                        df_responsaveis["id"] == responsavel_id_escolhido, "nivel"
                    ].iloc[0]
                    for programa in programas_editados:
                        cur.execute(
                            """
                            INSERT INTO responsavel_programas
                                (responsavel_id, programa, esfera, ativo)
                            VALUES (%s, %s, %s, TRUE)
                            ON CONFLICT (responsavel_id, programa)
                            DO UPDATE SET esfera=EXCLUDED.esfera, ativo=TRUE
                            """,
                            (responsavel_id_escolhido, programa, esfera_atual)
                        )
                    conn.commit()
                    cur.close()
                    st.success("Vínculos atualizados com sucesso.")
                    st.rerun()
                except Exception as e:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    st.error(f"Não foi possível atualizar os vínculos: {e}")

            if excluir_responsavel:
                try:
                    cur = conn.cursor()
                    cur.execute("DELETE FROM responsavel_programas WHERE responsavel_id=%s", (responsavel_id_escolhido,))
                    cur.execute("DELETE FROM responsaveis WHERE id=%s", (responsavel_id_escolhido,))
                    conn.commit()
                    cur.close()
                    st.success("Responsável excluído com sucesso.")
                    st.rerun()
                except Exception as e:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    st.error(f"Não foi possível excluir o responsável: {e}")

        st.markdown("---")

        # --------------------------------------------------
        # CADASTRAR NOVO RESPONSÁVEL
        # --------------------------------------------------
        st.subheader("Cadastrar novo responsável")
        st.caption("Informe os dados da pessoa e marque um ou mais programas aos quais ela ficará vinculada.")

        with st.form(key="novo_responsavel_unificado", clear_on_submit=True):
            col_cpf, col_nome = st.columns([1, 2])
            with col_cpf:
                cpf_novo = st.text_input("CPF *", key="novo_resp_cpf_unificado")
            with col_nome:
                nome_novo = st.text_input("Nome completo *", key="novo_resp_nome_unificado")

            esfera_nova = st.selectbox(
                "Esfera *",
                ["Federal", "Estadual", "Núcleo", "Municipal"],
                key="novo_resp_esfera_unificado"
            )

            st.markdown("**Programas aos quais o responsável será vinculado:**")
            p1, p2, p3, p4 = st.columns(4)
            with p1:
                prog_sisloc = st.checkbox("SISLOC", key="novo_resp_prog_sisloc")
            with p2:
                prog_pcdch = st.checkbox("PCDCh", key="novo_resp_prog_pcdch")
            with p3:
                prog_pce = st.checkbox("PCE", key="novo_resp_prog_pce")
            with p4:
                prog_pcl = st.checkbox("PCL", key="novo_resp_prog_pcl")

            st.caption('Senha inicial automática: **123456**. No primeiro acesso, o responsável será orientado a criar uma nova senha.')
            salvar_novo_resp = st.form_submit_button("Cadastrar responsável", type="primary")

            if salvar_novo_resp:
                cpf_limpo = so_numeros(cpf_novo)
                programas_escolhidos = [
                    programa for programa, marcado in [
                        ("SISLOC", prog_sisloc),
                        ("PCDCh", prog_pcdch),
                        ("PCE", prog_pce),
                        ("PCL", prog_pcl),
                    ] if marcado
                ]

                if not nome_novo.strip():
                    st.warning("Informe o nome completo.")
                elif len(cpf_limpo) != 11:
                    st.warning("Informe um CPF com 11 números.")
                elif not programas_escolhidos:
                    st.warning("Selecione pelo menos um programa.")
                else:
                    try:
                        cur = conn.cursor()
                        cur.execute(
                            "SELECT id FROM responsaveis WHERE regexp_replace(cpf, '[^0-9]', '', 'g')=%s LIMIT 1",
                            (cpf_limpo,)
                        )
                        existente = cur.fetchone()

                        if existente:
                            cur.close()
                            st.warning("Já existe uma pessoa cadastrada com este CPF. Selecione-a acima para consultar seus programas vinculados.")
                        else:
                            cur.execute(
                                """
                                INSERT INTO responsaveis
                                    (cpf, nome, nivel, estado_id, ativo, senha_hash, deve_trocar_senha)
                                VALUES (%s, %s, %s, NULL, TRUE, %s, TRUE)
                                RETURNING id
                                """,
                                (
                                    cpf_limpo,
                                    nome_novo.strip(),
                                    esfera_nova,
                                    hash_senha("123456", cpf_limpo),
                                )
                            )
                            novo_id = int(cur.fetchone()[0])

                            for programa in programas_escolhidos:
                                cur.execute(
                                    """
                                    INSERT INTO responsavel_programas
                                        (responsavel_id, programa, esfera, ativo)
                                    VALUES (%s, %s, %s, TRUE)
                                    ON CONFLICT (responsavel_id, programa)
                                    DO UPDATE SET esfera=EXCLUDED.esfera, ativo=TRUE
                                    """,
                                    (novo_id, programa, esfera_nova)
                                )

                            conn.commit()
                            cur.close()
                            st.success(
                                f"{nome_novo.strip()} foi cadastrado(a) com sucesso. "
                                f"Senha inicial: 123456. Programas vinculados: {', '.join(programas_escolhidos)}."
                            )
                            st.rerun()

                    except Exception as e:
                        try:
                            conn.rollback()
                        except Exception:
                            pass
                        st.error(f"Não foi possível cadastrar o responsável: {e}")

    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        st.error(f"Erro ao gerenciar responsáveis: {e}")

    conn.close()

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

elif st.session_state.pagina == "TrocarSenha":
    st.subheader("Trocar minha senha")
    atual = st.text_input("Senha atual", type="password")
    n1 = st.text_input("Nova senha", type="password", key="ts1")
    n2 = st.text_input("Confirmar", type="password", key="ts2")
    if st.button("Salvar", type="primary"):
        if hash_senha(atual, usuario["cpf"]) != (usuario.get("senha_hash") or "").lower():
            st.error("Senha atual incorreta.")
        else:
            ok, msg = senha_valida(n1)
            if not ok: st.warning(msg)
            elif n1 != n2: st.warning("Senhas não conferem.")
            else:
                conn = conectar_banco()
                if conn:
                    cur = conn.cursor()
                    cur.execute("UPDATE responsaveis SET senha_hash=%s, deve_trocar_senha=FALSE WHERE id=%s",
                                (hash_senha(n1, usuario["cpf"]), int(usuario["id"])))
                    conn.commit(); cur.close(); conn.close(); st.success("Senha alterada!")

elif st.session_state.pagina == "Responsaveis":
    st.markdown('<div class="module-header"><h1>Responsáveis</h1></div>', unsafe_allow_html=True)
    conn = conectar_banco()
    if conn:
        try:
            df = pd.read_sql("""
                SELECT r.id, r.cpf, r.nome, r.nivel, e.nome as estado, r.ativo
                FROM responsaveis r LEFT JOIN estados e ON e.id = r.estado_id ORDER BY r.nivel, r.nome
            """, conn)
            if not df.empty:
                df["cpf"] = df["cpf"].apply(formatar_cpf)
                st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Erro: {e}")
        conn.close()

elif st.session_state.pagina == "Contato":
    contato_aba = st.session_state.get("contato_aba", "Inicio")

    # A imagem é apenas a apresentação inicial do módulo.
    # Ao selecionar uma esfera na lateral, ela desaparece e fica somente o conteúdo escolhido.
    if contato_aba == "Inicio":
        imagem_contato = localizar_imagem_modulo("contato", "contato")
        if imagem_contato:
            st.image(imagem_contato, use_container_width=True)

    st.markdown(
        '<div class="module-header">'
        '<h1>📇 Contato</h1>'
        '<p>Contatos institucionais por esfera de atuação</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.get("contato_aba", "Inicio") == "Inicio":
        st.info("Selecione uma opção no menu lateral para consultar os contatos da esfera Federal, Estadual, dos Núcleos ou Municipal.")

    conn = conectar_banco()

    if not conn:
        st.stop()

    # ======================================================
    # FEDERAL
    # ======================================================
    if contato_aba == "Federal":

        st.subheader("Esfera Federal")

        nac = carregar_nacional(conn)

        dados_federal = [
            {
                "Cargo": "Presidente da República",
                "Nome": nac["presidente"] if nac["presidente"] != "—" else "Não informado",
                "E-mail": "Não informado"
            },
            {
                "Cargo": "Ministro da Saúde",
                "Nome": nac["ministro_saude"] if nac["ministro_saude"] != "—" else "Não informado",
                "E-mail": "Não informado"
            }
        ]

        st.dataframe(
            pd.DataFrame(dados_federal),
            use_container_width=True,
            hide_index=True
        )

    # ======================================================
    # ESTADUAL
    # ======================================================
    elif contato_aba == "Estadual":

        st.subheader("Esfera Estadual")

        df_estados = carregar_estados_todos(conn)

        if not df_estados.empty:

            estado_contato = st.selectbox(
                "Selecione o Estado",
                df_estados["nome"].tolist(),
                key="contato_estado"
            )

            estado_id_contato = int(
                df_estados[
                    df_estados["nome"] == estado_contato
                ].iloc[0]["id"]
            )

            info_estado = carregar_estado_info(
                conn,
                estado_id_contato
            )

            dados_estadual = [
                {
                    "Cargo": "Governador",
                    "Nome": info_estado["governador"]
                    if info_estado and info_estado["governador"] != "—"
                    else "Não informado",
                    "E-mail": "Não informado"
                },
                {
                    "Cargo": "Secretário Estadual de Saúde",
                    "Nome": info_estado["secretario_saude"]
                    if info_estado and info_estado["secretario_saude"] != "—"
                    else "Não informado",
                    "E-mail": "Não informado"
                },
                {
                    "Cargo": "Coordenador do SISLOC",
                    "Nome": "Não informado",
                    "E-mail": "Não informado"
                },
                {
                    "Cargo": "Coordenador do PCDCh",
                    "Nome": "Não informado",
                    "E-mail": "Não informado"
                },
                {
                    "Cargo": "Coordenador do PCE",
                    "Nome": "Não informado",
                    "E-mail": "Não informado"
                },
                {
                    "Cargo": "Coordenador do PCL",
                    "Nome": "Não informado",
                    "E-mail": "Não informado"
                }
            ]

            st.dataframe(
                pd.DataFrame(dados_estadual),
                use_container_width=True,
                hide_index=True
            )

    # ======================================================
    # NÚCLEOS
    # ======================================================
    elif contato_aba == "Núcleos":

        st.subheader("Núcleos de Saúde")

        df_estados = carregar_estados_todos(conn)

        if not df_estados.empty:

            estado_nucleo = st.selectbox(
                "Estado",
                df_estados["nome"].tolist(),
                key="contato_nucleo_estado"
            )

            estado_id_nucleo = int(
                df_estados[
                    df_estados["nome"] == estado_nucleo
                ].iloc[0]["id"]
            )

            try:

                df_nucleos_contato = pd.read_sql(
                    """
                    SELECT id, nome
                    FROM regionais_saude
                    WHERE estado_id=%s
                    AND (parent_id IS NULL OR parent_id=0)
                    ORDER BY nome
                    """,
                    conn,
                    params=(estado_id_nucleo,)
                )

            except Exception:

                df_nucleos_contato = pd.DataFrame()

            if not df_nucleos_contato.empty:

                nucleo_contato = st.selectbox(
                    "Núcleo",
                    df_nucleos_contato["nome"].tolist(),
                    key="contato_nucleo"
                )

                dados_nucleo = [
                    {
                        "Cargo": "Coordenador de Saúde",
                        "Nome": "Não informado",
                        "E-mail": "Não informado"
                    },
                    {
                        "Cargo": "Coordenador Administrativo",
                        "Nome": "Não informado",
                        "E-mail": "Não informado"
                    },
                    {
                        "Cargo": "Coordenador do SISLOC",
                        "Nome": "Não informado",
                        "E-mail": "Não informado"
                    },
                    {
                        "Cargo": "Coordenador do PCDCh",
                        "Nome": "Não informado",
                        "E-mail": "Não informado"
                    },
                    {
                        "Cargo": "Coordenador do PCE",
                        "Nome": "Não informado",
                        "E-mail": "Não informado"
                    },
                    {
                        "Cargo": "Coordenador do PCL",
                        "Nome": "Não informado",
                        "E-mail": "Não informado"
                    }
                ]

                st.dataframe(
                    pd.DataFrame(dados_nucleo),
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.info("Nenhum núcleo encontrado para este estado.")

    # ======================================================
    # MUNICIPAL
    # ======================================================
    elif contato_aba == "Municipal":

        st.subheader("Esfera Municipal")

        df_estados = carregar_estados_todos(conn)

        if not df_estados.empty:

            estado_municipal = st.selectbox(
                "Estado",
                df_estados["nome"].tolist(),
                key="contato_municipal_estado"
            )

            estado_id_municipal = int(
                df_estados[
                    df_estados["nome"] == estado_municipal
                ].iloc[0]["id"]
            )

            df_municipios_contato = pd.read_sql(
                """
                SELECT m.id, m.nome
                FROM municipios m
                LEFT JOIN regionais_saude r
                    ON r.id = m.regional_id
                WHERE r.estado_id=%s
                ORDER BY m.nome
                """,
                conn,
                params=(estado_id_municipal,)
            )

            if not df_municipios_contato.empty:

                municipio_contato = st.selectbox(
                    "Município",
                    df_municipios_contato["nome"].tolist(),
                    key="contato_municipio"
                )

                municipio_id_contato = int(
                    df_municipios_contato[
                        df_municipios_contato["nome"] == municipio_contato
                    ].iloc[0]["id"]
                )

                info_municipio = carregar_municipio_info(
                    conn,
                    municipio_id_contato
                )

                dados_municipal = [
                    {
                        "Cargo": "Prefeito",
                        "Nome": info_municipio["prefeito"]
                        if info_municipio and info_municipio["prefeito"] != "—"
                        else "Não informado",
                        "E-mail": "Não informado"
                    },
                    {
                        "Cargo": "Secretário Municipal de Saúde",
                        "Nome": info_municipio["secretario_saude"]
                        if info_municipio and info_municipio["secretario_saude"] != "—"
                        else "Não informado",
                        "E-mail": "Não informado"
                    },
                    {
                        "Cargo": "Digitador",
                        "Nome": "Não informado",
                        "E-mail": "Não informado"
                    },
                    {
                        "Cargo": "Coordenador do SISLOC",
                        "Nome": "Não informado",
                        "E-mail": "Não informado"
                    },
                    {
                        "Cargo": "Coordenador do PCDCh",
                        "Nome": "Não informado",
                        "E-mail": "Não informado"
                    },
                    {
                        "Cargo": "Coordenador do PCE",
                        "Nome": "Não informado",
                        "E-mail": "Não informado"
                    },
                    {
                        "Cargo": "Coordenador do PCL",
                        "Nome": "Não informado",
                        "E-mail": "Não informado"
                    }
                ]

                st.dataframe(
                    pd.DataFrame(dados_municipal),
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.info("Nenhum município encontrado para este estado.")

    conn.close()

elif st.session_state.pagina == "Sisloc":
    imagem_sisloc = localizar_imagem_modulo("sisloc")
    if st.session_state.get("modulo_inicio", False) and imagem_sisloc:
        st.image(imagem_sisloc, use_container_width=True)
        st.markdown("---")
    st.markdown('<div class="module-header"><h1>Sisloc</h1><p>Reconhecimento Geográfico</p></div>', unsafe_allow_html=True)
    menu_sisloc = st.session_state.get("menu_sisloc", "Navegação Hierárquica")
    conn = conectar_banco()
    if not conn: st.stop()
    df_estados_view = carregar_estados_todos(conn)
    df_estados_cad = carregar_estados_cadastro(conn, usuario)

    if menu_sisloc == "Navegação Hierárquica":
        st.subheader("Navegação Hierárquica")
        try:
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                estado_sel = st.selectbox("Estado", ["Selecione..."] + df_estados_view["nome"].tolist(), key="nav_estado")
            estado_id = None; df_nucleos = pd.DataFrame(); df_regionais = pd.DataFrame(); df_mun = pd.DataFrame(); nucleo_id = None
            if estado_sel != "Selecione...":
                estado_id = int(df_estados_view[df_estados_view["nome"] == estado_sel].iloc[0]["id"])
                info_est = carregar_estado_info(conn, estado_id)
                if info_est:
                    st.markdown(f'<div class="auth-box"><b>Estado:</b> {info_est["nome"]} ({info_est["sigla"]})<br><b>Governador:</b> {info_est["governador"]}<br><b>Secretário(a):</b> {info_est["secretario_saude"]}</div>', unsafe_allow_html=True)
                try:
                    df_nucleos = pd.read_sql("SELECT id, nome FROM regionais_saude WHERE estado_id=%s AND (parent_id IS NULL OR parent_id=0) ORDER BY nome", conn, params=(estado_id,))
                except Exception:
                    df_nucleos = pd.read_sql("SELECT id, nome FROM regionais_saude WHERE estado_id=%s ORDER BY nome", conn, params=(estado_id,))
            with c2:
                lista_n = (["Selecione..."] + df_nucleos["nome"].tolist()) if estado_id and not df_nucleos.empty else ["Selecione o estado primeiro"]
                nucleo_sel = st.selectbox("Núcleo", lista_n, key="nav_nucleo")
            if estado_id and nucleo_sel not in ["Selecione...", "Selecione o estado primeiro"]:
                nucleo_id = int(df_nucleos[df_nucleos["nome"] == nucleo_sel].iloc[0]["id"])
                try:
                    df_regionais = pd.read_sql("SELECT id, nome FROM regionais_saude WHERE parent_id=%s ORDER BY nome", conn, params=(nucleo_id,))
                except Exception:
                    df_regionais = pd.DataFrame()
            with c3:
                lista_r = (["Todos do núcleo"] + df_regionais["nome"].tolist()) if nucleo_id and not df_regionais.empty else (["Todos do núcleo"] if nucleo_id else ["Selecione o núcleo"])
                reg_sel = st.selectbox("Regional", lista_r, key="nav_regional")
            if nucleo_id is not None:
                if reg_sel not in ["Todos do núcleo", "Selecione o núcleo"] and not df_regionais.empty:
                    reg_id = int(df_regionais[df_regionais["nome"] == reg_sel].iloc[0]["id"])
                    df_mun = pd.read_sql("SELECT id, nome, codigo_ibge, status FROM municipios WHERE regional_id=%s ORDER BY nome", conn, params=(reg_id,))
                elif not df_regionais.empty:
                    ids = [nucleo_id] + df_regionais["id"].tolist()
                    ph = ",".join(["%s"] * len(ids))
                    df_mun = pd.read_sql(f"SELECT id, nome, codigo_ibge, status FROM municipios WHERE regional_id IN ({ph}) ORDER BY nome", conn, params=tuple(ids))
                else:
                    df_mun = pd.read_sql("SELECT id, nome, codigo_ibge, status FROM municipios WHERE regional_id=%s ORDER BY nome", conn, params=(nucleo_id,))
            elif estado_id is not None:
                df_mun = pd.read_sql("SELECT m.id, m.nome, m.codigo_ibge, m.status FROM municipios m LEFT JOIN regionais_saude r ON r.id = m.regional_id WHERE r.estado_id=%s ORDER BY m.nome", conn, params=(estado_id,))
            with c4:
                lista_m = (["Selecione..."] + df_mun["nome"].tolist()) if not df_mun.empty else ["Sem municípios"]
                mun_sel = st.selectbox("Município", lista_m, key="nav_mun")
            if mun_sel not in ["Selecione...", "Sem municípios"] and not df_mun.empty:
                mid = int(df_mun[df_mun["nome"] == mun_sel].iloc[0]["id"])
                st.markdown(f"### Localidades de **{mun_sel}**")
                df_loc = pd.read_sql("SELECT id, nome, tipo, status FROM localidades WHERE municipio_id=%s ORDER BY nome", conn, params=(mid,))
                if not df_loc.empty:
                    df_loc = df_loc.copy()
                    df_loc.insert(0, "Nº", range(1, len(df_loc) + 1))
                    st.caption(f"{len(df_loc)} localidades encontradas — sequência esperada: 1 a {len(df_loc)}")
                st.dataframe(df_loc if not df_loc.empty else pd.DataFrame(), use_container_width=True, hide_index=True)
            elif estado_sel != "Selecione..." and not df_mun.empty:
                df_mun = df_mun.copy()
                df_mun.insert(0, "Nº", range(1, len(df_mun) + 1))
                st.caption(f"{len(df_mun)} municípios encontrados — sequência esperada: 1 a {len(df_mun)}")
                st.dataframe(df_mun, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Erro: {e}")

    elif menu_sisloc == "Localidades":
        st.subheader("Localidades")
        try:
            est_f = st.selectbox("Estado", ["Todos"] + df_estados_view["nome"].tolist(), key="loc_est")
            sql = "SELECT l.id, e.nome as estado, m.nome as municipio, l.nome as localidade, l.tipo, l.status FROM localidades l LEFT JOIN municipios m ON m.id = l.municipio_id LEFT JOIN regionais_saude r ON r.id = m.regional_id LEFT JOIN estados e ON e.id = r.estado_id WHERE 1=1"
            params = []
            if est_f != "Todos":
                sql += " AND e.nome = %s"; params.append(est_f)
            sql += " ORDER BY e.nome, m.nome, l.nome LIMIT 5000"
            df = pd.read_sql(sql, conn, params=tuple(params) if params else None)
            if not df.empty:
                df = df.copy()
                df.insert(0, "Nº", range(1, len(df) + 1))
                st.caption(f"{len(df)} localidades encontradas — sequência esperada: 1 a {len(df)}")
            st.dataframe(df if not df.empty else pd.DataFrame(), use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Erro: {e}")

    elif menu_sisloc == "Cadastrar Localidade":
        st.subheader("Cadastrar Nova Localidade")
        try:
            if nivel == "Federal":
                estado_sel = st.selectbox("Estado", ["Selecione o estado..."] + df_estados_cad["nome"].tolist(), key="cad_est")
            else:
                estado_sel = df_estados_cad.iloc[0]["nome"]
                st.selectbox("Estado", [estado_sel], disabled=True, key="cad_est")
            df_mun = pd.DataFrame()
            if estado_sel != "Selecione o estado...":
                eid = int(df_estados_cad[df_estados_cad["nome"] == estado_sel].iloc[0]["id"])
                df_mun = municipios_para_cadastro(conn, usuario, False, estado_id=eid)
            mun_sel = st.selectbox("Município", ["Selecione..."] + df_mun["nome"].tolist() if not df_mun.empty else ["Selecione o estado"], key="cad_mun")
            nome = st.text_input("Nome da Localidade", key="cad_nome_loc")
            tipo = st.selectbox("Tipo", ["Bairro", "Povoado", "Vila", "Distrito", "Outro"], key="cad_tipo_loc")
            if st.button("Salvar Localidade", type="primary", key="cad_btn_loc"):
                if estado_sel == "Selecione o estado..." or mun_sel in ["Selecione...", "Selecione o estado"] or not nome.strip():
                    st.warning("Preencha os campos.")
                else:
                    mid = int(df_mun[df_mun["nome"] == mun_sel].iloc[0]["id"])
                    if not municipio_esta_no_escopo(conn, usuario, mid):
                        st.error("Município fora do escopo de cadastro do usuário.")
                        st.stop()
                    cur = conn.cursor()
                    cur.execute("INSERT INTO localidades (municipio_id, nome, tipo, status) VALUES (%s,%s,%s,'Ativa')", (mid, nome.strip(), tipo))
                    conn.commit(); cur.close(); st.success("Localidade salva!")
        except Exception as e:
            st.error(f"Erro: {e}")

    elif menu_sisloc == "Editar / Arquivar Localidade":
        st.subheader("Editar / Arquivar Localidade")
        try:
            if nivel == "Federal":
                est_e = st.selectbox("Estado", ["Selecione..."] + df_estados_cad["nome"].tolist(), key="edloc_est")
            else:
                est_e = df_estados_cad.iloc[0]["nome"] if not df_estados_cad.empty else None
                st.selectbox("Estado", [est_e], disabled=True, key="edloc_est")
            eid_e = int(df_estados_cad[df_estados_cad["nome"] == est_e].iloc[0]["id"]) if est_e and est_e != "Selecione..." and not df_estados_cad.empty else None
            df_mun_e = municipios_para_cadastro(conn, usuario, True, estado_id=eid_e) if eid_e is not None else pd.DataFrame()
            mun_e = st.selectbox("Município", ["Selecione..."] + df_mun_e["nome"].tolist() if not df_mun_e.empty else ["Selecione o estado"], key="edloc_mun")
            if mun_e not in ["Selecione...", "Selecione o estado"]:
                mid = int(df_mun_e[df_mun_e["nome"] == mun_e].iloc[0]["id"])
                df_loc_e = pd.read_sql("SELECT id, nome, tipo, status FROM localidades WHERE municipio_id=%s ORDER BY nome", conn, params=(mid,))
                if not df_loc_e.empty:
                    loc_e = st.selectbox("Localidade", [f"{r['nome']}  [{r['status']}]" for _, r in df_loc_e.iterrows()], key="edloc_loc")
                    nome_puro = loc_e.split("  [")[0]
                    row = df_loc_e[df_loc_e["nome"] == nome_puro].iloc[0]
                    lid = int(row["id"])
                    novo_nome = st.text_input("Nome", value=str(row["nome"]), key="edloc_nome")
                    tipos = ["Bairro", "Povoado", "Vila", "Distrito", "Outro"]
                    tipo_atual = str(row["tipo"]) if row["tipo"] in tipos else "Outro"
                    novo_tipo = st.selectbox("Tipo", tipos, index=tipos.index(tipo_atual), key="edloc_tipo")
                    status_atual = str(row["status"]) if row["status"] in ("Ativa", "Arquivada") else "Ativa"
                    novo_status = st.selectbox("Status", ["Ativa", "Arquivada"], index=0 if status_atual == "Ativa" else 1, key="edloc_status")
                    if st.button("Salvar", type="primary", key="edloc_salvar"):
                        cur = conn.cursor()
                        cur.execute("UPDATE localidades SET nome=%s, tipo=%s, status=%s WHERE id=%s", (novo_nome.strip(), novo_tipo, novo_status, lid))
                        conn.commit(); cur.close(); st.success("Atualizado!"); st.rerun()
        except Exception as e:
            st.error(f"Erro: {e}")

    elif menu_sisloc == "Editar / Arquivar Município":
        st.subheader("Editar / Arquivar Município")
        try:
            if nivel == "Federal":
                est_m = st.selectbox("Estado", ["Selecione..."] + df_estados_cad["nome"].tolist(), key="edmun_est")
            else:
                est_m = df_estados_cad.iloc[0]["nome"] if not df_estados_cad.empty else None
                st.selectbox("Estado", [est_m], disabled=True, key="edmun_est")
            eid_m = int(df_estados_cad[df_estados_cad["nome"] == est_m].iloc[0]["id"]) if est_m and est_m != "Selecione..." and not df_estados_cad.empty else None
            df_mun_m = municipios_para_cadastro(conn, usuario, True, estado_id=eid_m) if eid_m is not None else pd.DataFrame()
            if not df_mun_m.empty:
                mun_m = st.selectbox("Município", [f"{r['nome']}  [{r['status'] or 'Ativo'}]" for _, r in df_mun_m.iterrows()], key="edmun_mun")
                nome_puro = mun_m.split("  [")[0]
                row = df_mun_m[df_mun_m["nome"] == nome_puro].iloc[0]
                mid = int(row["id"])
                status_atual = str(row["status"]) if row["status"] in ("Ativo", "Arquivado") else "Ativo"
                novo_status = st.selectbox("Status", ["Ativo", "Arquivado"], index=0 if status_atual == "Ativo" else 1, key="edmun_status")
                if st.button("Salvar status", type="primary", key="edmun_salvar"):
                    cur = conn.cursor()
                    cur.execute("UPDATE municipios SET status=%s WHERE id=%s", (novo_status, mid))
                    conn.commit(); cur.close(); st.success("Atualizado!"); st.rerun()
        except Exception as e:
            st.error(f"Erro: {e}")

    elif menu_sisloc == "Imóveis":
        st.subheader("Imóveis")
        tab1, tab2 = st.tabs(["Listar", "Cadastrar"])
        with tab1:
            try:
                df = pd.read_sql("""
                    SELECT i.id, e.nome as estado, m.nome as municipio, l.nome as localidade,
                           i.identificacao, i.quarteirao, i.lado, i.sequencia, i.numero,
                           i.tipo, i.tipo_construcao, i.situacao, i.ativo
                    FROM imoveis i
                    LEFT JOIN localidades l ON l.id = i.localidade_id
                    LEFT JOIN municipios m ON m.id = l.municipio_id
                    LEFT JOIN regionais_saude r ON r.id = m.regional_id
                    LEFT JOIN estados e ON e.id = r.estado_id
                    ORDER BY e.nome, m.nome, i.quarteirao, i.sequencia LIMIT 3000
                """, conn)
                if df.empty:
                    st.info("Nenhum imóvel cadastrado ainda.")
                else:
                    df = df.copy()
                    df.insert(0, "Nº", range(1, len(df) + 1))
                    st.caption(f"{len(df)} imóveis encontrados — sequência esperada: 1 a {len(df)}")
                    st.dataframe(df, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"Erro: {e}")
        with tab2:
            try:
                if nivel == "Federal":
                    estado_sel = st.selectbox("Estado", ["Selecione o estado..."] + df_estados_cad["nome"].tolist(), key="imv_cad_est")
                else:
                    estado_sel = df_estados_cad.iloc[0]["nome"]
                    st.selectbox("Estado", [estado_sel], disabled=True, key="imv_cad_est")
                eid_imv = int(df_estados_cad[df_estados_cad["nome"] == estado_sel].iloc[0]["id"]) if estado_sel != "Selecione o estado..." and not df_estados_cad.empty else None
                df_mun = municipios_para_cadastro(conn, usuario, False, estado_id=eid_imv) if eid_imv is not None else pd.DataFrame()
                mun_sel = st.selectbox("Município", ["Selecione..."] + df_mun["nome"].tolist() if not df_mun.empty else ["Selecione o estado"], key="imv_cad_mun")
                df_loc = pd.DataFrame()
                if mun_sel not in ["Selecione...", "Selecione o estado"]:
                    mid = int(df_mun[df_mun["nome"] == mun_sel].iloc[0]["id"])
                    df_loc = pd.read_sql("SELECT id, nome FROM localidades WHERE municipio_id=%s AND (status IS NULL OR status='Ativa') ORDER BY nome", conn, params=(mid,))
                loc_sel = st.selectbox("Localidade", ["Selecione..."] + df_loc["nome"].tolist() if not df_loc.empty else ["Selecione o município"], key="imv_cad_loc")
                campos = form_campos_imovel("sis_imv")
                if st.button("Salvar Imóvel", type="primary", key="imv_cad_btn"):
                    if loc_sel in ["Selecione...", "Selecione o município"] or not campos["identificacao"]:
                        st.warning("Preencha localidade e identificação.")
                    else:
                        lid = int(df_loc[df_loc["nome"] == loc_sel].iloc[0]["id"])
                        mid_check = int(df_mun[df_mun["nome"] == mun_sel].iloc[0]["id"])
                        if not municipio_esta_no_escopo(conn, usuario, mid_check):
                            st.error("Município fora do escopo de cadastro do usuário.")
                            st.stop()
                        cur = conn.cursor()
                        cur.execute("""
                            INSERT INTO imoveis
                            (localidade_id, identificacao, quarteirao, lado, sequencia, numero, complemento,
                             tipo, tipo_construcao, situacao, observacao, ativo, data_cadastro)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,TRUE,CURRENT_DATE)
                        """, (lid, campos["identificacao"], campos["quarteirao"], campos["lado"], campos["sequencia"],
                              campos["numero"], campos["complemento"], campos["tipo"], campos["tipo_construcao"],
                              campos["situacao"], campos["observacao"]))
                        conn.commit(); cur.close(); st.success("Imóvel salvo!")
            except Exception as e:
                st.error(f"Erro: {e}")

    elif menu_sisloc == "Editar / Excluir Imóvel":
        st.subheader("Editar / Excluir Imóvel")
        try:
            if nivel == "Federal":
                est_i = st.selectbox("Estado", ["Selecione..."] + df_estados_cad["nome"].tolist(), key="edim_est")
            else:
                est_i = df_estados_cad.iloc[0]["nome"] if not df_estados_cad.empty else None
                st.selectbox("Estado", [est_i], disabled=True, key="edim_est")
            eid_i = int(df_estados_cad[df_estados_cad["nome"] == est_i].iloc[0]["id"]) if est_i and est_i != "Selecione..." and not df_estados_cad.empty else None
            df_mun_i = municipios_para_cadastro(conn, usuario, True, estado_id=eid_i) if eid_i is not None else pd.DataFrame()
            mun_i = st.selectbox("Município", ["Selecione..."] + df_mun_i["nome"].tolist() if not df_mun_i.empty else ["Selecione o estado"], key="edim_mun")
            df_loc_i = pd.DataFrame()
            if mun_i not in ["Selecione...", "Selecione o município"]:
                mid = int(df_mun_i[df_mun_i["nome"] == mun_i].iloc[0]["id"])
                df_loc_i = pd.read_sql("SELECT id, nome FROM localidades WHERE municipio_id=%s ORDER BY nome", conn, params=(mid,))
            loc_i = st.selectbox("Localidade", ["Selecione..."] + df_loc_i["nome"].tolist() if not df_loc_i.empty else ["Selecione o município"], key="edim_loc")
            if loc_i not in ["Selecione...", "Selecione o município"]:
                lid = int(df_loc_i[df_loc_i["nome"] == loc_i].iloc[0]["id"])
                df_imv = pd.read_sql("""
                    SELECT id, identificacao, quarteirao, lado, sequencia, numero, complemento,
                           tipo, tipo_construcao, situacao, observacao
                    FROM imoveis WHERE localidade_id=%s ORDER BY quarteirao, sequencia, id
                """, conn, params=(lid,))
                if df_imv.empty:
                    st.info("Nenhum imóvel nesta localidade.")
                else:
                    opcoes = [f"#{int(r['id'])} — Q{r['quarteirao'] or '-'} Seq{r['sequencia'] or '-'} | {r['identificacao'] or '(sem id.)'}" for _, r in df_imv.iterrows()]
                    escolhido = st.selectbox("Imóvel", opcoes, key="edim_sel")
                    iid = int(escolhido.split("—")[0].replace("#", "").strip())
                    row = df_imv[df_imv["id"] == iid].iloc[0]
                    campos = form_campos_imovel("ed_imv", row.to_dict())
                    if st.button("Salvar alterações", type="primary", key="edim_salvar"):
                        if not campos["identificacao"]:
                            st.warning("Identificação obrigatória.")
                        else:
                            cur = conn.cursor()
                            cur.execute("""
                                UPDATE imoveis SET
                                    identificacao=%s, quarteirao=%s, lado=%s, sequencia=%s, numero=%s,
                                    complemento=%s, tipo=%s, tipo_construcao=%s, situacao=%s, observacao=%s
                                WHERE id=%s
                            """, (campos["identificacao"], campos["quarteirao"], campos["lado"], campos["sequencia"],
                                  campos["numero"], campos["complemento"], campos["tipo"], campos["tipo_construcao"],
                                  campos["situacao"], campos["observacao"], iid))
                            conn.commit(); cur.close(); st.success("Imóvel atualizado!"); st.rerun()
                    st.markdown("---")
                    confirmar = st.checkbox("Confirmo exclusão definitiva deste imóvel", key="edim_conf")
                    if MODO_SIMULACAO:
                        st.button("Excluir imóvel", disabled=True, key="edim_excluir",
                                  help="A exclusão definitiva está bloqueada no ambiente de simulação.")
                        if confirmar:
                            st.warning("A exclusão definitiva está bloqueada no ambiente de simulação.")
                    elif st.button("Excluir imóvel", disabled=not confirmar, key="edim_excluir"):
                        cur = conn.cursor()
                        cur.execute("DELETE FROM imoveis WHERE id=%s", (iid,))
                        conn.commit(); cur.close(); st.success("Excluído."); st.rerun()
        except Exception as e:
            st.error(f"Erro: {e}")
    conn.close()

elif st.session_state.pagina == "PCDCh":
    imagem_pcdch = localizar_imagem_modulo("pcdch", "chagas")
    if st.session_state.get("modulo_inicio", False) and imagem_pcdch:
        st.image(imagem_pcdch, use_container_width=True)
        st.markdown("---")
    st.markdown('<div class="module-header"><h1>PCDCh</h1><p>Pesquisas, Capturas e Diário</p></div>', unsafe_allow_html=True)
    menu = st.session_state.get("pcdch_menu", "Cadastro")
    conn = conectar_banco()
    if not conn: st.stop()

    # PCE-102A: a tabela é garantida na conexão do próprio módulo PCE.
    # Nenhum outro módulo depende desta rotina.
    try:
        garantir_tabela_colecoes_hidricas(conn)
    except Exception as e:
        st.error(f"Erro ao preparar o PCE-102A — Coleção Hídrica: {e}")
        conn.close()
        st.stop()

    df_estados_cad = carregar_estados_cadastro(conn, usuario)

    def seletor_estado_cadastro(key):
        if nivel == "Federal":
            return st.selectbox("Estado", ["Selecione..."] + df_estados_cad["nome"].tolist(), key=key)
        nome = df_estados_cad.iloc[0]["nome"] if not df_estados_cad.empty else "—"
        st.selectbox("Estado", [nome], key=key, disabled=True)
        return nome

    def estado_id_de_nome(nome, df_ref):
        if not nome or nome == "Selecione...": return None
        row = df_ref[df_ref["nome"] == nome]
        return int(row.iloc[0]["id"]) if not row.empty else None

    def seletor_hierarquia_programacao(conn, usuario, df_estados_cad, prefixo):
        """Seleção territorial da Programação: Estado → Núcleo/estrutura superior → Regional/estrutura filha → Município.

        A hierarquia é carregada da tabela regionais_saude. Para a Bahia, por exemplo,
        o primeiro nível corresponde aos NRS e o segundo às Regionais de Saúde.
        Em estados cuja base possua outra organização, os rótulos se adaptam.
        O município final é sempre limitado ao escopo de cadastro do usuário.
        """
        df_scope = municipios_para_cadastro(conn, usuario, False)
        if df_scope.empty:
            st.warning("Nenhum município disponível para o seu escopo de cadastro.")
            return None, None, None, None

        # Estado
        if nivel_usuario(usuario) == "Federal":
            op_est = ["Selecione..."] + df_estados_cad["nome"].tolist()
            est = st.selectbox("Estado", op_est, key=f"{prefixo}_estado")
        else:
            est = str(df_estados_cad.iloc[0]["nome"]) if not df_estados_cad.empty else "—"
            st.selectbox("Estado", [est], key=f"{prefixo}_estado", disabled=True)

        if est in ("Selecione...", "—"):
            return None, None, None, None

        row_est = df_estados_cad[df_estados_cad["nome"] == est]
        if row_est.empty:
            return None, None, None, None
        estado_id = int(row_est.iloc[0]["id"])

        # Primeiro nível territorial: normalmente NRS/Núcleo.
        try:
            df_nivel1 = pd.read_sql(
                "SELECT id, nome FROM regionais_saude WHERE estado_id=%s AND (parent_id IS NULL OR parent_id=0) ORDER BY nome",
                conn, params=(estado_id,)
            )
        except Exception:
            df_nivel1 = pd.DataFrame(columns=["id", "nome"])

        # Se não houver estrutura superior, usamos as regionais diretamente.
        estrutura_superior = not df_nivel1.empty
        if estrutura_superior:
            label1 = "Núcleo / estrutura regional correspondente"
        else:
            try:
                df_nivel1 = pd.read_sql(
                    "SELECT id, nome FROM regionais_saude WHERE estado_id=%s ORDER BY nome",
                    conn, params=(estado_id,)
                )
            except Exception:
                df_nivel1 = pd.DataFrame(columns=["id", "nome"])
            label1 = "Regional / estrutura correspondente"

        op1 = ["Selecione..."] + df_nivel1["nome"].tolist() if not df_nivel1.empty else ["Nenhuma estrutura cadastrada"]
        nivel1 = st.selectbox(label1, op1, key=f"{prefixo}_nivel1")
        if nivel1 in ("Selecione...", "Nenhuma estrutura cadastrada"):
            # Enquanto não houver a estrutura superior, mostramos apenas a situação e não liberamos município.
            return estado_id, None, None, None

        nivel1_id = int(df_nivel1[df_nivel1["nome"] == nivel1].iloc[0]["id"])

        # Segundo nível: filhas do primeiro nível, quando existirem.
        try:
            df_nivel2 = pd.read_sql(
                "SELECT id, nome FROM regionais_saude WHERE parent_id=%s ORDER BY nome",
                conn, params=(nivel1_id,)
            ) if estrutura_superior else pd.DataFrame(columns=["id", "nome"])
        except Exception:
            df_nivel2 = pd.DataFrame(columns=["id", "nome"])

        if estrutura_superior and not df_nivel2.empty:
            label2 = "Regional / Região de Saúde"
            op2 = ["Selecione..."] + df_nivel2["nome"].tolist()
            nivel2 = st.selectbox(label2, op2, key=f"{prefixo}_nivel2")
            if nivel2 == "Selecione...":
                return estado_id, nivel1_id, None, None
            regional_id = int(df_nivel2[df_nivel2["nome"] == nivel2].iloc[0]["id"])
            df_mun = df_scope[df_scope["id"].astype(int).isin(
                pd.read_sql("SELECT id FROM municipios WHERE regional_id=%s", conn, params=(regional_id,))["id"].astype(int).tolist()
            )].copy()
        else:
            # Sem nível filho: o primeiro nível já é a unidade regional usada pelos municípios.
            regional_id = nivel1_id
            df_mun = df_scope[df_scope["id"].astype(int).isin(
                pd.read_sql("SELECT id FROM municipios WHERE regional_id=%s", conn, params=(regional_id,))["id"].astype(int).tolist()
            )].copy()

        op_m = ["Selecione..."] + df_mun["nome"].tolist() if not df_mun.empty else ["Nenhum município disponível"]
        mun = st.selectbox("Município", op_m, key=f"{prefixo}_municipio")
        if mun in ("Selecione...", "Nenhum município disponível"):
            return estado_id, nivel1_id, regional_id, None

        mid = int(df_mun[df_mun["nome"] == mun].iloc[0]["id"])
        return estado_id, nivel1_id, regional_id, mid

    if menu == "Programação":
        st.subheader("Programação do PCDCh")
        st.caption("Planejamento anual das atividades e acompanhamento mensal do que foi programado e realizado.")

        if not garantir_tabelas_programacao_pcdch(conn):
            st.stop()

        tab_anual, tab_mensal, tab_acomp = st.tabs([
            "Plano anual",
            "Programação mensal",
            "Acompanhamento"
        ])

        # --------------------------------------------------
        # PLANO ANUAL
        # --------------------------------------------------
        with tab_anual:
            st.markdown("### Plano anual — parâmetros para pesquisa ativa")
            st.info(
                "O plano anual transforma os parâmetros do PCDCh em números de trabalho. "
                "A referência histórica utiliza 20 dias úteis/mês e calcula os dias de pesquisa "
                "depois de descontar PIT, atividades burocráticas e borrifação/imprevistos."
            )

            eid_pa, nucleo_pa, regional_pa, mid_pa = seletor_hierarquia_programacao(
                conn, usuario, df_estados_cad, "prog_an"
            )

            if mid_pa is None:
                st.info("Selecione a hierarquia territorial até chegar ao município para continuar.")
            else:
                mun_pa = ""
                ano_pa = st.number_input("Ano", min_value=2020, max_value=2100, value=2026, step=1, key="prog_an_ano")

                df_ag_pa = pd.DataFrame()
                if mid_pa:
                    try:
                        df_ag_pa = pd.read_sql(
                            "SELECT id, nome FROM agentes WHERE municipio_id=%s AND (ativo IS NULL OR ativo=TRUE) ORDER BY nome",
                            conn, params=(mid_pa,)
                        )
                    except Exception:
                        df_ag_pa = pd.DataFrame()

                op_ag_pa = ["Sem agente específico"] + [f"#{int(r['id'])} — {r['nome']}" for _, r in df_ag_pa.iterrows()]
                ag_pa = st.selectbox("Agente responsável (opcional)", op_ag_pa, key="prog_an_ag")
                agente_pa = None if ag_pa == "Sem agente específico" else int(ag_pa.split("—")[0].replace("#", "").strip())

                c1, c2, c3 = st.columns(3)
                with c1:
                    ud_exist = st.number_input("Nº de prédios / UDs existentes", min_value=0, value=0, step=1, key="prog_an_ud")
                with c2:
                    pits_exist = st.number_input("Nº de PITs existentes", min_value=0, value=0, step=1, key="prog_an_pits")
                with c3:
                    dias_pit = st.number_input("Dias/mês para visita a PIT", min_value=0, max_value=20, value=0, step=1, key="prog_an_dpit")

                c4, c5, c6 = st.columns(3)
                with c4:
                    dias_buro = st.number_input("Dias/mês para atividades burocráticas", min_value=0, max_value=20, value=1, step=1, key="prog_an_dburo")
                with c5:
                    dias_borr = st.number_input("Dias/mês para borrifação + imprevistos", min_value=0, max_value=20, value=2, step=1, key="prog_an_dborr")
                with c6:
                    media_ud = st.number_input("Média de UDs pesquisadas / homem / dia", min_value=0.0, max_value=100.0, value=10.0, step=0.5, key="prog_an_media")

                dias_pesq_calc, ud_mes_calc = calcular_parametros_programacao(
                    ud_exist, pits_exist, dias_pit, dias_buro, dias_borr, media_ud
                )
                ud_q_calc = int(ud_mes_calc * 4)

                st.markdown("#### Resultado calculado")
                r1, r2, r3, r4 = st.columns(4)
                r1.metric("Dias/mês para pesquisa", dias_pesq_calc)
                r2.metric("UDs a pesquisar/mês", ud_mes_calc)
                r3.metric("1º quadrimestre", ud_q_calc)
                r4.metric("2º quadrimestre", ud_q_calc)
                st.caption("O 3º quadrimestre também parte do valor mensal × 4; meses de férias ou ajustes devem ser adequados pelo responsável.")

                c7, c8, c9 = st.columns(3)
                with c7:
                    ud_q1 = st.number_input("UDs — 1º quadrimestre", min_value=0, value=ud_q_calc, step=1, key="prog_an_q1")
                with c8:
                    ud_q2 = st.number_input("UDs — 2º quadrimestre", min_value=0, value=ud_q_calc, step=1, key="prog_an_q2")
                with c9:
                    ud_q3 = st.number_input("UDs — 3º quadrimestre", min_value=0, value=ud_q_calc, step=1, key="prog_an_q3")

                rg_loc = st.text_input(
                    "RG das localidades a serem trabalhadas no ano",
                    placeholder="Ex.: RG 7 à 68",
                    key="prog_an_rg"
                )
                obs_an = st.text_area("Observações do plano anual", key="prog_an_obs")

                if st.button("Salvar plano anual", type="primary", key="prog_an_salvar"):
                    if not mid_pa:
                        st.warning("Selecione o município.")
                    elif not municipio_esta_no_escopo(conn, usuario, mid_pa):
                        st.error("Município fora do escopo de cadastro do usuário.")
                    else:
                        try:
                            cur = conn.cursor()
                            cur.execute("""
                                INSERT INTO programacao_pcdch_anual
                                (municipio_id, agente_id, ano, ud_existentes, pits_existentes,
                                 dias_pit, dias_burocraticos, dias_borrifacao_imprevistos,
                                 dias_pesquisa_mes, media_ud_homem_dia, ud_pesquisar_mes,
                                 ud_pesquisar_q1, ud_pesquisar_q2, ud_pesquisar_q3,
                                 rg_localidades, observacao, atualizado_em)
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP)
                                ON CONFLICT (municipio_id, ano, agente_id)
                                DO UPDATE SET
                                    ud_existentes=EXCLUDED.ud_existentes,
                                    pits_existentes=EXCLUDED.pits_existentes,
                                    dias_pit=EXCLUDED.dias_pit,
                                    dias_burocraticos=EXCLUDED.dias_burocraticos,
                                    dias_borrifacao_imprevistos=EXCLUDED.dias_borrifacao_imprevistos,
                                    dias_pesquisa_mes=EXCLUDED.dias_pesquisa_mes,
                                    media_ud_homem_dia=EXCLUDED.media_ud_homem_dia,
                                    ud_pesquisar_mes=EXCLUDED.ud_pesquisar_mes,
                                    ud_pesquisar_q1=EXCLUDED.ud_pesquisar_q1,
                                    ud_pesquisar_q2=EXCLUDED.ud_pesquisar_q2,
                                    ud_pesquisar_q3=EXCLUDED.ud_pesquisar_q3,
                                    rg_localidades=EXCLUDED.rg_localidades,
                                    observacao=EXCLUDED.observacao,
                                    atualizado_em=CURRENT_TIMESTAMP
                            """, (
                                mid_pa, agente_pa, int(ano_pa), int(ud_exist), int(pits_exist),
                                int(dias_pit), int(dias_buro), int(dias_borr), int(dias_pesq_calc),
                                float(media_ud), int(ud_mes_calc), int(ud_q1), int(ud_q2), int(ud_q3),
                                rg_loc.strip() or None, obs_an.strip() or None
                            ))
                            conn.commit(); cur.close()
                            st.success("Plano anual salvo com sucesso!")
                        except Exception as e:
                            try: conn.rollback()
                            except Exception: pass
                            st.error(f"Erro ao salvar o plano anual: {e}")

                st.markdown("---")
                st.markdown("### Planos anuais cadastrados")
                try:
                    df_planos = pd.read_sql("""
                        SELECT p.id, p.ano, m.nome AS municipio, a.nome AS agente,
                               p.ud_existentes, p.pits_existentes, p.dias_pesquisa_mes,
                               p.ud_pesquisar_mes, p.ud_pesquisar_q1, p.ud_pesquisar_q2, p.ud_pesquisar_q3,
                               p.status
                        FROM programacao_pcdch_anual p
                        LEFT JOIN municipios m ON m.id=p.municipio_id
                        LEFT JOIN agentes a ON a.id=p.agente_id
                        ORDER BY p.ano DESC, m.nome, a.nome
                        LIMIT 1000
                    """, conn)
                    st.dataframe(df_planos if not df_planos.empty else pd.DataFrame(), use_container_width=True, hide_index=True)
                except Exception as e:
                    st.warning(str(e))

        # --------------------------------------------------
        # PROGRAMAÇÃO MENSAL
        # --------------------------------------------------
        with tab_mensal:
            st.markdown("### Programação mensal")
            eid_pm, nucleo_pm, regional_pm, mid_pm = seletor_hierarquia_programacao(
                conn, usuario, df_estados_cad, "prog_me"
            )
            if mid_pm is None:
                st.info("Selecione a hierarquia territorial até chegar ao município para continuar.")
            else:
                mun_pm = ""
                ano_pm = st.number_input("Ano", min_value=2020, max_value=2100, value=2026, step=1, key="prog_me_ano")
                mes_pm = st.selectbox("Mês", list(range(1,13)), format_func=lambda x: f"{x:02d}", key="prog_me_mes")

                df_ag_pm = pd.DataFrame()
                df_loc_pm = pd.DataFrame()
                if mid_pm:
                    try:
                        df_ag_pm = pd.read_sql("SELECT id, nome FROM agentes WHERE municipio_id=%s AND (ativo IS NULL OR ativo=TRUE) ORDER BY nome", conn, params=(mid_pm,))
                        df_loc_pm = pd.read_sql("SELECT id, nome FROM localidades WHERE municipio_id=%s AND (status IS NULL OR status='Ativa') ORDER BY nome", conn, params=(mid_pm,))
                    except Exception:
                        pass

                op_ag_pm = ["Sem agente específico"] + [f"#{int(r['id'])} — {r['nome']}" for _, r in df_ag_pm.iterrows()]
                ag_pm = st.selectbox("Agente", op_ag_pm, key="prog_me_ag")
                agente_pm = None if ag_pm == "Sem agente específico" else int(ag_pm.split("—")[0].replace("#", "").strip())
                op_loc_pm = ["Todas / não específica"] + [f"#{int(r['id'])} — {r['nome']}" for _, r in df_loc_pm.iterrows()]
                loc_pm = st.selectbox("Localidade", op_loc_pm, key="prog_me_loc")
                localidade_pm = None if loc_pm == "Todas / não específica" else int(loc_pm.split("—")[0].replace("#", "").strip())

                data_pm = st.date_input("Data programada", value=date.today(), key="prog_me_data")
                atividade_pm = st.selectbox("Atividade", atividade_programacao_pcdch(), key="prog_me_atividade")
                c1, c2, c3 = st.columns(3)
                with c1:
                    ud_prog = st.number_input("UDs programadas", min_value=0, value=0, step=1, key="prog_me_udp")
                with c2:
                    pit_prog = st.number_input("PITs programados", min_value=0, value=0, step=1, key="prog_me_pitp")
                with c3:
                    dias_prog = st.number_input("Dias programados", min_value=0.0, value=1.0, step=0.5, key="prog_me_diasp")
                obs_pm = st.text_area("Observação", key="prog_me_obs")

                if st.button("Adicionar programação", type="primary", key="prog_me_add"):
                    if not mid_pm:
                        st.warning("Selecione o município.")
                    elif not municipio_esta_no_escopo(conn, usuario, mid_pm):
                        st.error("Município fora do escopo de cadastro do usuário.")
                    else:
                        try:
                            cur = conn.cursor()
                            cur.execute("""
                                INSERT INTO programacao_pcdch_mensal
                                (municipio_id, localidade_id, agente_id, ano, mes, data_programada,
                                 atividade, ud_programadas, pit_programados, dias_programados, observacao)
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            """, (mid_pm, localidade_pm, agente_pm, int(ano_pm), int(mes_pm), data_pm,
                                  atividade_pm, int(ud_prog), int(pit_prog), float(dias_prog), obs_pm.strip() or None))
                            conn.commit(); cur.close(); st.success("Programação adicionada!"); st.rerun()
                        except Exception as e:
                            try: conn.rollback()
                            except Exception: pass
                            st.error(f"Erro ao adicionar programação: {e}")

                st.markdown("---")
                st.markdown("### Itens programados no mês")
                try:
                    df_mes = pd.read_sql("""
                        SELECT p.id, p.data_programada, p.atividade, p.ud_programadas, p.ud_realizadas,
                               p.pit_programados, p.pit_realizados, p.dias_programados, p.dias_realizados,
                               l.nome AS localidade, a.nome AS agente, p.status
                        FROM programacao_pcdch_mensal p
                        LEFT JOIN localidades l ON l.id=p.localidade_id
                        LEFT JOIN agentes a ON a.id=p.agente_id
                        WHERE p.municipio_id=%s AND p.ano=%s AND p.mes=%s
                        ORDER BY p.data_programada, p.id
                    """, conn, params=(mid_pm, int(ano_pm), int(mes_pm))) if mid_pm else pd.DataFrame()
                    st.dataframe(df_mes if not df_mes.empty else pd.DataFrame(), use_container_width=True, hide_index=True)

                    if not df_mes.empty:
                        op_itens = [f"#{int(r['id'])} — {r['data_programada']} | {r['atividade']} | {r['localidade'] or 'Geral'}" for _, r in df_mes.iterrows()]
                        item_sel = st.selectbox("Atualizar item", op_itens, key="prog_me_item")
                        item_id = int(item_sel.split("—")[0].replace("#", "").strip())
                        row_item = df_mes[df_mes["id"] == item_id].iloc[0]
                        c4, c5, c6 = st.columns(3)
                        with c4:
                            ud_real = st.number_input("UDs realizadas", min_value=0, value=int(row_item["ud_realizadas"] or 0), step=1, key="prog_me_udr")
                        with c5:
                            pit_real = st.number_input("PITs realizados", min_value=0, value=int(row_item["pit_realizados"] or 0), step=1, key="prog_me_pitr")
                        with c6:
                            dias_real = st.number_input("Dias realizados", min_value=0.0, value=float(row_item["dias_realizados"] or 0), step=0.5, key="prog_me_diasr")
                        status_item = st.selectbox("Status", ["Programada", "Em andamento", "Concluída", "Não realizada", "Cancelada"], key="prog_me_status")
                        if st.button("Salvar realização", type="primary", key="prog_me_salvar"):
                            cur = conn.cursor()
                            cur.execute("""
                                UPDATE programacao_pcdch_mensal
                                SET ud_realizadas=%s, pit_realizados=%s, dias_realizados=%s,
                                    status=%s, atualizado_em=CURRENT_TIMESTAMP
                                WHERE id=%s
                            """, (int(ud_real), int(pit_real), float(dias_real), status_item, item_id))
                            conn.commit(); cur.close(); st.success("Realização atualizada!"); st.rerun()
                except Exception as e:
                    st.warning(str(e))

        # --------------------------------------------------
        # ACOMPANHAMENTO
        # --------------------------------------------------
        with tab_acomp:
            st.markdown("### Acompanhamento da programação")
            ano_ac = st.number_input("Ano", min_value=2020, max_value=2100, value=2026, step=1, key="prog_ac_ano")
            try:
                df_ac = pd.read_sql("""
                    SELECT m.nome AS municipio,
                           COUNT(p.id) AS atividades,
                           COALESCE(SUM(p.ud_programadas),0) AS ud_programadas,
                           COALESCE(SUM(p.ud_realizadas),0) AS ud_realizadas,
                           COALESCE(SUM(p.pit_programados),0) AS pit_programados,
                           COALESCE(SUM(p.pit_realizados),0) AS pit_realizados,
                           COALESCE(SUM(p.dias_programados),0) AS dias_programados,
                           COALESCE(SUM(p.dias_realizados),0) AS dias_realizados
                    FROM programacao_pcdch_mensal p
                    JOIN municipios m ON m.id=p.municipio_id
                    WHERE p.ano=%s
                    GROUP BY m.id, m.nome
                    ORDER BY m.nome
                """, conn, params=(int(ano_ac),))
                if df_ac.empty:
                    st.info("Ainda não há programação mensal registrada para este ano.")
                else:
                    df_ac["% UDs"] = df_ac.apply(lambda r: round((float(r["ud_realizadas"]) / float(r["ud_programadas"]) * 100), 1) if float(r["ud_programadas"]) else 0, axis=1)
                    df_ac["% PITs"] = df_ac.apply(lambda r: round((float(r["pit_realizados"]) / float(r["pit_programados"]) * 100), 1) if float(r["pit_programados"]) else 0, axis=1)
                    st.dataframe(df_ac, use_container_width=True, hide_index=True)
                    total_prog = int(df_ac["ud_programadas"].sum())
                    total_real = int(df_ac["ud_realizadas"].sum())
                    pct = round(total_real / total_prog * 100, 1) if total_prog else 0
                    st.metric("Execução de UDs no ano", f"{pct}%", f"{total_real} de {total_prog}")
            except Exception as e:
                st.warning(str(e))

    elif menu == "Cadastro":
        sub = st.session_state.get("pcdch_sub") or "Agente"
        st.markdown("---")
        if sub == "Agente":
            ag_sub = st.radio("Agente", ["Novo", "Listar", "Editar / Inativar"], horizontal=True, key="ag_sub")
            st.markdown("---")
            if ag_sub == "Novo":
                st.subheader("Cadastro de Agente")
                est = seletor_estado_cadastro("ag_est")
                eid = estado_id_de_nome(est, df_estados_cad)
                df_mun = municipios_para_cadastro(conn, usuario, False, estado_id=eid)
                mun_sel = st.selectbox("Município", ["Selecione..."] + df_mun["nome"].tolist(), key="ag_mun") if not df_mun.empty else None
                nome = st.text_input("Nome do agente", key="ag_nome")
                cpf = st.text_input("CPF (opcional)", key="ag_cpf")
                matricula = st.text_input("Matrícula (opcional)", key="ag_mat")
                telefone = st.text_input("Telefone (opcional)", key="ag_tel")
                if st.button("Salvar Agente", type="primary", key="ag_btn"):
                    if not nome.strip() or not mun_sel or mun_sel == "Selecione...":
                        st.warning("Informe nome e município.")
                    else:
                        mid = int(df_mun[df_mun["nome"] == mun_sel].iloc[0]["id"])
                        if not municipio_esta_no_escopo(conn, usuario, mid):
                            st.error("Município fora do escopo de cadastro do usuário.")
                            st.stop()
                        try:
                            cur = conn.cursor()
                            cur.execute("INSERT INTO agentes (nome, cpf, matricula, telefone, municipio_id, ativo) VALUES (%s,%s,%s,%s,%s,TRUE)",
                                        (nome.strip(), so_numeros(cpf) or None, matricula.strip() or None, telefone.strip() or None, mid))
                            conn.commit(); cur.close(); st.success(f"Agente **{nome}** salvo!")
                        except Exception as e:
                            st.error(f"Erro: {e}")
            elif ag_sub == "Listar":
                st.subheader("Agentes")
                try:
                    df = pd.read_sql("""
                        SELECT a.id, a.nome, a.cpf, a.matricula, a.ativo, m.nome as municipio, e.nome as estado
                        FROM agentes a
                        LEFT JOIN municipios m ON m.id = a.municipio_id
                        LEFT JOIN regionais_saude r ON r.id = m.regional_id
                        LEFT JOIN estados e ON e.id = r.estado_id
                        ORDER BY e.nome, m.nome, a.nome LIMIT 2000
                    """, conn)
                    if df.empty:
                        st.info("Nenhum agente.")
                    else:
                        df["ativo"] = df["ativo"].apply(lambda x: "Ativo" if x is None or x else "Inativo")
                        st.dataframe(df, use_container_width=True, hide_index=True)
                except Exception as e:
                    st.error(f"Erro: {e}")
            else:
                st.subheader("Editar / Inativar Agente")
                try:
                    df_ag = pd.read_sql("SELECT a.id, a.nome, a.ativo, m.nome as municipio FROM agentes a LEFT JOIN municipios m ON m.id = a.municipio_id ORDER BY a.nome LIMIT 500", conn)
                    if not df_ag.empty:
                        opcoes = [f"#{int(r['id'])} — {r['nome']} [{'Ativo' if r['ativo'] is None or r['ativo'] else 'Inativo'}]" for _, r in df_ag.iterrows()]
                        escolhido = st.selectbox("Agente", opcoes, key="ag_ed_sel")
                        aid = int(escolhido.split("—")[0].replace("#", "").strip())
                        row = df_ag[df_ag["id"] == aid].iloc[0]
                        novo_nome = st.text_input("Nome", value=str(row["nome"] or ""), key="ag_ed_nome")
                        novo_ativo = st.selectbox("Situação", ["Ativo", "Inativo"], index=0 if (row["ativo"] is None or row["ativo"]) else 1, key="ag_ed_ativo")
                        if st.button("Salvar", type="primary", key="ag_ed_salvar"):
                            cur = conn.cursor()
                            cur.execute("UPDATE agentes SET nome=%s, ativo=%s WHERE id=%s", (novo_nome.strip(), novo_ativo == "Ativo", aid))
                            conn.commit(); cur.close(); st.success("Atualizado!"); st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

        elif sub == "Imóvel":
            st.subheader("Cadastro de Imóvel (PCDCh)")
            est = seletor_estado_cadastro("im_est")
            eid = estado_id_de_nome(est, df_estados_cad)
            df_mun = municipios_para_cadastro(conn, usuario, False, estado_id=eid)
            mun_sel = st.selectbox("Município", ["Selecione..."] + df_mun["nome"].tolist(), key="im_mun") if not df_mun.empty else None
            df_loc = pd.DataFrame(); loc_sel = None
            if mun_sel and mun_sel != "Selecione...":
                mid = int(df_mun[df_mun["nome"] == mun_sel].iloc[0]["id"])
                df_loc = pd.read_sql("SELECT id, nome FROM localidades WHERE municipio_id=%s ORDER BY nome", conn, params=(mid,))
                if not df_loc.empty:
                    loc_sel = st.selectbox("Localidade", ["Selecione..."] + df_loc["nome"].tolist(), key="im_loc")
            campos = form_campos_imovel("pcd_imv")
            if st.button("Salvar Imóvel", type="primary", key="im_btn"):
                if not loc_sel or loc_sel == "Selecione..." or not campos["identificacao"]:
                    st.warning("Selecione localidade e identificação.")
                else:
                    lid = int(df_loc[df_loc["nome"] == loc_sel].iloc[0]["id"])
                    try:
                        cur = conn.cursor()
                        cur.execute("""
                            INSERT INTO imoveis
                            (localidade_id, identificacao, quarteirao, lado, sequencia, numero, complemento,
                             tipo, tipo_construcao, situacao, observacao, ativo, data_cadastro)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,TRUE,CURRENT_DATE)
                        """, (lid, campos["identificacao"], campos["quarteirao"], campos["lado"], campos["sequencia"],
                              campos["numero"], campos["complemento"], campos["tipo"], campos["tipo_construcao"],
                              campos["situacao"], campos["observacao"]))
                        conn.commit(); cur.close(); st.success("Imóvel salvo!")
                    except Exception as e:
                        st.error(f"Erro: {e}")

        elif sub == "Etiqueta":
            st.subheader("Controle de Etiquetas")
            est = seletor_estado_cadastro("etq_est")
            eid = estado_id_de_nome(est, df_estados_cad)
            df_mun = municipios_para_cadastro(conn, usuario, False, estado_id=eid)
            if not df_mun.empty:
                mun_sel = st.selectbox("Município", df_mun["nome"].tolist(), key="etq_mun")
                mid = int(df_mun[df_mun["nome"] == mun_sel].iloc[0]["id"])
                atual = obter_proximo_etiqueta(conn, mid)
                st.info(f"Próximo número em **{mun_sel}**: **{atual}**")
                novo_num = st.number_input("Definir próximo número", min_value=1, value=int(atual), key="etq_num")
                if st.button("Salvar número", type="primary", key="etq_salvar"):
                    try:
                        cur = conn.cursor()
                        cur.execute("""
                            INSERT INTO etiquetas_controle (municipio_id, proximo_numero, atualizado_em)
                            VALUES (%s, %s, CURRENT_TIMESTAMP)
                            ON CONFLICT (municipio_id)
                            DO UPDATE SET proximo_numero = EXCLUDED.proximo_numero, atualizado_em = CURRENT_TIMESTAMP
                        """, (mid, int(novo_num)))
                        conn.commit(); cur.close(); st.success("Salvo!"); st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")

        elif sub == "Triatomínio":
            st.subheader("Cadastro de Triatomínio (espécies)")
            tab_t1, tab_t2 = st.tabs(["Listar / Novo", "Inativar"])
            with tab_t1:
                try:
                    df_t = pd.read_sql("SELECT id, nome_cientifico, nome_popular, ativo FROM triatominios ORDER BY nome_cientifico", conn)
                    if df_t.empty:
                        st.info("Nenhuma espécie cadastrada.")
                    else:
                        df_show = df_t.copy()
                        df_show["ativo"] = df_show["ativo"].apply(lambda x: "Ativo" if x is None or x else "Inativo")
                        st.dataframe(df_show, use_container_width=True, hide_index=True)
                except Exception as e:
                    st.error(f"Erro: {e}")
                st.markdown("---")
                nc = st.text_input("Nome científico *", key="tri_nc")
                npop = st.text_input("Nome popular", key="tri_np")
                if st.button("Salvar espécie", type="primary", key="tri_btn"):
                    if not nc.strip():
                        st.warning("Informe o nome científico.")
                    else:
                        try:
                            cur = conn.cursor()
                            cur.execute("INSERT INTO triatominios (nome_cientifico, nome_popular, ativo) VALUES (%s,%s,TRUE)", (nc.strip(), npop.strip() or None))
                            conn.commit(); cur.close(); st.success(f"**{nc}** salva!"); st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")
            with tab_t2:
                try:
                    df_t2 = pd.read_sql("SELECT id, nome_cientifico, ativo FROM triatominios ORDER BY nome_cientifico", conn)
                    if not df_t2.empty:
                        op = [f"#{int(r['id'])} — {r['nome_cientifico']} [{'Ativo' if r['ativo'] is None or r['ativo'] else 'Inativo'}]" for _, r in df_t2.iterrows()]
                        esc = st.selectbox("Espécie", op, key="tri_ed_sel")
                        tid = int(esc.split("—")[0].replace("#", "").strip())
                        row = df_t2[df_t2["id"] == tid].iloc[0]
                        sit = st.selectbox("Situação", ["Ativo", "Inativo"], index=0 if (row["ativo"] is None or row["ativo"]) else 1, key="tri_ed_sit")
                        if st.button("Salvar situação", type="primary", key="tri_ed_btn"):
                            cur = conn.cursor()
                            cur.execute("UPDATE triatominios SET ativo=%s WHERE id=%s", (sit == "Ativo", tid))
                            conn.commit(); cur.close(); st.success("Atualizado!"); st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

        elif sub == "Inseticida":
            st.subheader("Cadastro de Inseticida")
            tab_i1, tab_i2 = st.tabs(["Listar / Novo", "Inativar"])
            with tab_i1:
                try:
                    df_i = pd.read_sql("SELECT id, nome, principio_ativo, formulacao, ativo FROM inseticidas ORDER BY nome", conn)
                    if df_i.empty:
                        st.info("Nenhum inseticida cadastrado.")
                    else:
                        df_show = df_i.copy()
                        df_show["ativo"] = df_show["ativo"].apply(lambda x: "Ativo" if x is None or x else "Inativo")
                        st.dataframe(df_show, use_container_width=True, hide_index=True)
                except Exception as e:
                    st.error(f"Erro: {e}")
                st.markdown("---")
                nome_i = st.text_input("Nome do produto *", key="ins_nome")
                pa = st.text_input("Princípio ativo", key="ins_pa")
                form = st.text_input("Formulação", key="ins_form")
                if st.button("Salvar inseticida", type="primary", key="ins_btn"):
                    if not nome_i.strip():
                        st.warning("Informe o nome do produto.")
                    else:
                        try:
                            cur = conn.cursor()
                            cur.execute("INSERT INTO inseticidas (nome, principio_ativo, formulacao, ativo) VALUES (%s,%s,%s,TRUE)",
                                        (nome_i.strip(), pa.strip() or None, form.strip() or None))
                            conn.commit(); cur.close(); st.success(f"**{nome_i}** salvo!"); st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")
            with tab_i2:
                try:
                    df_i2 = pd.read_sql("SELECT id, nome, ativo FROM inseticidas ORDER BY nome", conn)
                    if not df_i2.empty:
                        op = [f"#{int(r['id'])} — {r['nome']} [{'Ativo' if r['ativo'] is None or r['ativo'] else 'Inativo'}]" for _, r in df_i2.iterrows()]
                        esc = st.selectbox("Inseticida", op, key="ins_ed_sel")
                        iid = int(esc.split("—")[0].replace("#", "").strip())
                        row = df_i2[df_i2["id"] == iid].iloc[0]
                        sit = st.selectbox("Situação", ["Ativo", "Inativo"], index=0 if (row["ativo"] is None or row["ativo"]) else 1, key="ins_ed_sit")
                        if st.button("Salvar situação", type="primary", key="ins_ed_btn"):
                            cur = conn.cursor()
                            cur.execute("UPDATE inseticidas SET ativo=%s WHERE id=%s", (sit == "Ativo", iid))
                            conn.commit(); cur.close(); st.success("Atualizado!"); st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

    elif menu == "Pesquisa":
        sub = st.session_state.get("pcdch_sub") or "Nova Pesquisa"
        st.markdown("---")
        if sub == "Nova Pesquisa":
            st.subheader("Nova Pesquisa Entomológica")
            est = seletor_estado_cadastro("pq_est")
            eid = estado_id_de_nome(est, df_estados_cad)
            df_mun = municipios_para_cadastro(conn, usuario, False, estado_id=eid)
            mun_sel = st.selectbox("Município", ["Selecione..."] + df_mun["nome"].tolist(), key="pq_mun") if not df_mun.empty else None
            df_loc = pd.DataFrame(); loc_sel = None; lid = None; mid = None
            if mun_sel and mun_sel != "Selecione...":
                mid = int(df_mun[df_mun["nome"] == mun_sel].iloc[0]["id"])
                df_loc = pd.read_sql("SELECT id, nome FROM localidades WHERE municipio_id=%s ORDER BY nome", conn, params=(mid,))
                if not df_loc.empty:
                    loc_sel = st.selectbox("Localidade", ["Selecione..."] + df_loc["nome"].tolist(), key="pq_loc")
                    if loc_sel and loc_sel != "Selecione...":
                        lid = int(df_loc[df_loc["nome"] == loc_sel].iloc[0]["id"])
            imovel_id = None
            if lid:
                df_imv = imoveis_da_localidade(conn, lid)
                if not df_imv.empty:
                    opcoes_i = ["Sem imóvel específico"] + [f"#{int(r['id'])} — Q{r['quarteirao'] or '-'} | {r['identificacao'] or '-'}" for _, r in df_imv.iterrows()]
                    imv_sel = st.selectbox("Imóvel (opcional)", opcoes_i, key="pq_imv")
                    if imv_sel != "Sem imóvel específico":
                        imovel_id = int(imv_sel.split("—")[0].replace("#", "").strip())
            agente_id = None
            if mid:
                try:
                    df_ag = pd.read_sql("SELECT id, nome FROM agentes WHERE municipio_id=%s AND (ativo IS NULL OR ativo=TRUE) ORDER BY nome", conn, params=(mid,))
                except Exception:
                    df_ag = pd.DataFrame()
                if not df_ag.empty:
                    op_ag = ["Selecione..."] + [f"#{int(r['id'])} — {r['nome']}" for _, r in df_ag.iterrows()]
                    ag_sel = st.selectbox("Agente", op_ag, key="pq_ag")
                    if ag_sel != "Selecione...":
                        agente_id = int(ag_sel.split("—")[0].replace("#", "").strip())
            sugestao = obter_proximo_etiqueta(conn, mid) if mid else 1
            data_p = st.date_input("Data", value=date.today(), key="pq_data")
            tipo = st.selectbox("Tipo", ["Ativa", "Passiva", "Notificação de morador", "Pesquisa de foco", "Outra"], key="pq_tipo")
            metodo = st.selectbox("Método", ["Captura manual", "Armadilha adesiva", "Armadilha luminosa", "Outro"], key="pq_met")
            c1, c2 = st.columns(2)
            with c1:
                ei = st.number_input("Etiqueta inicial", min_value=1, value=int(sugestao), key="pq_ei")
            with c2:
                ef = st.number_input("Etiqueta final", min_value=int(ei), value=int(ei), key="pq_ef")
            c3, c4 = st.columns(2)
            with c3:
                imov_pesq = st.number_input("Imóveis pesquisados", min_value=0, value=0, key="pq_ip")
            with c4:
                imov_pos = st.number_input("Imóveis positivos", min_value=0, value=0, key="pq_ipo")
            obs = st.text_area("Observações", key="pq_obs")
            if st.button("Salvar Pesquisa", type="primary", key="pq_btn"):
                if not loc_sel or loc_sel == "Selecione...":
                    st.warning("Selecione a localidade.")
                else:
                    try:
                        cur = conn.cursor()
                        cur.execute("""
                            INSERT INTO pesquisas_entomologicas
                            (localidade_id, imovel_id, agente_id, data_pesquisa, tipo_pesquisa, metodo, status,
                             etiqueta_inicial, etiqueta_final, imoveis_pesquisados, imoveis_positivos, observacao, status_envio)
                            VALUES (%s,%s,%s,%s,%s,%s,'Ativa',%s,%s,%s,%s,%s,'Rascunho')
                        """, (lid, imovel_id, agente_id, data_p, tipo, metodo, ei, ef, imov_pesq, imov_pos, obs.strip() or None))
                        if mid and ef:
                            cur.execute("""
                                INSERT INTO etiquetas_controle (municipio_id, proximo_numero, atualizado_em)
                                VALUES (%s, %s, CURRENT_TIMESTAMP)
                                ON CONFLICT (municipio_id)
                                DO UPDATE SET proximo_numero = GREATEST(etiquetas_controle.proximo_numero, EXCLUDED.proximo_numero),
                                              atualizado_em = CURRENT_TIMESTAMP
                            """, (mid, int(ef) + 1))
                        conn.commit(); cur.close(); st.success("Pesquisa salva!")
                    except Exception as e:
                        st.error(f"Erro: {e}")
        elif sub == "Listar":
            try:
                df = pd.read_sql("""
                    SELECT p.id, p.data_pesquisa, p.tipo_pesquisa, p.status, p.imoveis_pesquisados, p.imoveis_positivos,
                           a.nome as agente, l.nome as localidade, m.nome as municipio
                    FROM pesquisas_entomologicas p
                    LEFT JOIN agentes a ON a.id = p.agente_id
                    LEFT JOIN localidades l ON l.id = p.localidade_id
                    LEFT JOIN municipios m ON m.id = l.municipio_id
                    ORDER BY p.data_pesquisa DESC LIMIT 500
                """, conn)
                st.dataframe(df if not df.empty else pd.DataFrame(), use_container_width=True, hide_index=True)
            except Exception as e:
                st.warning(str(e))
        else:
            try:
                df_p = pd.read_sql("SELECT p.id, p.data_pesquisa, p.status, m.nome as municipio FROM pesquisas_entomologicas p LEFT JOIN localidades l ON l.id = p.localidade_id LEFT JOIN municipios m ON m.id = l.municipio_id ORDER BY p.data_pesquisa DESC LIMIT 300", conn)
                if not df_p.empty:
                    opcoes = [f"#{int(r['id'])} — {r['data_pesquisa']} | {r['municipio'] or '-'} [{r['status'] or 'Ativa'}]" for _, r in df_p.iterrows()]
                    escolhido = st.selectbox("Pesquisa", opcoes, key="edpq_sel")
                    pid = int(escolhido.split("—")[0].replace("#", "").strip())
                    row = df_p[df_p["id"] == pid].iloc[0]
                    status_atual = str(row["status"]) if row["status"] in ("Ativa", "Arquivada") else "Ativa"
                    novo_status = st.selectbox("Status", ["Ativa", "Arquivada"], index=0 if status_atual == "Ativa" else 1, key="edpq_status")
                    if st.button("Salvar", type="primary", key="edpq_salvar"):
                        cur = conn.cursor()
                        cur.execute("UPDATE pesquisas_entomologicas SET status=%s WHERE id=%s", (novo_status, pid))
                        conn.commit(); cur.close(); st.success("Atualizado!"); st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")

    elif menu == "Captura":
        sub = st.session_state.get("pcdch_sub") or "Nova Captura"
        st.markdown("---")
        if sub == "Nova Captura":
            st.subheader("Nova Captura")
            est = seletor_estado_cadastro("cp_est")
            eid = estado_id_de_nome(est, df_estados_cad)
            df_mun = municipios_para_cadastro(conn, usuario, False, estado_id=eid)
            mun_sel = st.selectbox("Município", ["Selecione..."] + df_mun["nome"].tolist(), key="cp_mun") if not df_mun.empty else None
            df_loc = pd.DataFrame(); loc_sel = None; lid = None; mid = None
            if mun_sel and mun_sel != "Selecione...":
                mid = int(df_mun[df_mun["nome"] == mun_sel].iloc[0]["id"])
                df_loc = pd.read_sql("SELECT id, nome FROM localidades WHERE municipio_id=%s ORDER BY nome", conn, params=(mid,))
                if not df_loc.empty:
                    loc_sel = st.selectbox("Localidade", ["Selecione..."] + df_loc["nome"].tolist(), key="cp_loc")
                    if loc_sel and loc_sel != "Selecione...":
                        lid = int(df_loc[df_loc["nome"] == loc_sel].iloc[0]["id"])
            pesquisa_id = None
            if lid:
                df_pesq = pesquisas_da_localidade(conn, lid)
                if not df_pesq.empty:
                    opcoes_p = ["Sem vínculo"] + [f"#{int(r['id'])} — {r['data_pesquisa']}" for _, r in df_pesq.iterrows()]
                    pesq_sel = st.selectbox("Pesquisa (opcional)", opcoes_p, key="cp_pesq")
                    if pesq_sel != "Sem vínculo":
                        pesquisa_id = int(pesq_sel.split("—")[0].replace("#", "").strip())
            agente_id = None
            if mid:
                try:
                    df_ag = pd.read_sql("SELECT id, nome FROM agentes WHERE municipio_id=%s AND (ativo IS NULL OR ativo=TRUE) ORDER BY nome", conn, params=(mid,))
                except Exception:
                    df_ag = pd.DataFrame()
                if not df_ag.empty:
                    op_ag = ["Selecione..."] + [f"#{int(r['id'])} — {r['nome']}" for _, r in df_ag.iterrows()]
                    ag_sel = st.selectbox("Agente", op_ag, key="cp_ag")
                    if ag_sel != "Selecione...":
                        agente_id = int(ag_sel.split("—")[0].replace("#", "").strip())
            sugestao = obter_proximo_etiqueta(conn, mid) if mid else 0
            data_c = st.date_input("Data", value=date.today(), key="cp_data")
            especie = st.selectbox("Espécie", lista_especies_triatomineo(conn), key="cp_esp")
            qtd = st.number_input("Quantidade", min_value=1, value=1, key="cp_qtd")
            estagio = st.selectbox("Estágio", ["Ovo", "Ninfa 1", "Ninfa 2", "Ninfa 3", "Ninfa 4", "Ninfa 5", "Adulto"], key="cp_estagio")
            sexo = st.selectbox("Sexo", ["Não se aplica", "Macho", "Fêmea", "Não identificado"], key="cp_sexo")
            local_c = st.selectbox("Local", ["Intradomicílio", "Peridomicílio", "Anexo", "Outro"], key="cp_local")
            num_etq = st.number_input("Nº etiqueta", min_value=0, value=int(sugestao), key="cp_etq")
            examinado = st.checkbox("Examinado em laboratório", key="cp_exam")
            positivo_tc = st.checkbox("Positivo para T. cruzi", key="cp_tc") if examinado else False
            obs = st.text_area("Observações", key="cp_obs")
            if st.button("Salvar Captura", type="primary", key="cp_btn"):
                if not loc_sel or loc_sel == "Selecione...":
                    st.warning("Selecione a localidade.")
                else:
                    try:
                        cur = conn.cursor()
                        cur.execute("""
                            INSERT INTO capturas
                            (localidade_id, pesquisa_id, agente_id, data_captura, especie, quantidade, estagio,
                             sexo, local_captura, numero_etiqueta, examinado, positivo_tc, observacao, status, status_envio)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'Ativa','Rascunho')
                        """, (lid, pesquisa_id, agente_id, data_c, especie, qtd, estagio,
                              None if sexo == "Não se aplica" else sexo, local_c,
                              num_etq if num_etq > 0 else None, examinado, positivo_tc, obs.strip() or None))
                        if mid and num_etq and num_etq > 0:
                            cur.execute("""
                                INSERT INTO etiquetas_controle (municipio_id, proximo_numero, atualizado_em)
                                VALUES (%s, %s, CURRENT_TIMESTAMP)
                                ON CONFLICT (municipio_id)
                                DO UPDATE SET proximo_numero = GREATEST(etiquetas_controle.proximo_numero, EXCLUDED.proximo_numero),
                                              atualizado_em = CURRENT_TIMESTAMP
                            """, (mid, int(num_etq) + 1))
                        conn.commit(); cur.close(); st.success("Captura salva!")
                    except Exception as e:
                        st.error(f"Erro: {e}")
        elif sub == "Listar":
            try:
                df = pd.read_sql("""
                    SELECT c.id, c.data_captura, c.especie, c.quantidade, c.estagio, c.sexo, c.local_captura,
                           c.numero_etiqueta, c.examinado, c.positivo_tc, c.status, a.nome as agente, l.nome as localidade
                    FROM capturas c
                    LEFT JOIN agentes a ON a.id = c.agente_id
                    LEFT JOIN localidades l ON l.id = c.localidade_id
                    ORDER BY c.data_captura DESC LIMIT 500
                """, conn)
                st.dataframe(df if not df.empty else pd.DataFrame(), use_container_width=True, hide_index=True)
            except Exception as e:
                st.warning(str(e))
        else:
            try:
                df_c = pd.read_sql("SELECT id, data_captura, especie, status FROM capturas ORDER BY data_captura DESC LIMIT 300", conn)
                if not df_c.empty:
                    opcoes = [f"#{int(r['id'])} — {r['data_captura']} | {r['especie']} [{r['status'] or 'Ativa'}]" for _, r in df_c.iterrows()]
                    escolhido = st.selectbox("Captura", opcoes, key="edcp_sel")
                    cid = int(escolhido.split("—")[0].replace("#", "").strip())
                    row = df_c[df_c["id"] == cid].iloc[0]
                    status_atual = str(row["status"]) if row["status"] in ("Ativa", "Arquivada") else "Ativa"
                    novo_status = st.selectbox("Status", ["Ativa", "Arquivada"], index=0 if status_atual == "Ativa" else 1, key="edcp_status")
                    if st.button("Salvar", type="primary", key="edcp_salvar"):
                        cur = conn.cursor()
                        cur.execute("UPDATE capturas SET status=%s WHERE id=%s", (novo_status, cid))
                        conn.commit(); cur.close(); st.success("Atualizado!"); st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")

    elif menu == "Diário":
        sub = st.session_state.get("pcdch_sub") or "Novo (unidade domiciliar)"
        st.markdown("---")
        if sub == "Novo (unidade domiciliar)":
            st.subheader("Diário de Pesquisa e/ou Borrifação")
            st.caption("Marque as atividades e preencha os blocos correspondentes (padrão MS-DOS / PCDCh).")

            # 1 - Localização da Unidade Domiciliar
            st.markdown("### 1 — Localização da Unidade Domiciliar")
            est = seletor_estado_cadastro("di_est")
            eid = estado_id_de_nome(est, df_estados_cad)
            df_mun = municipios_para_cadastro(conn, usuario, False, estado_id=eid)
            mun_sel = st.selectbox("Município", ["Selecione..."] + df_mun["nome"].tolist(), key="di_mun") if not df_mun.empty else None
            mid = None
            lid = None
            df_loc = pd.DataFrame()
            codigo_ibge = ""
            if mun_sel and mun_sel != "Selecione...":
                mid = int(df_mun[df_mun["nome"] == mun_sel].iloc[0]["id"])
                codigo_ibge = str(df_mun[df_mun["nome"] == mun_sel].iloc[0].get("codigo_ibge") or "")
                df_loc = pd.read_sql(
                    "SELECT id, nome, tipo FROM localidades WHERE municipio_id=%s AND (status IS NULL OR status='Ativa') ORDER BY nome",
                    conn, params=(mid,)
                )
            loc_sel = st.selectbox("Localidade", ["Selecione..."] + df_loc["nome"].tolist(), key="di_loc") if not df_loc.empty else None
            if loc_sel and loc_sel != "Selecione...":
                lid = int(df_loc[df_loc["nome"] == loc_sel].iloc[0]["id"])
                categoria_sugerida = str(df_loc[df_loc["nome"] == loc_sel].iloc[0].get("tipo") or "")
            else:
                categoria_sugerida = ""

            cA, cB = st.columns(2)
            with cA:
                st.text_input("Código município (IBGE)", value=codigo_ibge, disabled=True, key="di_cod_mun")
            with cB:
                data_ativ = st.date_input("Data da atividade", value=date.today(), key="di_data")

            # Atividades (X)
            st.markdown("### Atividade (marque com X)")
            a1, a2, a3 = st.columns(3)
            with a1:
                faz_pesquisa = st.checkbox("Pesquisa", key="di_x_pesq")
            with a2:
                faz_borrifacao = st.checkbox("Borrifação", key="di_x_borr")
            with a3:
                faz_pit = st.checkbox("At. PIT", key="di_x_pit")


            categoria = st.text_input("Categoria", value=categoria_sugerida, key="di_cat")
            c1, c2, c3 = st.columns(3)
            with c1:
                quarteirao = st.text_input("Quarteirão", key="di_quart")
            with c2:
                casa = st.text_input("Casa", key="di_casa")
            with c3:
                complemento = st.text_input("Complemento", key="di_comp")

            c4, c5 = st.columns(2)
            with c4:
                pend_pesq = st.text_input("Pendência na Pesquisa", key="di_pend_p")
            with c5:
                pend_borr = st.text_input("Pendência na Borrifação", key="di_pend_b")

            morador = st.text_input("Morador / colaborador", key="di_mor")
            c6, c7, c8 = st.columns(3)
            with c6:
                hab = st.number_input("Habitantes", min_value=0, value=0, key="di_hab")
            with c7:
                anexos = st.number_input("Anexos", min_value=0, value=0, key="di_anx")
            with c8:
                situacao = st.selectbox("Situação", ["", "Existente", "Fechado", "Desabitado", "Recusado", "Destruído", "Outro"], key="di_sit")

            c9, c10 = st.columns(2)
            with c9:
                tipo_parede = st.selectbox("Tipo parede", ["", "Alvenaria", "Madeira", "Taipa", "Mista", "Outro"], key="di_parede")
            with c10:
                tipo_teto = st.selectbox("Tipo teto", ["", "Telha", "Laje", "Palha", "Zinco", "Outro"], key="di_teto")

            captura_intra = 0
            vestigios_intra = False
            captura_peri = 0
            vestigios_peri = False
            usa_idet = False
            desalojante = None
            qtde_des = 0.0
            inseticida = None
            qtde_ins = 0.0
            num_pit = None
            notificacao = None
            agente_saude = None
            etiqueta = None

            if faz_pesquisa:
                st.markdown('<div class="diario-box">', unsafe_allow_html=True)
                st.markdown("### 2 — Dados da Pesquisa")
                st.markdown("**Intradomicílio**")
                i1, i2 = st.columns(2)
                with i1:
                    captura_intra = st.number_input("Captura (intra)", min_value=0, value=0, key="di_cap_in")
                with i2:
                    vestigios_intra = st.checkbox("Vestígios (intra)", key="di_ves_in")
                st.markdown("**Peridomicílio**")
                p1, p2 = st.columns(2)
                with p1:
                    captura_peri = st.number_input("Captura (peri)", min_value=0, value=0, key="di_cap_pe")
                with p2:
                    vestigios_peri = st.checkbox("Vestígios (peri)", key="di_ves_pe")
                usa_idet = st.checkbox("Utilizando inseto de detecção", key="di_idet")
                st.markdown("</div>", unsafe_allow_html=True)

            if faz_borrifacao or faz_pit:
                st.markdown('<div class="diario-box">', unsafe_allow_html=True)
                st.markdown("### 2 — Dados da Borrifação / At. PIT")
                b1, b2 = st.columns(2)
                with b1:
                    lista_des = lista_desalojantes(conn)
                    desalojante = st.selectbox(
                        "Desalojante",
                        ["Selecione..."] + lista_des,
                        key="di_des"
                    )
                    if desalojante == "Selecione...":
                        desalojante = None
                    qtde_des = st.number_input("Qtde desalojante", min_value=0.0, value=0.0, step=0.1, key="di_qdes")
                with b2:
                    lista_ins = lista_inseticidas(conn)
                    inseticida = st.selectbox("Inseticida", ["Selecione..."] + lista_ins, key="di_ins")
                    if inseticida == "Selecione...":
                        inseticida = None
                    qtde_ins = st.number_input("Qtde inseticida", min_value=0.0, value=0.0, step=0.1, key="di_qins")
                num_pit = st.text_input("Num. PIT", key="di_npit")
                notificacao = st.text_input("Notificação", key="di_notif")
                agente_saude = st.text_input("Agente de saúde", key="di_ags")
                etq_sug = obter_proximo_etiqueta(conn, mid) if mid else 0
                etiqueta = st.number_input("Etiqueta", min_value=0, value=int(etq_sug), key="di_etq")
                st.markdown("</div>", unsafe_allow_html=True)

            if st.button("Salvar diário da unidade", type="primary", key="di_salvar"):
                if not mid or not lid:
                    st.warning("Selecione município e localidade.")
                elif not (faz_pesquisa or faz_borrifacao or faz_pit):
                    st.warning("Marque ao menos uma atividade: Pesquisa, Borrifação ou At. PIT.")
                else:
                    try:
                        cur = conn.cursor()
                        cur.execute("""
                            INSERT INTO diario_pcdch (
                                data_atividade, municipio_id, localidade_id, categoria,
                                quarteirao, casa, complemento, pendencia_pesquisa, pendencia_borrifacao,
                                morador_colaborador, habitantes, anexos, tipo_parede, tipo_teto, situacao_imovel,
                                faz_pesquisa, faz_borrifacao, faz_pit,
                                captura_intra, vestigios_intra, captura_peri, vestigios_peri, usa_inseto_deteccao,
                                desalojante, qtde_desalojante, inseticida, qtde_inseticida,
                                num_pit, notificacao, agente_saude, etiqueta, status
                            ) VALUES (
                                %s,%s,%s,%s,
                                %s,%s,%s,%s,%s,
                                %s,%s,%s,%s,%s,%s,
                                %s,%s,%s,
                                %s,%s,%s,%s,%s,
                                %s,%s,%s,%s,
                                %s,%s,%s,%s,'Ativo'
                            )
                        """, (
                            data_ativ, mid, lid, categoria.strip() or None,
                            quarteirao.strip() or None, casa.strip() or None, complemento.strip() or None,
                            pend_pesq.strip() or None, pend_borr.strip() or None,
                            morador.strip() or None, int(hab), int(anexos),
                            tipo_parede or None, tipo_teto or None, situacao or None,
                            faz_pesquisa, faz_borrifacao, faz_pit,
                            int(captura_intra), vestigios_intra, int(captura_peri), vestigios_peri, usa_idet,
                            (desalojante or "").strip() or None, float(qtde_des or 0),
                            inseticida, float(qtde_ins or 0),
                            (num_pit or "").strip() or None, (notificacao or "").strip() or None,
                            (agente_saude or "").strip() or None,
                            int(etiqueta) if etiqueta and int(etiqueta) > 0 else None
                        ))
                        if mid and etiqueta and int(etiqueta) > 0:
                            cur.execute("""
                                INSERT INTO etiquetas_controle (municipio_id, proximo_numero, atualizado_em)
                                VALUES (%s, %s, CURRENT_TIMESTAMP)
                                ON CONFLICT (municipio_id)
                                DO UPDATE SET proximo_numero = GREATEST(etiquetas_controle.proximo_numero, EXCLUDED.proximo_numero),
                                              atualizado_em = CURRENT_TIMESTAMP
                            """, (mid, int(etiqueta) + 1))
                        conn.commit(); cur.close()
                        st.success("Diário da unidade domiciliar salvo!")
                    except Exception as e:
                        st.error(f"Erro: {e}. Confirme se a tabela diario_pcdch foi recriada com o SQL novo.")

        elif sub == "Listar":
            st.subheader("Registros do Diário")
            try:
                df = pd.read_sql("""
                    SELECT d.id, d.data_atividade, m.nome as municipio, l.nome as localidade,
                           d.quarteirao, d.casa, d.faz_pesquisa, d.faz_borrifacao, d.faz_pit,
                           d.captura_intra, d.captura_peri, d.inseticida, d.etiqueta, d.status
                    FROM diario_pcdch d
                    LEFT JOIN municipios m ON m.id = d.municipio_id
                    LEFT JOIN localidades l ON l.id = d.localidade_id
                    ORDER BY d.data_atividade DESC, d.id DESC
                    LIMIT 500
                """, conn)
                if df.empty:
                    st.info("Nenhum registro de diário.")
                else:
                    st.dataframe(df, use_container_width=True, hide_index=True)
            except Exception as e:
                st.warning(str(e))

        else:
            st.subheader("Arquivar registro do Diário")
            try:
                df_d = pd.read_sql("""
                    SELECT d.id, d.data_atividade, d.quarteirao, d.casa, d.status, m.nome as municipio
                    FROM diario_pcdch d
                    LEFT JOIN municipios m ON m.id = d.municipio_id
                    ORDER BY d.data_atividade DESC LIMIT 300
                """, conn)
                if df_d.empty:
                    st.info("Nenhum registro.")
                else:
                    opcoes = [f"#{int(r['id'])} — {r['data_atividade']} | {r['municipio'] or '-'} Q{r['quarteirao'] or '-'} Casa {r['casa'] or '-'} [{r['status'] or 'Ativo'}]" for _, r in df_d.iterrows()]
                    escolhido = st.selectbox("Registro", opcoes, key="di_arq_sel")
                    did = int(escolhido.split("—")[0].replace("#", "").strip())
                    row = df_d[df_d["id"] == did].iloc[0]
                    status_atual = str(row["status"]) if row["status"] in ("Ativo", "Arquivado") else "Ativo"
                    novo_status = st.selectbox("Status", ["Ativo", "Arquivado"], index=0 if status_atual == "Ativo" else 1, key="di_arq_status")
                    if st.button("Salvar", type="primary", key="di_arq_btn"):
                        cur = conn.cursor()
                        cur.execute("UPDATE diario_pcdch SET status=%s WHERE id=%s", (novo_status, did))
                        conn.commit(); cur.close(); st.success("Atualizado!"); st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")
    elif menu == "PIT":
        st.subheader("Cadastro de PIT")
        if not garantir_tabela_pits_pcdch(conn):
            st.stop()

        est = seletor_estado_cadastro("pit_est")
        eid = estado_id_de_nome(est, df_estados_cad)
        df_mun = municipios_por_estado(conn, eid, False) if eid else pd.DataFrame()

        if df_mun.empty:
            st.info("Nenhum município disponível para este estado.")
        else:
            mun_sel = st.selectbox(
                "Município",
                ["Selecione..."] + df_mun["nome"].tolist(),
                key="pit_mun"
            )

            if mun_sel and mun_sel != "Selecione...":
                mun_row = df_mun[df_mun["nome"] == mun_sel].iloc[0]
                mid = int(mun_row["id"])
                codigo_mun = str(mun_row["codigo_ibge"] or "")
                st.text_input("Código do Município", value=codigo_mun, disabled=True, key="pit_cod_mun")

                c1, c2 = st.columns(2)
                with c1:
                    codigo_not = st.text_input("Código do notificante", key="pit_cod_not")
                with c2:
                    nome_not = st.text_input("Nome do notificante", key="pit_nome_not")

                st.markdown("---")
                st.markdown("### PITs cadastrados no município")
                try:
                    df_pits = pd.read_sql("""
                        SELECT p.id, p.localidade_id, p.numero_pit, p.nome,
                               l.nome AS localidade
                        FROM pits_pcdch p
                        LEFT JOIN localidades l ON l.id = p.localidade_id
                        WHERE p.municipio_id = %s AND (p.ativo IS NULL OR p.ativo = TRUE)
                        ORDER BY p.numero_pit
                    """, conn, params=(mid,))
                except Exception:
                    df_pits = pd.DataFrame()

                if df_pits.empty:
                    st.info("Nenhum PIT cadastrado neste município.")
                else:
                    df_show = df_pits.copy()
                    df_show["NUM_PIT"] = df_show["numero_pit"].apply(lambda x: f"{int(x):04d}")
                    df_show["ID_LOC"] = df_show["localidade_id"].apply(lambda x: f"{int(x)}" if pd.notna(x) else "")
                    df_show = df_show[["ID_LOC", "NUM_PIT", "nome", "localidade"]].rename(columns={"nome": "NOME", "localidade": "LOCALIDADE"})
                    st.dataframe(df_show, use_container_width=True, hide_index=True)

                st.markdown("---")
                st.markdown("### Consultar / cadastrar PIT")
                num_pit = st.number_input("Número do PIT", min_value=1, max_value=9999, value=1, step=1, format="%04d", key="pit_num")

                try:
                    df_exist = pd.read_sql("""
                        SELECT p.id, p.localidade_id, p.numero_pit, p.nome,
                               p.codigo_notificante, p.nome_notificante, l.nome AS localidade
                        FROM pits_pcdch p
                        LEFT JOIN localidades l ON l.id = p.localidade_id
                        WHERE p.municipio_id = %s AND p.numero_pit = %s
                        LIMIT 1
                    """, conn, params=(mid, int(num_pit)))
                except Exception:
                    df_exist = pd.DataFrame()

                if not df_exist.empty:
                    r = df_exist.iloc[0]
                    st.success(f"PIT **{int(num_pit):04d}** já cadastrado neste município.")
                    st.write(f"**Localidade:** {r['localidade'] or '—'}")
                    st.write(f"**Nome:** {r['nome'] or '—'}")
                    st.caption("Se o PIT já existe, esta consulta apenas identifica o cadastro. O cadastro original não é alterado automaticamente.")
                else:
                    st.info(f"PIT **{int(num_pit):04d}** ainda não está cadastrado em **{mun_sel}**. Preencha os dados abaixo para criá-lo.")
                    df_loc_pit = pd.read_sql("""
                        SELECT id, nome
                        FROM localidades
                        WHERE municipio_id = %s AND (status IS NULL OR status = 'Ativa')
                        ORDER BY nome
                    """, conn, params=(mid,))

                    if df_loc_pit.empty:
                        st.warning("Este município ainda não possui localidades cadastradas no Sisloc.")
                    else:
                        loc_sel = st.selectbox(
                            "Localidade do PIT",
                            ["Selecione..."] + df_loc_pit["nome"].tolist(),
                            key="pit_loc"
                        )
                        nome_pit = st.text_input("Nome do PIT", key="pit_nome")

                        if st.button("Cadastrar PIT", type="primary", key="pit_btn"):
                            if loc_sel == "Selecione..." or not nome_pit.strip():
                                st.warning("Informe a localidade e o nome do PIT.")
                            else:
                                lid_pit = int(df_loc_pit[df_loc_pit["nome"] == loc_sel].iloc[0]["id"])
                                try:
                                    cur = conn.cursor()
                                    cur.execute("""
                                        INSERT INTO pits_pcdch
                                        (municipio_id, localidade_id, numero_pit, nome, codigo_notificante, nome_notificante, ativo)
                                        VALUES (%s,%s,%s,%s,%s,%s,TRUE)
                                    """, (mid, lid_pit, int(num_pit), nome_pit.strip(), codigo_not.strip() or None, nome_not.strip() or None))
                                    conn.commit()
                                    cur.close()
                                    st.success(f"PIT **{int(num_pit):04d}** cadastrado com sucesso!")
                                    st.rerun()
                                except Exception as e:
                                    try:
                                        conn.rollback()
                                    except Exception:
                                        pass
                                    st.error(f"Erro ao cadastrar PIT: {e}")

    elif menu == "Exame":
        st.subheader("Exame de Triatomíneos")
        st.caption("Informe a etiqueta e o município. O sistema localizará o Diário correspondente e montará as linhas conforme as capturas registradas.")

        if not garantir_tabela_exames_pcdch(conn):
            st.stop()

        if "exame_diario_id" not in st.session_state:
            st.session_state.exame_diario_id = None
        if "exame_dados" not in st.session_state:
            st.session_state.exame_dados = None

        st.markdown("### Novo registro")

        f1, f2 = st.columns([1, 2])
        with f1:
            etiqueta_txt = st.text_input("Número da etiqueta", key="ex_etiqueta")
        with f2:
            est_ex = seletor_estado_cadastro("ex_est")
            eid_ex = estado_id_de_nome(est_ex, df_estados_cad)
            df_mun_ex = municipios_por_estado(conn, eid_ex, False) if eid_ex else pd.DataFrame()
            mun_ex = st.selectbox(
                "Município",
                ["Selecione..."] + df_mun_ex["nome"].tolist(),
                key="ex_mun"
            ) if not df_mun_ex.empty else None

        if st.button("Enter — Carregar etiqueta", type="primary", key="ex_carregar"):
            numero = so_numeros(etiqueta_txt)
            if not numero:
                st.warning("Informe o número da etiqueta.")
            elif not mun_ex or mun_ex == "Selecione...":
                st.warning("Selecione o município.")
            else:
                mid_ex = int(df_mun_ex[df_mun_ex["nome"] == mun_ex].iloc[0]["id"])
                try:
                    df_dex = pd.read_sql("""
                        SELECT d.id, d.data_atividade, d.municipio_id, d.localidade_id,
                               d.categoria, d.quarteirao, d.casa, d.complemento,
                               d.morador_colaborador, d.habitantes, d.anexos,
                               d.tipo_parede, d.tipo_teto, d.situacao_imovel,
                               d.captura_intra, d.captura_peri, d.etiqueta,
                               m.nome AS municipio, m.codigo_ibge,
                               l.nome AS localidade
                        FROM diario_pcdch d
                        LEFT JOIN municipios m ON m.id = d.municipio_id
                        LEFT JOIN localidades l ON l.id = d.localidade_id
                        WHERE d.municipio_id = %s
                          AND d.etiqueta = %s
                          AND (d.status IS NULL OR d.status = 'Ativo')
                        ORDER BY d.id DESC
                        LIMIT 1
                    """, conn, params=(mid_ex, int(numero)))

                    if df_dex.empty:
                        st.session_state.exame_diario_id = None
                        st.session_state.exame_dados = None
                        st.error(f"Não foi encontrada a etiqueta {int(numero):05d} no município de {mun_ex}.")
                    else:
                        dados = df_dex.iloc[0].to_dict()
                        total_capturas = int(dados.get("captura_intra") or 0) + int(dados.get("captura_peri") or 0)
                        dados["total_capturas"] = total_capturas
                        st.session_state.exame_diario_id = int(dados["id"])
                        st.session_state.exame_dados = dados
                        st.success(f"Etiqueta {int(numero):05d} carregada.")
                        st.rerun()
                except Exception as e:
                    st.error(f"Erro ao localizar a etiqueta: {e}")

        dados = st.session_state.get("exame_dados")

        if dados:
            st.markdown("---")
            st.markdown("### 1 — Dados da unidade domiciliar")

            info1, info2, info3, info4 = st.columns(4)
            with info1:
                st.text_input("Etiqueta", value=f"{int(dados['etiqueta']):05d}", disabled=True, key="ex_info_etq")
            with info2:
                st.text_input("Município", value=f"{dados.get('codigo_ibge') or ''} — {dados.get('municipio') or ''}", disabled=True, key="ex_info_mun")
            with info3:
                st.text_input("Localidade", value=str(dados.get("localidade") or ""), disabled=True, key="ex_info_loc")
            with info4:
                st.text_input("Data da pesquisa", value=str(dados.get("data_atividade") or ""), disabled=True, key="ex_info_data")

            u1, u2, u3 = st.columns(3)
            with u1:
                st.text_input("Casa", value=str(dados.get("casa") or ""), disabled=True, key="ex_info_casa")
            with u2:
                st.text_input("Complemento", value=str(dados.get("complemento") or ""), disabled=True, key="ex_info_comp")
            with u3:
                st.text_input("Morador / colaborador", value=str(dados.get("morador_colaborador") or ""), disabled=True, key="ex_info_mor")

            u4, u5, u6, u7 = st.columns(4)
            with u4:
                st.text_input("Habitantes", value=str(int(dados.get("habitantes") or 0)), disabled=True, key="ex_info_hab")
            with u5:
                st.text_input("Anexos", value=str(int(dados.get("anexos") or 0)), disabled=True, key="ex_info_anx")
            with u6:
                st.text_input("Tipo de parede", value=str(dados.get("tipo_parede") or ""), disabled=True, key="ex_info_par")
            with u7:
                st.text_input("Tipo de teto", value=str(dados.get("tipo_teto") or ""), disabled=True, key="ex_info_tet")

            st.text_input("Situação", value=str(dados.get("situacao_imovel") or ""), disabled=True, key="ex_info_sit")

            total = int(dados.get("total_capturas") or 0)
            intra = int(dados.get("captura_intra") or 0)
            peri = int(dados.get("captura_peri") or 0)

            st.markdown("---")
            st.markdown("### 2 — Dados sobre exame do Triatomíneo")
            st.info(f"Capturas registradas no Diário: **{total}** — Intradomicílio: **{intra}** | Peridomicílio: **{peri}**")

            if total == 0:
                st.warning("Não há captura registrada no Diário para esta etiqueta. Não é necessário preencher o Exame.")
                if st.button("Novo registro", key="ex_novo_sem_captura"):
                    st.session_state.exame_diario_id = None
                    st.session_state.exame_dados = None
                    st.rerun()
            else:
                especies = ["Selecione..."] + lista_especies_triatomineo(conn)
                capturas_padrao = (["1 — Intradomicílio"] * intra) + (["2 — Peridomicílio"] * peri)

                try:
                    df_exist = pd.read_sql("""
                        SELECT sequencia, especie, local_captura, estagio, resultado
                        FROM exames_pcdch
                        WHERE diario_id = %s
                        ORDER BY sequencia
                    """, conn, params=(int(dados["id"]),))
                    existentes = {int(r["sequencia"]): r for _, r in df_exist.iterrows()}
                except Exception:
                    existentes = {}

                st.markdown("**Seq. | Espécie de triatomíneo | Captura | Estádio da captura | Resultado**")

                linhas_exame = []
                with st.form("ex_form_linhas"):
                    for seq in range(1, total + 1):
                        anterior = existentes.get(seq)
                        especie_anterior = str(anterior["especie"] or "") if anterior is not None else ""
                        captura_anterior = str(anterior["local_captura"] or "") if anterior is not None else capturas_padrao[seq - 1]
                        estagio_anterior = str(anterior["estagio"] or "") if anterior is not None else ""
                        resultado_anterior = str(anterior["resultado"] or "") if anterior is not None else ""

                        cseq, cesp, ccap, cest, cres = st.columns([0.45, 2.3, 1.8, 1.8, 1.8])
                        with cseq:
                            st.text_input("Seq.", value=f"{seq:02d}", disabled=True, key=f"ex_seq_{seq}")
                        with cesp:
                            idx_esp = especies.index(especie_anterior) if especie_anterior in especies else 0
                            especie = st.selectbox("Espécie", especies, index=idx_esp, key=f"ex_esp_{seq}")
                        with ccap:
                            locais = ["1 — Intradomicílio", "2 — Peridomicílio"]
                            idx_cap = locais.index(captura_anterior) if captura_anterior in locais else 0
                            captura = st.selectbox("Captura", locais, index=idx_cap, key=f"ex_cap_{seq}")
                        with cest:
                            estagios = ["Selecione...", "1 — Ninfa", "2 — Adulto macho", "3 — Adulto fêmea"]
                            idx_est = estagios.index(estagio_anterior) if estagio_anterior in estagios else 0
                            estagio = st.selectbox("Estádio", estagios, index=idx_est, key=f"ex_estg_{seq}")
                        with cres:
                            resultados = ["Selecione...", "1 — Positivo (+)", "2 — Negativo (-)", "3 — Não exam."]
                            idx_res = resultados.index(resultado_anterior) if resultado_anterior in resultados else 0
                            resultado = st.selectbox("Resultado", resultados, index=idx_res, key=f"ex_res_{seq}")

                        linhas_exame.append((seq, especie, captura, estagio, resultado))

                    st.markdown("---")
                    salvar_exame = st.form_submit_button("Salvar exame / Encerrar", type="primary")

                if salvar_exame:
                    preenchidas = []
                    incompleta = False
                    for seq, especie, captura, estagio, resultado in linhas_exame:
                        iniciou = especie != "Selecione..." or estagio != "Selecione..." or resultado != "Selecione..."
                        if not iniciou:
                            continue
                        if especie == "Selecione..." or estagio == "Selecione..." or resultado == "Selecione...":
                            incompleta = True
                            break
                        preenchidas.append((seq, especie, captura, estagio, resultado))

                    if incompleta:
                        st.warning("A linha iniciada precisa ser completada: espécie, estádio e resultado.")
                    elif not preenchidas:
                        st.warning("Preencha pelo menos uma linha do exame ou encerre sem iniciar nenhuma.")
                    else:
                        qtd_intra = sum(1 for _, _, captura, _, _ in preenchidas if captura == "1 — Intradomicílio")
                        qtd_peri = sum(1 for _, _, captura, _, _ in preenchidas if captura == "2 — Peridomicílio")
                        if qtd_intra > intra or qtd_peri > peri:
                            st.error("A quantidade de capturas informada no Exame não pode ultrapassar as capturas registradas no Diário para cada local.")
                        else:
                            try:
                                cur = conn.cursor()
                                for seq, especie, captura, estagio, resultado in preenchidas:
                                    cur.execute("""
                                        INSERT INTO exames_pcdch
                                            (diario_id, municipio_id, localidade_id, etiqueta, sequencia,
                                             especie, local_captura, estagio, resultado, atualizado_em)
                                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP)
                                        ON CONFLICT (diario_id, sequencia)
                                        DO UPDATE SET
                                            especie=EXCLUDED.especie,
                                            local_captura=EXCLUDED.local_captura,
                                            estagio=EXCLUDED.estagio,
                                            resultado=EXCLUDED.resultado,
                                            atualizado_em=CURRENT_TIMESTAMP
                                    """, (
                                        int(dados["id"]), int(dados["municipio_id"]), int(dados["localidade_id"]),
                                        int(dados["etiqueta"]), int(seq), especie, captura, estagio, resultado
                                    ))
                                conn.commit()
                                cur.close()
                                st.success(f"Exame salvo: {len(preenchidas)} linha(s) registrada(s).")
                                st.session_state.exame_diario_id = None
                                st.session_state.exame_dados = None
                                for k in list(st.session_state.keys()):
                                    if str(k).startswith("ex_"):
                                        del st.session_state[k]
                                st.rerun()
                            except Exception as e:
                                try:
                                    conn.rollback()
                                except Exception:
                                    pass
                                st.error(f"Erro ao salvar o exame: {e}")

    elif menu == "Diário":
        sub = st.session_state.get("pcdch_sub") or "Novo (unidade domiciliar)"
        st.markdown("---")
        if sub == "Novo (unidade domiciliar)":
            st.subheader("Diário de Pesquisa e/ou Borrifação")
            st.caption("Marque as atividades e preencha os blocos correspondentes (padrão MS-DOS / PCDCh).")

            # 1 - Localização da Unidade Domiciliar
            st.markdown("### 1 — Localização da Unidade Domiciliar")
            est = seletor_estado_cadastro("di_est")
            eid = estado_id_de_nome(est, df_estados_cad)
            df_mun = municipios_por_estado(conn, eid, False) if eid else pd.DataFrame()
            mun_sel = st.selectbox("Município", ["Selecione..."] + df_mun["nome"].tolist(), key="di_mun") if not df_mun.empty else None
            mid = None
            lid = None
            df_loc = pd.DataFrame()
            codigo_ibge = ""
            if mun_sel and mun_sel != "Selecione...":
                mid = int(df_mun[df_mun["nome"] == mun_sel].iloc[0]["id"])
                codigo_ibge = str(df_mun[df_mun["nome"] == mun_sel].iloc[0].get("codigo_ibge") or "")
                df_loc = pd.read_sql(
                    "SELECT id, nome, tipo FROM localidades WHERE municipio_id=%s AND (status IS NULL OR status='Ativa') ORDER BY nome",
                    conn, params=(mid,)
                )
            loc_sel = st.selectbox("Localidade", ["Selecione..."] + df_loc["nome"].tolist(), key="di_loc") if not df_loc.empty else None
            if loc_sel and loc_sel != "Selecione...":
                lid = int(df_loc[df_loc["nome"] == loc_sel].iloc[0]["id"])
                categoria_sugerida = str(df_loc[df_loc["nome"] == loc_sel].iloc[0].get("tipo") or "")
            else:
                categoria_sugerida = ""

            cA, cB = st.columns(2)
            with cA:
                st.text_input("Código município (IBGE)", value=codigo_ibge, disabled=True, key="di_cod_mun")
            with cB:
                data_ativ = st.date_input("Data da atividade", value=date.today(), key="di_data")

            # Atividades (X)
            st.markdown("### Atividade (marque com X)")
            a1, a2, a3 = st.columns(3)
            with a1:
                faz_pesquisa = st.checkbox("Pesquisa", key="di_x_pesq")
            with a2:
                faz_borrifacao = st.checkbox("Borrifação", key="di_x_borr")
            with a3:
                faz_pit = st.checkbox("At. PIT", key="di_x_pit")

            categoria = st.text_input("Categoria", value=categoria_sugerida, key="di_cat")
            c1, c2, c3 = st.columns(3)
            with c1:
                quarteirao = st.text_input("Quarteirão", key="di_quart")
            with c2:
                casa = st.text_input("Casa", key="di_casa")
            with c3:
                complemento = st.text_input("Complemento", key="di_comp")

            c4, c5 = st.columns(2)
            with c4:
                pend_pesq = st.text_input("Pendência na Pesquisa", key="di_pend_p")
            with c5:
                pend_borr = st.text_input("Pendência na Borrifação", key="di_pend_b")

            morador = st.text_input("Morador / colaborador", key="di_mor")
            c6, c7, c8 = st.columns(3)
            with c6:
                hab = st.number_input("Habitantes", min_value=0, value=0, key="di_hab")
            with c7:
                anexos = st.number_input("Anexos", min_value=0, value=0, key="di_anx")
            with c8:
                situacao = st.selectbox("Situação", ["", "Existente", "Fechado", "Desabitado", "Recusado", "Destruído", "Outro"], key="di_sit")

            c9, c10 = st.columns(2)
            with c9:
                tipo_parede = st.selectbox("Tipo parede", ["", "Alvenaria", "Madeira", "Taipa", "Mista", "Outro"], key="di_parede")
            with c10:
                tipo_teto = st.selectbox("Tipo teto", ["", "Telha", "Laje", "Palha", "Zinco", "Outro"], key="di_teto")

            captura_intra = 0
            vestigios_intra = False
            captura_peri = 0
            vestigios_peri = False
            usa_idet = False
            desalojante = None
            qtde_des = 0.0
            inseticida = None
            qtde_ins = 0.0
            num_pit = None
            notificacao = None
            agente_saude = None
            etiqueta = None

            if faz_pesquisa:
                st.markdown('<div class="diario-box">', unsafe_allow_html=True)
                st.markdown("### 2 — Dados da Pesquisa")
                st.markdown("**Intradomicílio**")
                i1, i2 = st.columns(2)
                with i1:
                    captura_intra = st.number_input("Captura (intra)", min_value=0, value=0, key="di_cap_in")
                with i2:
                    vestigios_intra = st.checkbox("Vestígios (intra)", key="di_ves_in")
                st.markdown("**Peridomicílio**")
                p1, p2 = st.columns(2)
                with p1:
                    captura_peri = st.number_input("Captura (peri)", min_value=0, value=0, key="di_cap_pe")
                with p2:
                    vestigios_peri = st.checkbox("Vestígios (peri)", key="di_ves_pe")
                usa_idet = st.checkbox("Utilizando inseto de detecção", key="di_idet")
                st.markdown("</div>", unsafe_allow_html=True)

            if faz_borrifacao or faz_pit:
                st.markdown('<div class="diario-box">', unsafe_allow_html=True)
                st.markdown("### 2 — Dados da Borrifação / At. PIT")
                b1, b2 = st.columns(2)
                with b1:
                    desalojante = st.text_input("Desalojante", key="di_des")
                    qtde_des = st.number_input("Qtde desalojante", min_value=0.0, value=0.0, step=0.1, key="di_qdes")
                with b2:
                    lista_ins = lista_inseticidas(conn)
                    inseticida = st.selectbox("Inseticida", ["Selecione..."] + lista_ins, key="di_ins")
                    if inseticida == "Selecione...":
                        inseticida = None
                    qtde_ins = st.number_input("Qtde inseticida", min_value=0.0, value=0.0, step=0.1, key="di_qins")
                num_pit = st.text_input("Num. PIT", key="di_npit")
                notificacao = st.text_input("Notificação", key="di_notif")
                agente_saude = st.text_input("Agente de saúde", key="di_ags")
                etq_sug = obter_proximo_etiqueta(conn, mid) if mid else 0
                etiqueta = st.number_input("Etiqueta", min_value=0, value=int(etq_sug), key="di_etq")
                st.markdown("</div>", unsafe_allow_html=True)

            if st.button("Salvar diário da unidade", type="primary", key="di_salvar"):
                if not mid or not lid:
                    st.warning("Selecione município e localidade.")
                elif not (faz_pesquisa or faz_borrifacao or faz_pit):
                    st.warning("Marque ao menos uma atividade: Pesquisa, Borrifação ou At. PIT.")
                else:
                    try:
                        cur = conn.cursor()
                        cur.execute("""
                            INSERT INTO diario_pcdch (
                                data_atividade, municipio_id, localidade_id, categoria,
                                quarteirao, casa, complemento, pendencia_pesquisa, pendencia_borrifacao,
                                morador_colaborador, habitantes, anexos, tipo_parede, tipo_teto, situacao_imovel,
                                faz_pesquisa, faz_borrifacao, faz_pit,
                                captura_intra, vestigios_intra, captura_peri, vestigios_peri, usa_inseto_deteccao,
                                desalojante, qtde_desalojante, inseticida, qtde_inseticida,
                                num_pit, notificacao, agente_saude, etiqueta, status
                            ) VALUES (
                                %s,%s,%s,%s,
                                %s,%s,%s,%s,%s,
                                %s,%s,%s,%s,%s,%s,
                                %s,%s,%s,
                                %s,%s,%s,%s,%s,
                                %s,%s,%s,%s,
                                %s,%s,%s,%s,'Ativo'
                            )
                        """, (
                            data_ativ, mid, lid, categoria.strip() or None,
                            quarteirao.strip() or None, casa.strip() or None, complemento.strip() or None,
                            pend_pesq.strip() or None, pend_borr.strip() or None,
                            morador.strip() or None, int(hab), int(anexos),
                            tipo_parede or None, tipo_teto or None, situacao or None,
                            faz_pesquisa, faz_borrifacao, faz_pit,
                            int(captura_intra), vestigios_intra, int(captura_peri), vestigios_peri, usa_idet,
                            (desalojante or "").strip() or None, float(qtde_des or 0),
                            inseticida, float(qtde_ins or 0),
                            (num_pit or "").strip() or None, (notificacao or "").strip() or None,
                            (agente_saude or "").strip() or None,
                            int(etiqueta) if etiqueta and int(etiqueta) > 0 else None
                        ))
                        if mid and etiqueta and int(etiqueta) > 0:
                            cur.execute("""
                                INSERT INTO etiquetas_controle (municipio_id, proximo_numero, atualizado_em)
                                VALUES (%s, %s, CURRENT_TIMESTAMP)
                                ON CONFLICT (municipio_id)
                                DO UPDATE SET proximo_numero = GREATEST(etiquetas_controle.proximo_numero, EXCLUDED.proximo_numero),
                                              atualizado_em = CURRENT_TIMESTAMP
                            """, (mid, int(etiqueta) + 1))
                        conn.commit(); cur.close()
                        st.success("Diário da unidade domiciliar salvo!")
                    except Exception as e:
                        st.error(f"Erro: {e}. Confirme se a tabela diario_pcdch foi recriada com o SQL novo.")

        elif sub == "Listar":
            st.subheader("Registros do Diário")
            try:
                df = pd.read_sql("""
                    SELECT d.id, d.data_atividade, m.nome as municipio, l.nome as localidade,
                           d.quarteirao, d.casa, d.faz_pesquisa, d.faz_borrifacao, d.faz_pit,
                           d.captura_intra, d.captura_peri, d.inseticida, d.etiqueta, d.status
                    FROM diario_pcdch d
                    LEFT JOIN municipios m ON m.id = d.municipio_id
                    LEFT JOIN localidades l ON l.id = d.localidade_id
                    ORDER BY d.data_atividade DESC, d.id DESC
                    LIMIT 500
                """, conn)
                if df.empty:
                    st.info("Nenhum registro de diário.")
                else:
                    st.dataframe(df, use_container_width=True, hide_index=True)
            except Exception as e:
                st.warning(str(e))

        else:
            st.subheader("Arquivar registro do Diário")
            try:
                df_d = pd.read_sql("""
                    SELECT d.id, d.data_atividade, d.quarteirao, d.casa, d.status, m.nome as municipio
                    FROM diario_pcdch d
                    LEFT JOIN municipios m ON m.id = d.municipio_id
                    ORDER BY d.data_atividade DESC LIMIT 300
                """, conn)
                if df_d.empty:
                    st.info("Nenhum registro.")
                else:
                    opcoes = [f"#{int(r['id'])} — {r['data_atividade']} | {r['municipio'] or '-'} Q{r['quarteirao'] or '-'} Casa {r['casa'] or '-'} [{r['status'] or 'Ativo'}]" for _, r in df_d.iterrows()]
                    escolhido = st.selectbox("Registro", opcoes, key="di_arq_sel")
                    did = int(escolhido.split("—")[0].replace("#", "").strip())
                    row = df_d[df_d["id"] == did].iloc[0]
                    status_atual = str(row["status"]) if row["status"] in ("Ativo", "Arquivado") else "Ativo"
                    novo_status = st.selectbox("Status", ["Ativo", "Arquivado"], index=0 if status_atual == "Ativo" else 1, key="di_arq_status")
                    if st.button("Salvar", type="primary", key="di_arq_btn"):
                        cur = conn.cursor()
                        cur.execute("UPDATE diario_pcdch SET status=%s WHERE id=%s", (novo_status, did))
                        conn.commit(); cur.close(); st.success("Atualizado!"); st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")

    conn.close()

elif st.session_state.pagina == "PCL":
    conn = conectar_banco()
    if not conn:
        st.stop()
    try:
        garantir_tabelas_pcl(conn)
    except Exception as e:
        st.error(f"Erro ao preparar o PCL: {e}")
        conn.close(); st.stop()

    doenca = st.session_state.get("pcl_doenca")
    menu_pcl = st.session_state.get("pcl_menu")

    imagem_pcl = localizar_imagem_modulo("pcl", "leishmaniose")

    if not doenca:
        # A imagem institucional do PCL aparece SOMENTE na entrada do módulo.
        # A escolha LV/LT agora fica exclusivamente na lateral.
        if st.session_state.get("modulo_inicio", True) and imagem_pcl:
            st.image(imagem_pcl, use_container_width=True)
            st.markdown("---")

        st.markdown('<div class="module-header"><h1>PCL</h1><p>Programa de Controle da Leishmaniose</p></div>', unsafe_allow_html=True)
        st.markdown("### Selecione no menu lateral a forma de leishmaniose que deseja operar")
        conn.close()
    else:
        titulo = "Leishmaniose Visceral (LV)" if doenca == "LV" else "Leishmaniose Tegumentar (LT)"
        st.markdown(f'<div class="module-header"><h1>PCL — {titulo}</h1><p>Vigilância, investigação, prevenção e controle</p></div>', unsafe_allow_html=True)
        if st.button("← PCL", key="pcl_back_doenca"):
            st.session_state.pcl_doenca = None; st.session_state.pcl_menu = None; st.session_state.pcl_sub = None; st.session_state.modulo_inicio = True; st.rerun()

        def pcl_estado(key):
            df_est = carregar_estados_cadastro(conn, usuario) if nivel != "Federal" else carregar_estados_todos(conn)
            if df_est.empty:
                st.warning("Nenhum estado disponível para o seu escopo."); return None, None, df_est
            if nivel == "Federal":
                est = st.selectbox("Estado", ["Selecione..."] + df_est["nome"].astype(str).tolist(), key=key)
            else:
                est = str(df_est.iloc[0]["nome"]); st.selectbox("Estado", [est], disabled=True, key=key)
            if est == "Selecione...": return None, None, df_est
            eid = int(df_est[df_est["nome"] == est].iloc[0]["id"])
            return est, eid, df_est

        def pcl_municipio(eid, key):
            df_m = municipios_para_cadastro(conn, usuario, False, estado_id=eid) if eid else pd.DataFrame()
            if df_m.empty:
                st.info("Nenhum município disponível para o Estado selecionado."); return None, df_m
            mun = st.selectbox("Município", ["Selecione..."] + df_m["nome"].astype(str).tolist(), key=key)
            return (mun if mun != "Selecione..." else None), df_m

        if menu_pcl is None:
            # As áreas de operação ficam exclusivamente no menu lateral.
            # Isso evita a duplicação de botões na tela e na lateral.
            st.info("Selecione uma área de operação no menu lateral para continuar.")
        else:
            st.markdown(f"### {menu_pcl}")
            if st.button("← Voltar às opções", key="pcl_back_ops"):
                st.session_state.pcl_menu = None; st.session_state.pcl_sub = None; st.session_state.modulo_inicio = True; st.rerun()

            # LV — Vigilância Humana
            if doenca == "LV" and menu_pcl == "Vigilância Humana":
                sub = st.session_state.get("pcl_sub") or "Novo Caso"
                sub = st.radio("Operação", ["Novo Caso","Consultar Casos"], horizontal=True, key="pcl_lv_hum_sub")
                st.session_state.pcl_sub = sub
                if sub == "Novo Caso":
                    est,eid,_ = pcl_estado("pcl_lv_h_est"); mun,df_m = pcl_municipio(eid,"pcl_lv_h_mun")
                    mid = int(df_m[df_m["nome"] == mun].iloc[0]["id"]) if mun else None
                    c1,c2 = st.columns(2)
                    with c1: nome=st.text_input("Nome do caso *",key="pcl_lvh_nome")
                    with c2: nasc=st.date_input("Data de nascimento",value=date(2000,1,1),key="pcl_lvh_nasc")
                    c1,c2,c3 = st.columns(3)
                    with c1: sexo=st.selectbox("Sexo",["Não informado","Masculino","Feminino"],key="pcl_lvh_sexo")
                    with c2: dt_not=st.date_input("Data da notificação",value=date.today(),key="pcl_lvh_not")
                    with c3: notificacao=st.text_input("Nº da notificação",key="pcl_lvh_num")
                    local=st.text_area("Local provável de infecção / exposição",key="pcl_lvh_lpi")
                    sintomas=st.text_area("Sinais e sintomas",key="pcl_lvh_sint")
                    c1,c2,c3=st.columns(3)
                    with c1: diag=st.selectbox("Diagnóstico",["Suspeito","Clínico","Laboratorial","Outro"],key="pcl_lvh_diag")
                    with c2: resultado=st.text_input("Resultado diagnóstico",key="pcl_lvh_res")
                    with c3: dt_diag=st.date_input("Data do diagnóstico",value=date.today(),key="pcl_lvh_dt")
                    tratamento=st.text_input("Tratamento",key="pcl_lvh_trat")
                    evolucao=st.selectbox("Evolução",["Em acompanhamento","Cura","Abandono","Transferência","Óbito","Outro"],key="pcl_lvh_evol")
                    obs=st.text_area("Observações",key="pcl_lvh_obs")
                    if st.button("Salvar caso LV",type="primary",key="pcl_lvh_save"):
                        if not nome.strip() or not mid: st.warning("Informe o nome e selecione o município.")
                        else:
                            try:
                                cur=conn.cursor(); cur.execute("INSERT INTO pcl_lv_humana (estado_id,municipio_id,notificacao,nome,data_nascimento,sexo,data_notificacao,local_provavel,sintomas,diagnostico,resultado,data_diagnostico,tratamento,evolucao,observacao) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (eid,mid,notificacao.strip() or None,nome.strip(),nasc,sexo,dt_not,local.strip() or None,sintomas.strip() or None,diag,resultado.strip() or None,dt_diag,tratamento.strip() or None,evolucao,obs.strip() or None)); conn.commit(); cur.close(); st.success("Caso de LV registrado com sucesso!")
                            except Exception as e: conn.rollback(); st.error(f"Erro ao salvar caso LV: {e}")
                else:
                    df=pd.read_sql("SELECT id,nome,data_notificacao,sexo,diagnostico,resultado,evolucao,criado_em FROM pcl_lv_humana ORDER BY id DESC LIMIT 500",conn); st.dataframe(df,use_container_width=True,hide_index=True)

            elif doenca == "LV" and menu_pcl == "Vigilância Canina":
                sub=st.radio("Operação",["Novo Registro","Consultar"],horizontal=True,key="pcl_lv_c_sub")
                if sub == "Novo Registro":
                    est,eid,_=pcl_estado("pcl_lv_c_est"); mun,df_m=pcl_municipio(eid,"pcl_lv_c_mun"); mid=int(df_m[df_m["nome"]==mun].iloc[0]["id"]) if mun else None
                    c1,c2=st.columns(2)
                    with c1: animal=st.text_input("Identificação do cão",key="pcl_lvc_animal")
                    with c2: resp=st.text_input("Responsável",key="pcl_lvc_resp")
                    c1,c2,c3=st.columns(3)
                    with c1: sexo=st.selectbox("Sexo",["Não informado","Macho","Fêmea"],key="pcl_lvc_sexo")
                    with c2: idade=st.number_input("Idade (anos)",min_value=0.0,value=0.0,step=0.1,key="pcl_lvc_idade")
                    with c3: raca=st.text_input("Raça",key="pcl_lvc_raca")
                    c1,c2,c3=st.columns(3)
                    with c1: dt=st.date_input("Data da coleta",value=date.today(),key="pcl_lvc_dt")
                    with c2: exame=st.text_input("Exame / método",key="pcl_lvc_exame")
                    with c3: resultado=st.selectbox("Resultado",["Não realizado","Negativo","Positivo","Indeterminado"],key="pcl_lvc_res")
                    situacao=st.selectbox("Situação",["Em investigação","Acompanhamento","Encerrado","Outro"],key="pcl_lvc_sit")
                    obs=st.text_area("Observações",key="pcl_lvc_obs")
                    if st.button("Salvar registro canino",type="primary",key="pcl_lvc_save"):
                        if not mid: st.warning("Selecione o município.")
                        else:
                            try:
                                cur=conn.cursor(); cur.execute("INSERT INTO pcl_lv_canina (estado_id,municipio_id,nome_animal,responsavel,sexo,idade_anos,raca,data_coleta,tipo_exame,resultado,situacao,observacao) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(eid,mid,animal.strip() or None,resp.strip() or None,sexo,idade,raca.strip() or None,dt,exame.strip() or None,resultado,situacao,obs.strip() or None)); conn.commit(); cur.close(); st.success("Registro canino salvo!")
                            except Exception as e: conn.rollback(); st.error(f"Erro: {e}")
                else:
                    df=pd.read_sql("SELECT id,nome_animal,responsavel,data_coleta,resultado,situacao,criado_em FROM pcl_lv_canina ORDER BY id DESC LIMIT 500",conn); st.dataframe(df,use_container_width=True,hide_index=True)

            elif doenca == "LV" and menu_pcl == "Vigilância Entomológica":
                sub=st.radio("Operação",["Nova Coleta","Consultar"],horizontal=True,key="pcl_lv_e_sub")
                if sub == "Nova Coleta":
                    est,eid,_=pcl_estado("pcl_lv_e_est"); mun,df_m=pcl_municipio(eid,"pcl_lv_e_mun"); mid=int(df_m[df_m["nome"]==mun].iloc[0]["id"]) if mun else None
                    c1,c2=st.columns(2)
                    with c1: dt=st.date_input("Data da coleta",value=date.today(),key="pcl_lve_dt")
                    with c2: ponto=st.text_input("Ponto de coleta",key="pcl_lve_ponto")
                    c1,c2,c3=st.columns(3)
                    with c1: ambiente=st.text_input("Ambiente",key="pcl_lve_amb")
                    with c2: metodo=st.text_input("Método de coleta",key="pcl_lve_met")
                    with c3: qtd=st.number_input("Quantidade",min_value=0,value=0,step=1,key="pcl_lve_qtd")
                    c1,c2=st.columns(2)
                    with c1: especie=st.text_input("Espécie identificada",key="pcl_lve_esp")
                    with c2: sexo=st.selectbox("Sexo",["Não informado","Macho","Fêmea"],key="pcl_lve_sexo")
                    resultado=st.text_input("Resultado / identificação laboratorial",key="pcl_lve_res")
                    obs=st.text_area("Observações",key="pcl_lve_obs")
                    if st.button("Salvar coleta entomológica",type="primary",key="pcl_lve_save"):
                        if not mid: st.warning("Selecione o município.")
                        else:
                            cur=conn.cursor(); cur.execute("INSERT INTO pcl_lv_entomologia (estado_id,municipio_id,data_coleta,ponto_coleta,ambiente,metodo,quantidade,especie,sexo,resultado,observacao) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(eid,mid,dt,ponto.strip() or None,ambiente.strip() or None,metodo.strip() or None,qtd,especie.strip() or None,sexo,resultado.strip() or None,obs.strip() or None)); conn.commit(); cur.close(); st.success("Coleta registrada!")
                else:
                    df=pd.read_sql("SELECT id,data_coleta,ponto_coleta,ambiente,quantidade,especie,sexo,resultado FROM pcl_lv_entomologia ORDER BY id DESC LIMIT 500",conn); st.dataframe(df,use_container_width=True,hide_index=True)

            elif doenca == "LV" and menu_pcl == "Investigação":
                est,eid,_=pcl_estado("pcl_lv_i_est"); mun,df_m=pcl_municipio(eid,"pcl_lv_i_mun"); mid=int(df_m[df_m["nome"]==mun].iloc[0]["id"]) if mun else None
                tipo=st.selectbox("Tipo de investigação",["Epidemiológica","Local provável de infecção","Foco","Canina","Entomológica"],key="pcl_lvi_tipo")
                dt=st.date_input("Data da investigação",value=date.today(),key="pcl_lvi_dt"); ref=st.text_input("Referência / caso relacionado",key="pcl_lvi_ref")
                lpi=st.text_area("Local provável / descrição",key="pcl_lvi_lpi"); ach=st.text_area("Achados",key="pcl_lvi_ach"); medidas=st.text_area("Medidas adotadas",key="pcl_lvi_med"); resp=st.text_input("Responsável",key="pcl_lvi_resp")
                status=st.selectbox("Status",["Em andamento","Concluída","Encaminhada"],key="pcl_lvi_status")
                if st.button("Salvar investigação",type="primary",key="pcl_lvi_save"):
                    if not mid: st.warning("Selecione o município.")
                    else:
                        cur=conn.cursor(); cur.execute("INSERT INTO pcl_lv_investigacoes (estado_id,municipio_id,data_investigacao,tipo,referencia,local_provavel,achados,medidas_adotadas,responsavel,status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(eid,mid,dt,tipo,ref.strip() or None,lpi.strip() or None,ach.strip() or None,medidas.strip() or None,resp.strip() or None,status)); conn.commit(); cur.close(); st.success("Investigação registrada!")
                df=pd.read_sql("SELECT id,data_investigacao,tipo,referencia,status,criado_em FROM pcl_lv_investigacoes ORDER BY id DESC LIMIT 200",conn); st.dataframe(df,use_container_width=True,hide_index=True)

            elif doenca == "LV" and menu_pcl == "Ações de Controle":
                est,eid,_=pcl_estado("pcl_lv_a_est"); mun,df_m=pcl_municipio(eid,"pcl_lv_a_mun"); mid=int(df_m[df_m["nome"]==mun].iloc[0]["id"]) if mun else None
                dt=st.date_input("Data da ação",value=date.today(),key="pcl_lva_dt"); tipo=st.selectbox("Tipo de ação",["Controle vetorial","Ação sobre reservatório","Manejo ambiental","Educação em saúde","Ação integrada","Outra"],key="pcl_lva_tipo"); publico=st.text_input("Público / área atingida",key="pcl_lva_pub"); qtd=st.number_input("Quantidade",min_value=0,value=0,step=1,key="pcl_lva_qtd"); desc=st.text_area("Descrição",key="pcl_lva_desc"); resp=st.text_input("Responsável",key="pcl_lva_resp")
                if st.button("Registrar ação",type="primary",key="pcl_lva_save"):
                    if not mid: st.warning("Selecione o município.")
                    else:
                        cur=conn.cursor(); cur.execute("INSERT INTO pcl_lv_acoes (estado_id,municipio_id,data_acao,tipo,publico_alvo,quantidade,descricao,responsavel) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",(eid,mid,dt,tipo,publico.strip() or None,qtd,desc.strip() or None,resp.strip() or None)); conn.commit(); cur.close(); st.success("Ação registrada!")

            elif doenca == "LV" and menu_pcl == "Vigilância do Óbito":
                est,eid,_=pcl_estado("pcl_lv_o_est"); mun,df_m=pcl_municipio(eid,"pcl_lv_o_mun"); mid=int(df_m[df_m["nome"]==mun].iloc[0]["id"]) if mun else None
                nome=st.text_input("Nome",key="pcl_lvo_nome"); dt=st.date_input("Data do óbito",value=date.today(),key="pcl_lvo_dt"); com=st.date_input("Data da comunicação",value=date.today(),key="pcl_lvo_com"); unidade=st.text_input("Unidade de investigação",key="pcl_lvo_un")
                ubs=st.text_area("Investigação UBS/UPA",key="pcl_lvo_ubs"); intern=st.text_area("Investigação no estabelecimento de internação",key="pcl_lvo_int"); dom=st.text_area("Entrevista domiciliar",key="pcl_lvo_dom"); conc=st.text_area("Conclusão",key="pcl_lvo_conc"); status=st.selectbox("Status",["Em investigação","Concluída"],key="pcl_lvo_status")
                if st.button("Registrar vigilância do óbito",type="primary",key="pcl_lvo_save"):
                    if not nome.strip() or not mid: st.warning("Informe o nome e selecione o município.")
                    else:
                        cur=conn.cursor(); cur.execute("INSERT INTO pcl_lv_obitos (estado_id,municipio_id,nome,data_obito,comunicacao,unidade_investigacao,investigacao_ubs,investigacao_internacao,entrevista_domiciliar,conclusao,status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(eid,mid,nome.strip(),dt,com,unidade.strip() or None,ubs.strip() or None,intern.strip() or None,dom.strip() or None,conc.strip() or None,status)); conn.commit(); cur.close(); st.success("Registro de óbito salvo!")
                df=pd.read_sql("SELECT id,nome,data_obito,comunicacao,status,criado_em FROM pcl_lv_obitos ORDER BY id DESC LIMIT 200",conn); st.dataframe(df,use_container_width=True,hide_index=True)

            elif doenca == "LT":
                if menu_pcl == "Vigilância de Casos":
                    est,eid,_=pcl_estado("pcl_lt_c_est"); mun,df_m=pcl_municipio(eid,"pcl_lt_c_mun"); mid=int(df_m[df_m["nome"]==mun].iloc[0]["id"]) if mun else None
                    nome=st.text_input("Nome do caso *",key="pcl_ltc_nome"); nasc=st.date_input("Data de nascimento",value=date(2000,1,1),key="pcl_ltc_nasc"); sexo=st.selectbox("Sexo",["Não informado","Masculino","Feminino"],key="pcl_ltc_sexo"); dt=st.date_input("Data da notificação",value=date.today(),key="pcl_ltc_dt"); forma=st.selectbox("Forma clínica",["Cutânea","Mucosa","Cutânea difusa","Outra"],key="pcl_ltc_forma"); lpi=st.text_area("Local provável de infecção",key="pcl_ltc_lpi"); diag=st.text_input("Diagnóstico / método",key="pcl_ltc_diag"); res=st.text_input("Resultado",key="pcl_ltc_res"); trat=st.text_input("Tratamento",key="pcl_ltc_trat"); evol=st.selectbox("Evolução",["Em acompanhamento","Cura","Abandono","Transferência","Óbito","Outro"],key="pcl_ltc_evol"); obs=st.text_area("Observações",key="pcl_ltc_obs")
                    if st.button("Salvar caso LT",type="primary",key="pcl_ltc_save"):
                        if not nome.strip() or not mid: st.warning("Informe o nome e selecione o município.")
                        else:
                            cur=conn.cursor(); cur.execute("INSERT INTO pcl_lt_casos (estado_id,municipio_id,nome,data_nascimento,sexo,data_notificacao,forma_clinica,local_infeccao,diagnostico,resultado,tratamento,evolucao,observacao) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(eid,mid,nome.strip(),nasc,sexo,dt,forma,lpi.strip() or None,diag.strip() or None,res.strip() or None,trat.strip() or None,evol,obs.strip() or None)); conn.commit(); cur.close(); st.success("Caso de LT registrado!")
                    df=pd.read_sql("SELECT id,nome,data_notificacao,forma_clinica,diagnostico,evolucao,criado_em FROM pcl_lt_casos ORDER BY id DESC LIMIT 500",conn); st.dataframe(df,use_container_width=True,hide_index=True)
                elif menu_pcl == "Investigação":
                    est,eid,_=pcl_estado("pcl_lt_i_est"); mun,df_m=pcl_municipio(eid,"pcl_lt_i_mun"); mid=int(df_m[df_m["nome"]==mun].iloc[0]["id"]) if mun else None; dt=st.date_input("Data da investigação",value=date.today(),key="pcl_lti_dt"); ref=st.text_input("Caso / referência",key="pcl_lti_ref"); lpi=st.text_area("Local provável",key="pcl_lti_lpi"); ach=st.text_area("Achados",key="pcl_lti_ach"); med=st.text_area("Medidas adotadas",key="pcl_lti_med"); resp=st.text_input("Responsável",key="pcl_lti_resp"); status=st.selectbox("Status",["Em andamento","Concluída","Encaminhada"],key="pcl_lti_status")
                    if st.button("Salvar investigação LT",type="primary",key="pcl_lti_save"):
                        if not mid: st.warning("Selecione o município.")
                        else:
                            cur=conn.cursor(); cur.execute("INSERT INTO pcl_lt_investigacoes (estado_id,municipio_id,data_investigacao,referencia,local_provavel,achados,medidas_adotadas,responsavel,status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",(eid,mid,dt,ref.strip() or None,lpi.strip() or None,ach.strip() or None,med.strip() or None,resp.strip() or None,status)); conn.commit(); cur.close(); st.success("Investigação LT registrada!")
                    df=pd.read_sql("SELECT id,data_investigacao,referencia,status,criado_em FROM pcl_lt_investigacoes ORDER BY id DESC LIMIT 200",conn); st.dataframe(df,use_container_width=True,hide_index=True)
                elif menu_pcl == "Acompanhamento":
                    df=pd.read_sql("SELECT id,nome,data_notificacao,forma_clinica,evolucao FROM pcl_lt_casos ORDER BY id DESC LIMIT 500",conn)
                    if df.empty: st.info("Nenhum caso de LT cadastrado.")
                    else:
                        caso=st.selectbox("Caso",[f"#{int(r.id)} — {r.nome}" for _,r in df.iterrows()],key="pcl_lta_caso"); caso_id=int(caso.split("—")[0].replace("#","").strip()); dt=st.date_input("Data do acompanhamento",value=date.today(),key="pcl_lta_dt"); trat=st.text_input("Tratamento",key="pcl_lta_trat"); evol=st.selectbox("Evolução",["Em acompanhamento","Cura","Abandono","Transferência","Óbito","Outro"],key="pcl_lta_evol"); res=st.text_input("Resultado",key="pcl_lta_res"); obs=st.text_area("Observações",key="pcl_lta_obs")
                        if st.button("Registrar acompanhamento",type="primary",key="pcl_lta_save"):
                            cur=conn.cursor(); cur.execute("INSERT INTO pcl_lt_acompanhamentos (caso_id,data_acompanhamento,tratamento,evolucao,resultado,observacao) VALUES (%s,%s,%s,%s,%s,%s)",(caso_id,dt,trat.strip() or None,evol,res.strip() or None,obs.strip() or None)); conn.commit(); cur.close(); st.success("Acompanhamento registrado!")
                elif menu_pcl == "Vigilância Entomológica":
                    est,eid,_=pcl_estado("pcl_lt_e_est"); mun,df_m=pcl_municipio(eid,"pcl_lt_e_mun"); mid=int(df_m[df_m["nome"]==mun].iloc[0]["id"]) if mun else None; dt=st.date_input("Data da coleta",value=date.today(),key="pcl_lte_dt"); ponto=st.text_input("Ponto de coleta",key="pcl_lte_ponto"); amb=st.text_input("Ambiente",key="pcl_lte_amb"); met=st.text_input("Método",key="pcl_lte_met"); qtd=st.number_input("Quantidade",min_value=0,value=0,step=1,key="pcl_lte_qtd"); esp=st.text_input("Espécie",key="pcl_lte_esp"); sexo=st.selectbox("Sexo",["Não informado","Macho","Fêmea"],key="pcl_lte_sexo"); res=st.text_input("Resultado",key="pcl_lte_res"); obs=st.text_area("Observações",key="pcl_lte_obs")
                    if st.button("Salvar coleta LT",type="primary",key="pcl_lte_save"):
                        if not mid: st.warning("Selecione o município.")
                        else:
                            cur=conn.cursor(); cur.execute("INSERT INTO pcl_lt_entomologia (estado_id,municipio_id,data_coleta,ponto_coleta,ambiente,metodo,quantidade,especie,sexo,resultado,observacao) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(eid,mid,dt,ponto.strip() or None,amb.strip() or None,met.strip() or None,qtd,esp.strip() or None,sexo,res.strip() or None,obs.strip() or None)); conn.commit(); cur.close(); st.success("Coleta LT registrada!")
                elif menu_pcl == "Ações de Controle":
                    est,eid,_=pcl_estado("pcl_lt_a_est"); mun,df_m=pcl_municipio(eid,"pcl_lt_a_mun"); mid=int(df_m[df_m["nome"]==mun].iloc[0]["id"]) if mun else None; dt=st.date_input("Data da ação",value=date.today(),key="pcl_lta_dt2"); tipo=st.selectbox("Tipo de ação",["Controle vetorial","Manejo ambiental","Educação em saúde","Ação integrada","Outra"],key="pcl_lta_tipo"); desc=st.text_area("Descrição",key="pcl_lta_desc"); resp=st.text_input("Responsável",key="pcl_lta_resp")
                    if st.button("Registrar ação LT",type="primary",key="pcl_lta_save2"):
                        if not mid: st.warning("Selecione o município.")
                        else:
                            cur=conn.cursor(); cur.execute("INSERT INTO pcl_lt_acoes (estado_id,municipio_id,data_acao,tipo,descricao,responsavel) VALUES (%s,%s,%s,%s,%s,%s)",(eid,mid,dt,tipo,desc.strip() or None,resp.strip() or None)); conn.commit(); cur.close(); st.success("Ação LT registrada!")

            if menu_pcl == "Relatórios e Indicadores":
                if doenca == "LV":
                    tabelas=[("Casos humanos","pcl_lv_humana"),("Registros caninos","pcl_lv_canina"),("Coletas entomológicas","pcl_lv_entomologia"),("Investigações","pcl_lv_investigacoes"),("Ações de controle","pcl_lv_acoes"),("Óbitos","pcl_lv_obitos")]
                else:
                    tabelas=[("Casos LT","pcl_lt_casos"),("Investigações","pcl_lt_investigacoes"),("Acompanhamentos","pcl_lt_acompanhamentos"),("Coletas entomológicas","pcl_lt_entomologia"),("Ações de controle","pcl_lt_acoes")]
                st.markdown("### Resumo operacional")
                cols=st.columns(min(4,len(tabelas)))
                for i,(label,tabela) in enumerate(tabelas):
                    try: total=int(pd.read_sql(f"SELECT COUNT(*) AS n FROM {tabela}",conn).iloc[0]["n"])
                    except Exception: total=0
                    with cols[i % len(cols)]: st.metric(label,total)
                st.markdown("### Últimos registros")
                for label,tabela in tabelas:
                    try:
                        df=pd.read_sql(f"SELECT * FROM {tabela} ORDER BY id DESC LIMIT 20",conn)
                        if not df.empty:
                            with st.expander(label): st.dataframe(df,use_container_width=True,hide_index=True)
                    except Exception: pass

    conn.close()

elif st.session_state.pagina == "PCE":
    imagem_pce = localizar_imagem_modulo("pce", "esquistossomose")
    if st.session_state.get("modulo_inicio", False) and imagem_pce:
        st.image(imagem_pce, use_container_width=True)
        st.markdown("---")
    st.markdown('<div class="module-header"><h1>PCE</h1><p>Programa de Controle da Esquistossomose</p></div>', unsafe_allow_html=True)
    menu_atual = st.session_state.get("pce_menu")

    # A navegação do conteúdo acompanha a mesma hierarquia do menu lateral.
    if menu_atual == "Cadastro":
        st.subheader("Cadastro")
        st.info("Selecione uma função de cadastro no menu lateral.")
        st.stop()

    if menu_atual == "Atividades":
        st.subheader("Atividades")
        st.info("Selecione uma atividade no menu lateral.")
        st.stop()

    conn = conectar_banco()
    if not conn: st.stop()
    df_estados_cad = carregar_estados_cadastro(conn, usuario)

    def seletor_estado_pce(key):
        if nivel == "Federal":
            return st.selectbox("Estado", ["Selecione..."] + df_estados_cad["nome"].tolist(), key=key)
        nome = df_estados_cad.iloc[0]["nome"] if not df_estados_cad.empty else "—"
        st.selectbox("Estado", [nome], key=key, disabled=True)
        return nome

    def estado_id_pce(nome, df_ref):
        if not nome or nome == "Selecione...": return None
        row = df_ref[df_ref["nome"] == nome]
        return int(row.iloc[0]["id"]) if not row.empty else None

    if menu_atual in ("PCE-101 — Coproscopia/Tratamento", "PCE-102A — Coleção Hídrica", "PCE-102 — Pesquisa Malacológica"):
        pce_prod = menu_atual

        if pce_prod == "PCE-101 — Coproscopia/Tratamento":
            st.subheader("PCE-101 — Coproscopia / Tratamento")
            operacao = st.session_state.get("pce_sub") or "Inclusão"

            try:
                cur = conn.cursor()
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS pce101_registros (
                        id BIGSERIAL PRIMARY KEY,
                        estado_id BIGINT,
                        municipio_id BIGINT,
                        localidade_id BIGINT,
                        controle VARCHAR(60) NOT NULL,
                        categoria VARCHAR(100),
                        fase VARCHAR(20),
                        data_coproscopia DATE,
                        inquerito VARCHAR(40),
                        tratamento VARCHAR(40),
                        recipientes_distribuidos INTEGER DEFAULT 0,
                        exames_realizados INTEGER DEFAULT 0,
                        exames_positivos INTEGER DEFAULT 0,
                        pessoas_tratar INTEGER DEFAULT 0,
                        pessoas_tratadas INTEGER DEFAULT 0,
                        positivos_masculino INTEGER DEFAULT 0,
                        positivos_feminino INTEGER DEFAULT 0,
                        ovos_1_4 INTEGER DEFAULT 0,
                        ovos_5_16 INTEGER DEFAULT 0,
                        ovos_17_64 INTEGER DEFAULT 0,
                        ovos_65_mais INTEGER DEFAULT 0,
                        helmintos_outros TEXT,
                        nao_tratados INTEGER DEFAULT 0,
                        motivo_nao_tratamento TEXT,
                        status VARCHAR(20) DEFAULT 'Ativo',
                        criado_por BIGINT,
                        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS pce101_amostras (
                        id BIGSERIAL PRIMARY KEY,
                        registro_id BIGINT NOT NULL REFERENCES pce101_registros(id) ON DELETE CASCADE,
                        numero_amostra INTEGER NOT NULL,
                        numero_casa VARCHAR(50),
                        data_nascimento DATE,
                        sexo VARCHAR(20),
                        coleta VARCHAR(30),
                        resultado VARCHAR(100),
                        tratamento VARCHAR(50),
                        motivo TEXT,
                        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(registro_id, numero_amostra)
                    )
                """)
                conn.commit()
                cur.close()
            except Exception as e:
                conn.rollback()
                st.error(f"Não foi possível preparar o PCE-101: {e}")
                st.stop()

            if operacao == "Consulta":
                st.markdown("### Registros PCE-101")
                try:
                    df = pd.read_sql("""
                        SELECT r.id, r.controle, m.nome AS municipio, l.nome AS localidade,
                               r.categoria, r.fase, r.data_coproscopia, r.inquerito,
                               r.tratamento, r.exames_realizados, r.exames_positivos, r.status
                        FROM pce101_registros r
                        LEFT JOIN municipios m ON m.id = r.municipio_id
                        LEFT JOIN localidades l ON l.id = r.localidade_id
                        ORDER BY r.id DESC LIMIT 500
                    """, conn)
                    st.dataframe(df if not df.empty else pd.DataFrame(), use_container_width=True, hide_index=True)
                except Exception as e:
                    st.error(f"Erro ao consultar PCE-101: {e}")
            else:
                registro_id = None
                registro_existente = None
                if operacao == "Alteração":
                    try:
                        df_reg = pd.read_sql("""
                            SELECT r.id, r.controle, m.nome AS municipio, l.nome AS localidade
                            FROM pce101_registros r
                            LEFT JOIN municipios m ON m.id=r.municipio_id
                            LEFT JOIN localidades l ON l.id=r.localidade_id
                            WHERE r.status <> 'Excluído'
                            ORDER BY r.id DESC LIMIT 500
                        """, conn)
                    except Exception:
                        df_reg = pd.DataFrame()
                    if df_reg.empty:
                        st.info("Ainda não existem registros PCE-101 para alterar.")
                        st.stop()
                    opcoes = [f"#{int(r.id)} — Controle {r.controle} | {r.municipio or '-'} | {r.localidade or '-'}" for r in df_reg.itertuples()]
                    escolhido = st.selectbox("Registro PCE-101", opcoes, key="pce101_reg_sel")
                    registro_id = int(escolhido.split("—")[0].replace("#", "").strip())
                    registro_existente = pd.read_sql("SELECT * FROM pce101_registros WHERE id=%s", conn, params=(registro_id,)).iloc[0].to_dict()

                est = seletor_estado_pce("pce101_est")
                eid = estado_id_pce(est, df_estados_cad)
                df_mun = municipios_por_estado(conn, eid, False) if eid else pd.DataFrame(columns=["id", "nome", "codigo_ibge", "status", "regional"])
                nomes_mun = ["Selecione..."] + (df_mun["nome"].astype(str).tolist() if "nome" in df_mun.columns else [])
                valor_mun = str(registro_existente.get("municipio_id")) if registro_existente else None
                mun_sel = st.selectbox("Município", nomes_mun, key="pce101_mun") if not df_mun.empty else None
                mid = None
                if registro_existente and not df_mun.empty:
                    rowm = df_mun[df_mun["id"] == int(registro_existente["municipio_id"])]
                    if not rowm.empty:
                        idx = nomes_mun.index(rowm.iloc[0]["nome"])
                        st.session_state["pce101_mun"] = rowm.iloc[0]["nome"]
                        mun_sel = rowm.iloc[0]["nome"]
                if mun_sel and mun_sel != "Selecione...":
                    mid = int(df_mun[df_mun["nome"] == mun_sel].iloc[0]["id"])

                df_loc = pd.DataFrame(); loc_sel = None; lid = None
                if mid:
                    df_loc = pd.read_sql("SELECT id, nome FROM localidades WHERE municipio_id=%s AND (status IS NULL OR status='Ativa') ORDER BY nome", conn, params=(mid,))
                    if not df_loc.empty:
                        nomes_loc = ["Selecione..."] + df_loc["nome"].tolist()
                        loc_sel = st.selectbox("Localidade", nomes_loc, key="pce101_loc")
                        if registro_existente:
                            rowl = df_loc[df_loc["id"] == int(registro_existente["localidade_id"])]
                            if not rowl.empty:
                                st.session_state["pce101_loc"] = rowl.iloc[0]["nome"]
                                loc_sel = rowl.iloc[0]["nome"]
                        if loc_sel and loc_sel != "Selecione...":
                            lid = int(df_loc[df_loc["nome"] == loc_sel].iloc[0]["id"])

                def rv(campo, padrao=""):
                    if not registro_existente: return padrao
                    v = registro_existente.get(campo)
                    return padrao if v is None else str(v)

                c1, c2, c3 = st.columns(3)
                with c1: controle = st.text_input("Controle *", value=rv("controle"), key="pce101_controle")
                categorias = ["Selecione...", "Residencial", "Comercial", "Institucional", "Outra"]
                cat0 = rv("categoria", "Selecione...")
                with c2: categoria = st.selectbox("Categoria", categorias, index=categorias.index(cat0) if cat0 in categorias else 0, key="pce101_categoria")
                fases = ["Selecione...", "1 — LIT", "2 — AVR", "3 — VIG"]
                fase0 = rv("fase", "Selecione...")
                with c3: fase = st.selectbox("Fase", fases, index=fases.index(fase0) if fase0 in fases else 0, key="pce101_fase")

                c1, c2, c3 = st.columns(3)
                data0 = registro_existente.get("data_coproscopia") if registro_existente else date.today()
                if pd.isna(data0) if hasattr(pd, 'isna') else False: data0 = date.today()
                with c1: data_cop = st.date_input("Data da coproscopia", value=data0 or date.today(), key="pce101_data")
                inqs = ["Selecione...", "1 — Censitário", "2 — Amostragem", "3 — Busca Passiva"]
                inq0 = rv("inquerito", "Selecione...")
                with c2: inquerito = st.selectbox("Inquérito de coproscopia", inqs, index=inqs.index(inq0) if inq0 in inqs else 0, key="pce101_inq")
                trs = ["Selecione...", "1 — Total população", "2 — Positivos", "3 — Positivos/conviventes"]
                tr0 = rv("tratamento", "Selecione...")
                with c3: tratamento = st.selectbox("Tratamento", trs, index=trs.index(tr0) if tr0 in trs else 0, key="pce101_trat")

                st.markdown("### Produção")
                a,b,c,d,e = st.columns(5)
                with a: recip = st.number_input("Recipientes distribuídos", min_value=0, value=int(registro_existente.get("recipientes_distribuidos",0)) if registro_existente else 0, step=1, key="pce101_recip")
                with b: exames = st.number_input("Exames realizados", min_value=0, value=int(registro_existente.get("exames_realizados",0)) if registro_existente else 0, step=1, key="pce101_exames")
                with c: positivos = st.number_input("Exames positivos", min_value=0, value=int(registro_existente.get("exames_positivos",0)) if registro_existente else 0, step=1, key="pce101_pos")
                with d: tratar = st.number_input("Pessoas a tratar", min_value=0, value=int(registro_existente.get("pessoas_tratar",0)) if registro_existente else 0, step=1, key="pce101_tratar")
                with e: tratados = st.number_input("Pessoas tratadas", min_value=0, value=int(registro_existente.get("pessoas_tratadas",0)) if registro_existente else 0, step=1, key="pce101_tratados")

                st.markdown("### Positivos e carga parasitária")
                a,b,c,d = st.columns(4)
                with a: pos_m = st.number_input("Positivos — masculino", min_value=0, value=int(registro_existente.get("positivos_masculino",0)) if registro_existente else 0, step=1, key="pce101_posm")
                with b: pos_f = st.number_input("Positivos — feminino", min_value=0, value=int(registro_existente.get("positivos_feminino",0)) if registro_existente else 0, step=1, key="pce101_posf")
                with c: ovos_1 = st.number_input("Ovos — 1 a 4", min_value=0, value=int(registro_existente.get("ovos_1_4",0)) if registro_existente else 0, step=1, key="pce101_o1")
                with d: ovos_2 = st.number_input("Ovos — 5 a 16", min_value=0, value=int(registro_existente.get("ovos_5_16",0)) if registro_existente else 0, step=1, key="pce101_o2")
                a,b,c = st.columns(3)
                with a: ovos_3 = st.number_input("Ovos — 17 a 64", min_value=0, value=int(registro_existente.get("ovos_17_64",0)) if registro_existente else 0, step=1, key="pce101_o3")
                with b: ovos_4 = st.number_input("Ovos — 65 ou mais", min_value=0, value=int(registro_existente.get("ovos_65_mais",0)) if registro_existente else 0, step=1, key="pce101_o4")
                with c: nao_trat = st.number_input("Não tratados", min_value=0, value=int(registro_existente.get("nao_tratados",0)) if registro_existente else 0, step=1, key="pce101_naotrat")
                helm = st.text_area("Helmintoses / outros registros", value=rv("helmintos_outros"), key="pce101_helm")
                motivo = st.text_area("Motivo de não tratamento", value=rv("motivo_nao_tratamento"), key="pce101_motivo")

                st.markdown("### Amostras")
                qtd_amostras = int(exames)
                linhas = []
                existentes = {}
                if registro_id:
                    try:
                        df_a = pd.read_sql("SELECT * FROM pce101_amostras WHERE registro_id=%s ORDER BY numero_amostra", conn, params=(registro_id,))
                        existentes = {int(r.numero_amostra): r._asdict() for r in df_a.itertuples(index=False)}
                    except Exception:
                        existentes = {}
                if qtd_amostras > 0:
                    st.info(f"Quantidade obrigatória: {qtd_amostras} amostra(s), numeradas de 1 a {qtd_amostras}.")
                    for i in range(1, qtd_amostras + 1):
                        ex = existentes.get(i, {})
                        with st.expander(f"Amostra {i}", expanded=(i <= 3)):
                            x1,x2,x3,x4,x5 = st.columns(5)
                            with x1: casa = st.text_input("Nº da casa", value=str(ex.get("numero_casa") or ""), key=f"pce101_casa_{i}")
                            with x2: nasc = st.date_input("Nascimento", value=ex.get("data_nascimento") or date(2000,1,1), key=f"pce101_nasc_{i}")
                            sexos=["Selecione...","Masculino","Feminino","Ignorado"]; sx=str(ex.get("sexo") or "Selecione...")
                            with x3: sexo = st.selectbox("Sexo", sexos, index=sexos.index(sx) if sx in sexos else 0, key=f"pce101_sexo_{i}")
                            coletas=["Selecione...","Realizada","Não recolhida"]; co=str(ex.get("coleta") or "Selecione...")
                            with x4: coleta = st.selectbox("Coleta", coletas, index=coletas.index(co) if co in coletas else 0, key=f"pce101_coleta_{i}")
                            with x5: res = st.text_input("Resultado", value=str(ex.get("resultado") or ""), key=f"pce101_res_{i}")
                            t1,t2=st.columns(2)
                            tratam=["Selecione...","Tratado","Não tratado","Não se aplica"]; ta=str(ex.get("tratamento") or "Selecione...")
                            with t1: trat_am=st.selectbox("Tratamento da amostra", tratam, index=tratam.index(ta) if ta in tratam else 0, key=f"pce101_tratam_{i}")
                            with t2: mot_am=st.text_input("Motivo", value=str(ex.get("motivo") or ""), key=f"pce101_motam_{i}")
                            linhas.append((i,casa,nasc,sexo,coleta,res,trat_am,mot_am))
                else:
                    st.caption("Informe a quantidade de exames realizados para abrir as amostras.")

                if st.button("Salvar PCE-101", type="primary", use_container_width=True, key="pce101_salvar"):
                    erros=[]
                    if not mid: erros.append("Selecione o município.")
                    if not lid: erros.append("Selecione a localidade.")
                    if not controle.strip(): erros.append("Informe o controle.")
                    if categoria == "Selecione...": erros.append("Informe a categoria.")
                    if fase == "Selecione...": erros.append("Informe a fase.")
                    if inquerito == "Selecione...": erros.append("Informe o inquérito de coproscopia.")
                    if tratamento == "Selecione...": erros.append("Informe o tipo de tratamento.")
                    if exames < 1: erros.append("Informe pelo menos 1 exame realizado.")
                    if len(linhas) != qtd_amostras: erros.append("A quantidade de amostras não corresponde aos exames realizados.")
                    for row in linhas:
                        i, casa, nasc, sexo, coleta, res, trat_am, mot_am = row
                        if sexo == "Selecione..." or coleta == "Selecione...": erros.append(f"Complete a amostra {i}.")
                    if erros:
                        for er in erros: st.error(er)
                    else:
                        try:
                            cur=conn.cursor()
                            valores=(eid,mid,lid,controle.strip(),categoria,fase,data_cop,inquerito,tratamento,recip,exames,positivos,tratar,tratados,pos_m,pos_f,ovos_1,ovos_2,ovos_3,ovos_4,helm.strip() or None,nao_trat,motivo.strip() or None,int(usuario["id"]))
                            if registro_id:
                                cur.execute("""UPDATE pce101_registros SET estado_id=%s,municipio_id=%s,localidade_id=%s,controle=%s,categoria=%s,fase=%s,data_coproscopia=%s,inquerito=%s,tratamento=%s,recipientes_distribuidos=%s,exames_realizados=%s,exames_positivos=%s,pessoas_tratar=%s,pessoas_tratadas=%s,positivos_masculino=%s,positivos_feminino=%s,ovos_1_4=%s,ovos_5_16=%s,ovos_17_64=%s,ovos_65_mais=%s,helmintos_outros=%s,nao_tratados=%s,motivo_nao_tratamento=%s,atualizado_em=CURRENT_TIMESTAMP WHERE id=%s""", valores[:-1]+(registro_id,))
                                cur.execute("DELETE FROM pce101_amostras WHERE registro_id=%s", (registro_id,))
                                rid=registro_id
                            else:
                                cur.execute("""INSERT INTO pce101_registros (estado_id,municipio_id,localidade_id,controle,categoria,fase,data_coproscopia,inquerito,tratamento,recipientes_distribuidos,exames_realizados,exames_positivos,pessoas_tratar,pessoas_tratadas,positivos_masculino,positivos_feminino,ovos_1_4,ovos_5_16,ovos_17_64,ovos_65_mais,helmintos_outros,nao_tratados,motivo_nao_tratamento,criado_por) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""", valores)
                                rid=cur.fetchone()[0]
                            for i,casa,nasc,sexo,coleta,res,trat_am,mot_am in linhas:
                                cur.execute("INSERT INTO pce101_amostras (registro_id,numero_amostra,numero_casa,data_nascimento,sexo,coleta,resultado,tratamento,motivo) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", (rid,i,casa.strip() or None,nasc,sexo,coleta,res.strip() or None,trat_am,mot_am.strip() or None))
                            conn.commit(); cur.close()
                            st.success(f"PCE-101 salvo com sucesso: {qtd_amostras} amostra(s), numeradas de 1 a {qtd_amostras}.")
                        except Exception as e:
                            conn.rollback(); st.error(f"Erro ao gravar PCE-101: {e}")

        elif pce_prod == "PCE-102A — Coleção Hídrica":
            st.subheader("Cadastro de Coleção Hídrica")

            # Mantém a estrutura do PCE-102A e garante que o ID seja a
            # identificação única do registro para Alteração/Consulta.
            try:
                cur = conn.cursor()
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
                cur.close()
            except Exception as e:
                conn.rollback()
                st.error(f"Não foi possível preparar o cadastro de coleção hídrica: {e}")
                st.stop()

            operacao_col = st.session_state.get("pce_sub") or "Inclusão"

            # ----------------------------------------------------------
            # INCLUSÃO
            # ----------------------------------------------------------
            if operacao_col == "Inclusão":
                est = seletor_estado_pce("pce_col_est")
                eid = estado_id_pce(est, df_estados_cad)
                df_mun = municipios_por_estado(conn, eid, False) if eid else pd.DataFrame()
                mun_sel = (
                    st.selectbox(
                        "Município",
                        ["Selecione..."] + df_mun["nome"].astype(str).tolist(),
                        key="pce_col_mun"
                    )
                    if not df_mun.empty else None
                )

                df_loc = pd.DataFrame()
                loc_sel = None
                if mun_sel and mun_sel != "Selecione...":
                    mid = int(df_mun[df_mun["nome"] == mun_sel].iloc[0]["id"])
                    df_loc = pd.read_sql(
                        "SELECT id, nome FROM localidades WHERE municipio_id=%s "
                        "AND (status IS NULL OR status='Ativa') ORDER BY nome",
                        conn, params=(mid,)
                    )
                    if not df_loc.empty:
                        loc_sel = st.selectbox(
                            "Localidade",
                            ["Selecione..."] + df_loc["nome"].tolist(),
                            key="pce_col_loc"
                        )

                nome_col = st.text_input(
                    "Nome da coleção / ponto de água *", key="pce_col_nome"
                )
                tipo_col = st.selectbox(
                    "Tipo",
                    ["Rio", "Córrego", "Lagoa", "Açude", "Vala", "Poço",
                     "Reservatório", "Outro"],
                    key="pce_col_tipo"
                )
                obs_col = st.text_area("Observações", key="pce_col_obs")

                if st.button("Salvar coleção hídrica", type="primary", key="pce_col_btn"):
                    if not loc_sel or loc_sel == "Selecione..." or not nome_col.strip():
                        st.warning("Informe localidade e nome.")
                    else:
                        lid = int(df_loc[df_loc["nome"] == loc_sel].iloc[0]["id"])
                        try:
                            cur = conn.cursor()
                            cur.execute(
                                """
                                INSERT INTO public.colecoes_hidricas
                                    (localidade_id, nome, tipo, status, observacao)
                                VALUES (%s, %s, %s, 'Ativa', %s)
                                RETURNING id
                                """,
                                (lid, nome_col.strip(), tipo_col, obs_col.strip() or None)
                            )
                            novo_id = int(cur.fetchone()[0])
                            conn.commit()
                            cur.close()
                            st.success(
                                f"Coleção **{nome_col}** salva com sucesso. "
                                f"ID do cadastro: **{novo_id}**"
                            )
                            st.info(
                                f"Guarde o ID **{novo_id}**. Ele será usado para "
                                f"localizar este cadastro na opção **Alteração**."
                            )
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Erro ao gravar coleção hídrica: {e}")

                try:
                    df_c = pd.read_sql(
                        """
                        SELECT c.id, c.nome, c.tipo, c.status,
                               l.nome AS localidade, m.nome AS municipio
                        FROM public.colecoes_hidricas c
                        LEFT JOIN localidades l ON l.id = c.localidade_id
                        LEFT JOIN municipios m ON m.id = l.municipio_id
                        ORDER BY c.id DESC
                        LIMIT 1000
                        """,
                        conn
                    )
                    st.dataframe(
                        df_c if not df_c.empty else pd.DataFrame(),
                        use_container_width=True,
                        hide_index=True
                    )
                except Exception as e:
                    st.caption(str(e))

            # ----------------------------------------------------------
            # ALTERAÇÃO
            # Estado + Município + ID localizam o registro.
            # Depois, todos os dados existentes são carregados na ficha.
            # ----------------------------------------------------------
            elif operacao_col == "Alteração":
                st.markdown("### Alteração de Coleção Hídrica")
                st.caption(
                    "Informe Estado, Município e o ID do cadastro. "
                    "O sistema carregará os dados existentes para edição."
                )

                est_alt = seletor_estado_pce("pce_col_alt_est")
                eid_alt = estado_id_pce(est_alt, df_estados_cad)
                df_mun_alt = (
                    municipios_por_estado(conn, eid_alt, False)
                    if eid_alt else pd.DataFrame()
                )
                mun_alt = (
                    st.selectbox(
                        "Município",
                        ["Selecione..."] + df_mun_alt["nome"].astype(str).tolist(),
                        key="pce_col_alt_mun"
                    )
                    if not df_mun_alt.empty else None
                )

                id_col_alt = st.number_input(
                    "ID da coleção hídrica",
                    min_value=1,
                    step=1,
                    value=1,
                    format="%d",
                    key="pce_col_alt_id"
                )

                if st.button(
                    "Localizar coleção",
                    type="primary",
                    key="pce_col_alt_buscar"
                ):
                    if not mun_alt or mun_alt == "Selecione...":
                        st.warning("Selecione o município.")
                    else:
                        mid_alt = int(
                            df_mun_alt[df_mun_alt["nome"] == mun_alt].iloc[0]["id"]
                        )
                        try:
                            df_alt = pd.read_sql(
                                """
                                SELECT c.id, c.localidade_id, c.nome, c.tipo,
                                       c.status, c.observacao,
                                       l.nome AS localidade
                                FROM public.colecoes_hidricas c
                                LEFT JOIN localidades l ON l.id = c.localidade_id
                                WHERE c.id = %s
                                  AND l.municipio_id = %s
                                """,
                                conn,
                                params=(int(id_col_alt), mid_alt)
                            )
                            if df_alt.empty:
                                st.session_state["pce_col_alt_registro"] = None
                                st.warning(
                                    f"Nenhuma coleção encontrada para o ID "
                                    f"{int(id_col_alt)} nesse município."
                                )
                            else:
                                st.session_state["pce_col_alt_registro"] = (
                                    df_alt.iloc[0].to_dict()
                                )
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao localizar coleção hídrica: {e}")

                registro_alt = st.session_state.get("pce_col_alt_registro")

                if registro_alt:
                    st.success(
                        f"Cadastro localizado — ID **{int(registro_alt['id'])}**"
                    )

                    # Município do registro localizado.
                    mid_reg = None
                    try:
                        df_mreg = pd.read_sql(
                            "SELECT id, nome FROM municipios WHERE id = "
                            "(SELECT municipio_id FROM localidades WHERE id=%s)",
                            conn, params=(int(registro_alt["localidade_id"]),)
                        )
                        if not df_mreg.empty:
                            mid_reg = int(df_mreg.iloc[0]["id"])
                    except Exception:
                        pass

                    df_loc_alt = pd.DataFrame()
                    if mid_reg:
                        df_loc_alt = pd.read_sql(
                            """
                            SELECT id, nome
                            FROM localidades
                            WHERE municipio_id=%s
                              AND (status IS NULL OR status='Ativa')
                            ORDER BY nome
                            """,
                            conn, params=(mid_reg,)
                        )

                    nomes_loc = df_loc_alt["nome"].astype(str).tolist()
                    loc_original = str(registro_alt.get("localidade") or "")
                    idx_loc = (
                        nomes_loc.index(loc_original)
                        if loc_original in nomes_loc else 0
                    )
                    loc_alt = (
                        st.selectbox(
                            "Localidade",
                            nomes_loc,
                            index=idx_loc,
                            key=f"pce_col_alt_loc_{int(registro_alt['id'])}"
                        )
                        if nomes_loc else None
                    )

                    nome_alt = st.text_input(
                        "Nome da coleção / ponto de água *",
                        value=str(registro_alt.get("nome") or ""),
                        key=f"pce_col_alt_nome_{int(registro_alt['id'])}"
                    )

                    tipos_alt = [
                        "Rio", "Córrego", "Lagoa", "Açude", "Vala",
                        "Poço", "Reservatório", "Outro"
                    ]
                    tipo_original = str(registro_alt.get("tipo") or "")
                    idx_tipo = (
                        tipos_alt.index(tipo_original)
                        if tipo_original in tipos_alt else 0
                    )
                    tipo_alt = st.selectbox(
                        "Tipo",
                        tipos_alt,
                        index=idx_tipo,
                        key=f"pce_col_alt_tipo_{int(registro_alt['id'])}"
                    )

                    status_alt = st.selectbox(
                        "Status",
                        ["Ativa", "Inativa", "Arquivada"],
                        index=(
                            ["Ativa", "Inativa", "Arquivada"].index(
                                str(registro_alt.get("status") or "Ativa")
                            )
                            if str(registro_alt.get("status") or "Ativa")
                            in ["Ativa", "Inativa", "Arquivada"] else 0
                        ),
                        key=f"pce_col_alt_status_{int(registro_alt['id'])}"
                    )

                    obs_alt = st.text_area(
                        "Observações",
                        value=str(registro_alt.get("observacao") or ""),
                        key=f"pce_col_alt_obs_{int(registro_alt['id'])}"
                    )

                    if st.button(
                        "Atualizar coleção hídrica",
                        type="primary",
                        key=f"pce_col_alt_salvar_{int(registro_alt['id'])}"
                    ):
                        if not loc_alt or not nome_alt.strip():
                            st.warning("Informe localidade e nome.")
                        else:
                            lid_alt = int(
                                df_loc_alt[df_loc_alt["nome"] == loc_alt].iloc[0]["id"]
                            )
                            try:
                                cur = conn.cursor()
                                cur.execute(
                                    """
                                    UPDATE public.colecoes_hidricas
                                    SET localidade_id=%s,
                                        nome=%s,
                                        tipo=%s,
                                        status=%s,
                                        observacao=%s
                                    WHERE id=%s
                                    """,
                                    (
                                        lid_alt,
                                        nome_alt.strip(),
                                        tipo_alt,
                                        status_alt,
                                        obs_alt.strip() or None,
                                        int(registro_alt["id"])
                                    )
                                )
                                conn.commit()
                                cur.close()
                                st.success(
                                    f"Coleção ID **{int(registro_alt['id'])}** "
                                    "atualizada com sucesso."
                                )
                                st.session_state["pce_col_alt_registro"] = None
                                st.rerun()
                            except Exception as e:
                                conn.rollback()
                                st.error(
                                    f"Erro ao atualizar coleção hídrica: {e}"
                                )

            # ----------------------------------------------------------
            # CONSULTA
            # ----------------------------------------------------------
            elif operacao_col == "Consulta":
                st.markdown("### Consulta de Coleção Hídrica")
                est_con = seletor_estado_pce("pce_col_con_est")
                eid_con = estado_id_pce(est_con, df_estados_cad)
                df_mun_con = (
                    municipios_por_estado(conn, eid_con, False)
                    if eid_con else pd.DataFrame()
                )
                mun_con = (
                    st.selectbox(
                        "Município",
                        ["Todos"] + df_mun_con["nome"].astype(str).tolist(),
                        key="pce_col_con_mun"
                    )
                    if not df_mun_con.empty else "Todos"
                )
                id_con = st.number_input(
                    "ID da coleção (opcional)",
                    min_value=0,
                    step=1,
                    value=0,
                    format="%d",
                    key="pce_col_con_id"
                )

                try:
                    sql_con = """
                        SELECT c.id, c.nome, c.tipo, c.status,
                               l.nome AS localidade, m.nome AS municipio
                        FROM public.colecoes_hidricas c
                        LEFT JOIN localidades l ON l.id = c.localidade_id
                        LEFT JOIN municipios m ON m.id = l.municipio_id
                        WHERE 1=1
                    """
                    params_con = []
                    if eid_con:
                        sql_con += " AND m.estado_id=%s"
                        params_con.append(eid_con)
                    if mun_con and mun_con != "Todos":
                        mid_con = int(
                            df_mun_con[df_mun_con["nome"] == mun_con].iloc[0]["id"]
                        )
                        sql_con += " AND m.id=%s"
                        params_con.append(mid_con)
                    if int(id_con) > 0:
                        sql_con += " AND c.id=%s"
                        params_con.append(int(id_con))
                    sql_con += " ORDER BY c.id DESC LIMIT 1000"

                    df_cons = pd.read_sql(sql_con, conn, params=params_con)
                    st.dataframe(
                        df_cons if not df_cons.empty else pd.DataFrame(),
                        use_container_width=True,
                        hide_index=True
                    )
                except Exception as e:
                    st.error(f"Erro na consulta de coleções hídricas: {e}")

        elif pce_prod == "PCE-102 — Pesquisa Malacológica":
            st.subheader("Pesquisa Malacológica")
            sub = st.session_state.get("pce_sub") or "Nova"
            st.markdown("---")
            if sub == "Nova":
                est=seletor_estado_pce("pce_pm_est"); eid=estado_id_pce(est,df_estados_cad); df_mun=municipios_por_estado(conn,eid,False) if eid else pd.DataFrame()
                mun_sel=st.selectbox("Município",["Selecione..."]+df_mun["nome"].astype(str).tolist(),key="pce_pm_mun") if not df_mun.empty else None
                df_loc=pd.DataFrame(); loc_sel=None; lid=None; mid=None
                if mun_sel and mun_sel!="Selecione...":
                    mid=int(df_mun[df_mun["nome"]==mun_sel].iloc[0]["id"]); df_loc=pd.read_sql("SELECT id,nome FROM localidades WHERE municipio_id=%s AND (status IS NULL OR status='Ativa') ORDER BY nome",conn,params=(mid,))
                    if not df_loc.empty: loc_sel=st.selectbox("Localidade",["Selecione..."]+df_loc["nome"].tolist(),key="pce_pm_loc"); lid=int(df_loc[df_loc["nome"]==loc_sel].iloc[0]["id"]) if loc_sel and loc_sel!="Selecione..." else None
                colecao_id=None
                if lid:
                    try: df_col=pd.read_sql("SELECT id,nome,tipo FROM colecoes_hidricas WHERE localidade_id=%s AND (status IS NULL OR status='Ativa') ORDER BY nome",conn,params=(lid,))
                    except Exception: df_col=pd.DataFrame()
                    if not df_col.empty:
                        op_col=["Sem coleção específica"]+[f"#{int(r['id'])} — {r['nome']} ({r['tipo'] or '-'})" for _,r in df_col.iterrows()]; col_sel=st.selectbox("Coleção hídrica",op_col,key="pce_pm_col"); colecao_id=int(col_sel.split("—")[0].replace("#","").strip()) if col_sel!="Sem coleção específica" else None
                agente_id=None
                if mid:
                    try: df_ag=pd.read_sql("SELECT id,nome FROM agentes WHERE municipio_id=%s AND (ativo IS NULL OR ativo=TRUE) ORDER BY nome",conn,params=(mid,))
                    except Exception: df_ag=pd.DataFrame()
                    if not df_ag.empty:
                        op_ag=["Selecione..."]+[f"#{int(r['id'])} — {r['nome']}" for _,r in df_ag.iterrows()]; ag_sel=st.selectbox("Agente",op_ag,key="pce_pm_ag"); agente_id=int(ag_sel.split("—")[0].replace("#","").strip()) if ag_sel!="Selecione..." else None
                data_p=st.date_input("Data",value=date.today(),key="pce_pm_data"); especie=st.selectbox("Espécie",["Biomphalaria glabrata","Biomphalaria straminea","Biomphalaria tenagophila","Biomphalaria spp.","Outra"],key="pce_pm_esp"); metodo=st.selectbox("Método",["Concha / peneira","Pinça","Armadilha","Observação direta","Outro"],key="pce_pm_met")
                c1,c2=st.columns(2)
                with c1: coletados=st.number_input("Moluscos coletados",min_value=0,value=0,key="pce_pm_col_n")
                with c2: positivos=st.number_input("Moluscos positivos",min_value=0,value=0,key="pce_pm_pos")
                obs=st.text_area("Observações",key="pce_pm_obs")
                if st.button("Salvar pesquisa malacológica",type="primary",key="pce_pm_btn"):
                    if not lid: st.warning("Selecione a localidade.")
                    else:
                        try:
                            cur=conn.cursor(); cur.execute("INSERT INTO pesquisas_malacologicas (localidade_id,colecao_id,agente_id,data_pesquisa,especie,moluscos_coletados,moluscos_positivos,metodo,observacao,status,status_envio) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'Ativa','Rascunho')",(lid,colecao_id,agente_id,data_p,especie,coletados,positivos,metodo,obs.strip() or None)); conn.commit(); cur.close(); st.success("Pesquisa malacológica salva!")
                        except Exception as e: conn.rollback(); st.error(f"Erro: {e}")
            elif sub == "Listar":
                try:
                    df=pd.read_sql("SELECT p.id,p.data_pesquisa,p.especie,p.moluscos_coletados,p.moluscos_positivos,p.status,a.nome as agente,l.nome as localidade,m.nome as municipio FROM pesquisas_malacologicas p LEFT JOIN agentes a ON a.id=p.agente_id LEFT JOIN localidades l ON l.id=p.localidade_id LEFT JOIN municipios m ON m.id=l.municipio_id ORDER BY p.data_pesquisa DESC LIMIT 500",conn); st.dataframe(df if not df.empty else pd.DataFrame(),use_container_width=True,hide_index=True)
                except Exception as e: st.warning(str(e))
            else:
                try:
                    df_p=pd.read_sql("SELECT p.id,p.data_pesquisa,p.especie,p.status,m.nome as municipio FROM pesquisas_malacologicas p LEFT JOIN localidades l ON l.id=p.localidade_id LEFT JOIN municipios m ON m.id=l.municipio_id ORDER BY p.data_pesquisa DESC LIMIT 300",conn)
                    if not df_p.empty:
                        op=[f"#{int(r.id)} — {r.data_pesquisa} | {r.especie or '-'} [{r.status or 'Ativa'}]" for r in df_p.itertuples()]; esc=st.selectbox("Pesquisa",op,key="pce_arq_sel"); pid=int(esc.split("—")[0].replace("#","").strip()); row=df_p[df_p.id==pid].iloc[0]; atual=str(row.status) if row.status in ("Ativa","Arquivada") else "Ativa"; novo=st.selectbox("Status",["Ativa","Arquivada"],index=0 if atual=="Ativa" else 1,key="pce_arq_status")
                        if st.button("Salvar",type="primary",key="pce_arq_btn"):
                            cur=conn.cursor(); cur.execute("UPDATE pesquisas_malacologicas SET status=%s WHERE id=%s",(novo,pid)); conn.commit(); cur.close(); st.success("Atualizado!"); st.rerun()
                except Exception as e: st.error(f"Erro: {e}")

    elif menu_atual == "Relatórios":
        st.subheader("Relatórios do PCE")
        st.markdown(f"### {st.session_state.get('pce_rel_sub', 'PCE-101 Detalhado')}")
        st.info("A estrutura foi mapeada a partir do PCE antigo. A implementação detalhada de cada relatório será feita após fecharmos as rotinas de produção.")
        st.markdown("**PCE-101 Detalhado · PCE-101 Resumo · Malacologia · Atividades Educativas · Atividades de Saneamento · Sinopse · Localidade/Prevalência · Casos da Rede Básica · Relatórios Gerados**")
    elif menu_atual == "PCE-108 — Casos da Rede Básica":
        st.subheader("PCE-108 — Casos da Rede Básica")
        operacao = st.session_state.get("pce_sub") or "Inclusão"
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pce108_casos (
                id BIGSERIAL PRIMARY KEY, estado_id BIGINT, municipio_id BIGINT, controle VARCHAR(60),
                unidade_saude VARCHAR(200), pacs_psf VARCHAR(100), nome_paciente VARCHAR(200),
                data_nascimento DATE, sexo VARCHAR(20), municipio_residencia VARCHAR(200), localidade VARCHAR(200),
                data_exame DATE, data_inicio_trat DATE, data_fim_trat DATE, resultado_exame TEXT,
                tratamento VARCHAR(100), peso NUMERIC(7,2), medicamento VARCHAR(150), quantidade INTEGER DEFAULT 0,
                motivo_nao_tratamento TEXT, tratamento_outras_enteroparasitoses TEXT, medicamento_helmintos VARCHAR(150),
                medicamento_protozoario VARCHAR(150), status VARCHAR(30) DEFAULT 'Ativo', criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit(); cur.close()
        if operacao == "Consulta":
            try:
                df=pd.read_sql("SELECT id,controle,nome_paciente,sexo,data_exame,resultado_exame,tratamento,status FROM pce108_casos ORDER BY id DESC LIMIT 1000",conn)
                st.dataframe(df,use_container_width=True,hide_index=True)
            except Exception as e:
                st.error(f"Erro ao consultar PCE-108: {e}")

        elif operacao == "Alteração":
            st.markdown("### Localizar caso para alteração")
            est_alt=seletor_estado_pce("pce108_alt_est")
            eid_alt=estado_id_pce(est_alt,df_estados_cad)
            df_mun_alt=municipios_por_estado(conn,eid_alt,False) if eid_alt else pd.DataFrame()
            mun_alt=st.selectbox("Município",["Selecione..."]+df_mun_alt["nome"].astype(str).tolist(),key="pce108_alt_mun") if not df_mun_alt.empty else None
            controle_alt=st.text_input("Número do Controle",key="pce108_alt_controle")

            if st.button("Localizar caso",type="primary",use_container_width=True,key="pce108_alt_localizar"):
                if not eid_alt:
                    st.warning("Selecione o Estado.")
                elif not mun_alt or mun_alt == "Selecione...":
                    st.warning("Selecione o Município.")
                elif not controle_alt.strip():
                    st.warning("Informe o número do Controle.")
                else:
                    mid_alt=int(df_mun_alt[df_mun_alt["nome"]==mun_alt].iloc[0]["id"])
                    df_reg=pd.read_sql("""
                        SELECT id, estado_id, municipio_id, controle, unidade_saude, pacs_psf,
                               nome_paciente, data_nascimento, sexo, municipio_residencia, localidade,
                               data_exame, data_inicio_trat, data_fim_trat, resultado_exame,
                               tratamento, peso, medicamento, quantidade, motivo_nao_tratamento,
                               tratamento_outras_enteroparasitoses, medicamento_helmintos,
                               medicamento_protozoario, status
                        FROM pce108_casos
                        WHERE estado_id=%s AND municipio_id=%s AND controle=%s
                          AND COALESCE(status,'Ativo') <> 'Excluído'
                        ORDER BY id DESC LIMIT 1
                    """,conn,params=(eid_alt,mid_alt,controle_alt.strip()))
                    if df_reg.empty:
                        st.warning("Nenhum caso PCE-108 encontrado para o Estado, Município e Controle informados.")
                        st.session_state.pop("pce108_alt_id",None)
                    else:
                        r=df_reg.iloc[0]
                        st.session_state["pce108_alt_id"]=int(r["id"])
                        st.session_state.update({
                            "pce108_alt_unidade": r["unidade_saude"] or "",
                            "pce108_alt_pacs": r["pacs_psf"] or "",
                            "pce108_alt_nome": r["nome_paciente"] or "",
                            "pce108_alt_nasc": r["data_nascimento"] if pd.notna(r["data_nascimento"]) else date(2000,1,1),
                            "pce108_alt_sexo": r["sexo"] or "Não informado",
                            "pce108_alt_munres": r["municipio_residencia"] or "",
                            "pce108_alt_local": r["localidade"] or "",
                            "pce108_alt_dtex": r["data_exame"] if pd.notna(r["data_exame"]) else date.today(),
                            "pce108_alt_dtini": r["data_inicio_trat"] if pd.notna(r["data_inicio_trat"]) else date.today(),
                            "pce108_alt_dtfim": r["data_fim_trat"] if pd.notna(r["data_fim_trat"]) else date.today(),
                            "pce108_alt_result": [x.strip() for x in str(r["resultado_exame"] or "").split(",") if x.strip()],
                            "pce108_alt_trat": r["tratamento"] or "",
                            "pce108_alt_peso": float(r["peso"]) if pd.notna(r["peso"]) else 0.0,
                            "pce108_alt_med": r["medicamento"] or "",
                            "pce108_alt_qt": int(r["quantidade"] or 0),
                            "pce108_alt_motivo": r["motivo_nao_tratamento"] or "",
                            "pce108_alt_outras": r["tratamento_outras_enteroparasitoses"] or "",
                            "pce108_alt_helm": r["medicamento_helmintos"] or "",
                            "pce108_alt_proto": r["medicamento_protozoario"] or "",
                        })
                        st.rerun()

            rid_alt=st.session_state.get("pce108_alt_id")
            if rid_alt:
                st.markdown("### Dados do caso")
                c1,c2,c3=st.columns(3)
                with c1: st.text_input("Controle",value=controle_alt,key="pce108_alt_controle_edit",disabled=True)
                with c2: unidade=st.text_input("Unidade de Saúde",key="pce108_alt_unidade")
                with c3: pacs=st.text_input("PACS/PSF",key="pce108_alt_pacs")
                c1,c2,c3=st.columns(3)
                with c1: nome=st.text_input("Nome do paciente *",key="pce108_alt_nome")
                with c2: nasc=st.date_input("Data de nascimento",key="pce108_alt_nasc")
                with c3: sexo=st.selectbox("Sexo",["Não informado","Masculino","Feminino"],key="pce108_alt_sexo")
                c1,c2=st.columns(2)
                with c1: mun_res=st.text_input("Município de residência",key="pce108_alt_munres")
                with c2: local=st.text_input("Localidade",key="pce108_alt_local")
                c1,c2,c3=st.columns(3)
                with c1: dt_ex=st.date_input("Data do exame",key="pce108_alt_dtex")
                with c2: dt_ini=st.date_input("Data início tratamento",key="pce108_alt_dtini")
                with c3: dt_fim=st.date_input("Data fim tratamento",key="pce108_alt_dtfim")
                resultado_op=["Negativo","S. mansoni","Ascaris","Ancilostomídeos","Taenia","Trichuris","Enterobius","Strongyloides","Hymenolepis nana","Entamoeba histolytica","Entamoeba coli","Iodamoeba butschlii","Endolimax nana","Giardia lamblia","Outro"]
                resultado=st.multiselect("Resultado do exame",resultado_op,key="pce108_alt_result")
                c1,c2,c3,c4=st.columns(4)
                with c1: tratamento=st.text_input("Tratamento esquistossomose",key="pce108_alt_trat")
                with c2: peso=st.number_input("Peso",min_value=0.0,step=0.1,key="pce108_alt_peso")
                with c3: medicamento=st.text_input("Medicamento",key="pce108_alt_med")
                with c4: quantidade=st.number_input("Quantidade",min_value=0,step=1,key="pce108_alt_qt")
                motivo=st.text_area("Motivo de não tratamento",key="pce108_alt_motivo")
                outras=st.text_input("Tratamento de outras enteroparasitoses",key="pce108_alt_outras")
                c1,c2=st.columns(2)
                with c1: med_helm=st.text_input("Medicamento — helmintos",key="pce108_alt_helm")
                with c2: med_proto=st.text_input("Medicamento — protozoários",key="pce108_alt_proto")
                if st.button("Atualizar PCE-108",type="primary",use_container_width=True,key="pce108_alt_salvar"):
                    if not nome.strip():
                        st.warning("Informe o nome do paciente.")
                    else:
                        try:
                            cur=conn.cursor()
                            cur.execute("""UPDATE pce108_casos SET
                                unidade_saude=%s, pacs_psf=%s, nome_paciente=%s, data_nascimento=%s,
                                sexo=%s, municipio_residencia=%s, localidade=%s, data_exame=%s,
                                data_inicio_trat=%s, data_fim_trat=%s, resultado_exame=%s,
                                tratamento=%s, peso=%s, medicamento=%s, quantidade=%s,
                                motivo_nao_tratamento=%s, tratamento_outras_enteroparasitoses=%s,
                                medicamento_helmintos=%s, medicamento_protozoario=%s
                                WHERE id=%s""",
                                (unidade.strip() or None,pacs.strip() or None,nome.strip(),nasc,sexo,
                                 mun_res.strip() or None,local.strip() or None,dt_ex,dt_ini,dt_fim,
                                 ", ".join(resultado) if resultado else None,tratamento.strip() or None,
                                 peso,medicamento.strip() or None,quantidade,motivo.strip() or None,
                                 outras.strip() or None,med_helm.strip() or None,med_proto.strip() or None,rid_alt))
                            conn.commit(); cur.close()
                            st.success("PCE-108 atualizado com sucesso!")
                            st.session_state.pop("pce108_alt_id",None)
                            st.rerun()
                        except Exception as e:
                            conn.rollback(); st.error(f"Erro ao atualizar PCE-108: {e}")

        else:
            est=seletor_estado_pce("pce108_est"); eid=estado_id_pce(est,df_estados_cad); df_mun=municipios_por_estado(conn,eid,False) if eid else pd.DataFrame()
            mun_sel=st.selectbox("Município",["Selecione..."]+df_mun["nome"].astype(str).tolist(),key="pce108_mun") if not df_mun.empty else None
            c1,c2,c3=st.columns(3)
            with c1: controle=st.text_input("Controle",key="pce108_controle")
            with c2: unidade=st.text_input("Unidade de Saúde",key="pce108_unidade")
            with c3: pacs=st.text_input("PACS/PSF",key="pce108_pacs")
            c1,c2,c3=st.columns(3)
            with c1: nome=st.text_input("Nome do paciente *",key="pce108_nome")
            with c2: nasc=st.date_input("Data de nascimento",value=date(2000,1,1),key="pce108_nasc")
            with c3: sexo=st.selectbox("Sexo",["Não informado","Masculino","Feminino"],key="pce108_sexo")
            c1,c2=st.columns(2)
            with c1: mun_res=st.text_input("Município de residência",key="pce108_munres")
            with c2: local=st.text_input("Localidade",key="pce108_local")
            c1,c2,c3=st.columns(3)
            with c1: dt_ex=st.date_input("Data do exame",value=date.today(),key="pce108_dtex")
            with c2: dt_ini=st.date_input("Data início tratamento",value=date.today(),key="pce108_dtini")
            with c3: dt_fim=st.date_input("Data fim tratamento",value=date.today(),key="pce108_dtfim")
            resultado_op=["Negativo","S. mansoni","Ascaris","Ancilostomídeos","Taenia","Trichuris","Enterobius","Strongyloides","Hymenolepis nana","Entamoeba histolytica","Entamoeba coli","Iodamoeba butschlii","Endolimax nana","Giardia lamblia","Outro"]
            resultado=st.multiselect("Resultado do exame",resultado_op,key="pce108_result")
            c1,c2,c3,c4=st.columns(4)
            with c1: tratamento=st.text_input("Tratamento esquistossomose",key="pce108_trat")
            with c2: peso=st.number_input("Peso",min_value=0.0,value=0.0,step=0.1,key="pce108_peso")
            with c3: medicamento=st.text_input("Medicamento",key="pce108_med")
            with c4: quantidade=st.number_input("Quantidade",min_value=0,value=0,step=1,key="pce108_qt")
            motivo=st.text_area("Motivo de não tratamento",key="pce108_motivo")
            outras=st.text_input("Tratamento de outras enteroparasitoses",key="pce108_outras")
            c1,c2=st.columns(2)
            with c1: med_helm=st.text_input("Medicamento — helmintos",key="pce108_helm")
            with c2: med_proto=st.text_input("Medicamento — protozoários",key="pce108_proto")
            if operacao == "Inclusão" and st.button("Salvar PCE-108",type="primary",use_container_width=True,key="pce108_save"):
                if not nome.strip(): st.warning("Informe o nome do paciente.")
                elif not mun_sel or mun_sel=="Selecione...": st.warning("Selecione o município.")
                else:
                    mid=int(df_mun[df_mun["nome"]==mun_sel].iloc[0]["id"])
                    try:
                        cur=conn.cursor(); cur.execute("INSERT INTO pce108_casos (estado_id,municipio_id,controle,unidade_saude,pacs_psf,nome_paciente,data_nascimento,sexo,municipio_residencia,localidade,data_exame,data_inicio_trat,data_fim_trat,resultado_exame,tratamento,peso,medicamento,quantidade,motivo_nao_tratamento,tratamento_outras_enteroparasitoses,medicamento_helmintos,medicamento_protozoario) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(eid,mid,controle.strip() or None,unidade.strip() or None,pacs.strip() or None,nome.strip(),nasc,sexo,mun_res.strip() or None,local.strip() or None,dt_ex,dt_ini,dt_fim,", ".join(resultado) if resultado else None,tratamento.strip() or None,peso,medicamento.strip() or None,quantidade,motivo.strip() or None,outras.strip() or None,med_helm.strip() or None,med_proto.strip() or None)); conn.commit(); cur.close(); st.success("PCE-108 salvo com sucesso!")
                    except Exception as e: conn.rollback(); st.error(f"Erro ao salvar PCE-108: {e}")

    elif menu_atual == "Atividades Educativas":
        st.subheader("Atividades Educativas")
        sub=st.session_state.get("pce_sub") or "Nova"
        cur=conn.cursor(); cur.execute("""CREATE TABLE IF NOT EXISTS pce_atividades_educativas (id BIGSERIAL PRIMARY KEY, estado_id BIGINT, municipio_id BIGINT, competencia VARCHAR(20), area VARCHAR(100), fase VARCHAR(100), num_escolas INTEGER DEFAULT 0, grupos_comunitarios INTEGER DEFAULT 0, seminarios INTEGER DEFAULT 0, gincanas INTEGER DEFAULT 0, demonstracoes INTEGER DEFAULT 0, folder INTEGER DEFAULT 0, cartaz INTEGER DEFAULT 0, cartilha INTEGER DEFAULT 0, video INTEGER DEFAULT 0, filete INTEGER DEFAULT 0, pop_beneficiada INTEGER DEFAULT 0, pop_existente INTEGER DEFAULT 0, status VARCHAR(30) DEFAULT 'Ativo', criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""); conn.commit(); cur.close()
        if sub == "Listar":
            df=pd.read_sql("SELECT id,competencia,area,fase,num_escolas,grupos_comunitarios,seminarios,gincanas,pop_beneficiada FROM pce_atividades_educativas ORDER BY id DESC LIMIT 500",conn); st.dataframe(df,use_container_width=True,hide_index=True)
        else:
            est=seletor_estado_pce("pce_edu_est"); eid=estado_id_pce(est,df_estados_cad); df_mun=municipios_por_estado(conn,eid,False) if eid else pd.DataFrame(); mun_sel=st.selectbox("Município",["Selecione..."]+df_mun["nome"].astype(str).tolist(),key="pce_edu_mun") if not df_mun.empty else None
            c1,c2,c3=st.columns(3)
            with c1: competencia=st.text_input("Competência",key="pce_edu_comp")
            with c2: area=st.selectbox("Área",["Focal","Endêmica","Com potencial endêmico","Outra"],key="pce_edu_area")
            with c3: fase=st.text_input("Fase",key="pce_edu_fase")
            vals=[]
            labels=[("Número de escolas","num_escolas"),("Grupos comunitários","grupos_comunitarios"),("Seminários","seminarios"),("Gincanas","gincanas"),("Demonstrações","demonstracoes"),("Folder","folder"),("Cartaz","cartaz"),("Cartilha","cartilha"),("Vídeo","video"),("Filmete","filete"),("População beneficiada","pop_beneficiada"),("População existente","pop_existente")]
            cols=st.columns(3)
            for i,(lab,key) in enumerate(labels): vals.append(st.number_input(lab,min_value=0,value=0,step=1,key="pce_edu_"+key))
            if st.button("Salvar atividade educativa",type="primary",key="pce_edu_save"):
                if not mun_sel or mun_sel=="Selecione...": st.warning("Selecione o município.")
                else:
                    mid=int(df_mun[df_mun["nome"]==mun_sel].iloc[0]["id"]); data=dict(zip([x[1] for x in labels],vals)); cur=conn.cursor(); cur.execute("INSERT INTO pce_atividades_educativas (estado_id,municipio_id,competencia,area,fase,num_escolas,grupos_comunitarios,seminarios,gincanas,demonstracoes,folder,cartaz,cartilha,video,filete,pop_beneficiada,pop_existente) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(eid,mid,competencia,area,fase,*[data[x[1]] for x in labels])); conn.commit(); cur.close(); st.success("Atividade educativa salva!")

    elif menu_atual == "Atividades de Saneamento":
        st.subheader("Atividades de Saneamento")
        sub=st.session_state.get("pce_sub") or "Nova"
        cur=conn.cursor(); cur.execute("""CREATE TABLE IF NOT EXISTS pce_atividades_saneamento (id BIGSERIAL PRIMARY KEY, estado_id BIGINT, municipio_id BIGINT, localidade VARCHAR(200), competencia VARCHAR(20), area VARCHAR(100), fase VARCHAR(100), melhoria_domiciliar INTEGER DEFAULT 0, pop_existente INTEGER DEFAULT 0, melhoria_coletiva INTEGER DEFAULT 0, pop_atingida INTEGER DEFAULT 0, oficina_municipal_implantada INTEGER DEFAULT 0, status VARCHAR(30) DEFAULT 'Ativo', criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""); conn.commit(); cur.close()
        if sub == "Listar":
            df=pd.read_sql("SELECT id,competencia,localidade,area,fase,melhoria_domiciliar,melhoria_coletiva,pop_atingida FROM pce_atividades_saneamento ORDER BY id DESC LIMIT 500",conn); st.dataframe(df,use_container_width=True,hide_index=True)
        else:
            est=seletor_estado_pce("pce_san_est"); eid=estado_id_pce(est,df_estados_cad); df_mun=municipios_por_estado(conn,eid,False) if eid else pd.DataFrame(); mun_sel=st.selectbox("Município",["Selecione..."]+df_mun["nome"].astype(str).tolist(),key="pce_san_mun") if not df_mun.empty else None
            localidade=st.text_input("Localidade",key="pce_san_loc")
            c1,c2,c3=st.columns(3)
            with c1: competencia=st.text_input("Competência",key="pce_san_comp")
            with c2: area=st.selectbox("Área",["Focal","Endêmica","Com potencial endêmico","Outra"],key="pce_san_area")
            with c3: fase=st.text_input("Fase",key="pce_san_fase")
            c1,c2=st.columns(2)
            with c1: md=st.number_input("Melhoria domiciliar",min_value=0,value=0,step=1,key="pce_san_md")
            with c2: pe=st.number_input("População existente",min_value=0,value=0,step=1,key="pce_san_pe")
            c1,c2=st.columns(2)
            with c1: mc=st.number_input("Melhoria coletiva",min_value=0,value=0,step=1,key="pce_san_mc")
            with c2: pa=st.number_input("População atingida",min_value=0,value=0,step=1,key="pce_san_pa")
            oficina=st.number_input("Oficina municipal implantada",min_value=0,value=0,step=1,key="pce_san_of")
            if st.button("Salvar atividade de saneamento",type="primary",key="pce_san_save"):
                if not mun_sel or mun_sel=="Selecione...": st.warning("Selecione o município.")
                else:
                    mid=int(df_mun[df_mun["nome"]==mun_sel].iloc[0]["id"]); cur=conn.cursor(); cur.execute("INSERT INTO pce_atividades_saneamento (estado_id,municipio_id,localidade,competencia,area,fase,melhoria_domiciliar,pop_existente,melhoria_coletiva,pop_atingida,oficina_municipal_implantada) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(eid,mid,localidade.strip() or None,competencia,area,fase,md,pe,mc,pa,oficina)); conn.commit(); cur.close(); st.success("Atividade de saneamento salva!")

    elif menu_atual == "Etiquetas":
        sub = st.session_state.get("pce_sub") or "Gerar etiquetas"
        st.subheader("Etiquetas")
        if sub == "Gerar etiquetas":
            st.markdown("### Geração / impressão de etiquetas")
            est = seletor_estado_pce("pce_etq_est")
            eid = estado_id_pce(est, df_estados_cad)
            df_mun = municipios_por_estado(conn, eid, False) if eid else pd.DataFrame(columns=["id", "nome", "codigo_ibge", "status", "regional"])
            mun_sel = st.selectbox("Município", ["Selecione..."] + (df_mun["nome"].astype(str).tolist() if "nome" in df_mun.columns else []), key="pce_etq_mun")
            mid = int(df_mun[df_mun["nome"] == mun_sel].iloc[0]["id"]) if mun_sel != "Selecione..." and "nome" in df_mun.columns and not df_mun.empty else None
            proximo = obter_proximo_etiqueta(conn, mid) if mid else 1
            numero_inicial = st.text_input("Número inicial", value=f"{proximo:06d}", key="pce_etq_numero")
            numero_paginas = st.number_input("Número de páginas", min_value=0, value=0, step=1, key="pce_etq_paginas")
            total_etiquetas = int(numero_paginas) * 35
            st.markdown(f"**{numero_paginas} × 35 = {total_etiquetas} etiquetas**")
            linha_inicial = st.number_input("O formulário tem 7 (sete) linhas de etiquetas. A partir de qual linha será iniciada a impressão?", min_value=1, max_value=7, value=1, step=1, key="pce_etq_linha")
            if st.button("Gerar etiquetas", type="primary", use_container_width=True, key="pce_etq_gerar"):
                if not mid:
                    st.warning("Selecione o município.")
                elif total_etiquetas <= 0:
                    st.warning("Informe pelo menos 1 página.")
                else:
                    st.success(f"Preparadas {total_etiquetas} etiquetas, iniciando em {numero_inicial}, a partir da linha {linha_inicial}.")
                    st.caption("A impressão física será ligada ao modelo definitivo da etiqueta na próxima etapa, sem alterar a numeração já cadastrada.")
        else:
            st.markdown("### Consultar numeração de etiquetas")
            try:
                df = pd.read_sql("SELECT municipio_id, proximo_numero, atualizado_em FROM etiquetas_controle ORDER BY municipio_id", conn)
                st.dataframe(df, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"Erro ao consultar etiquetas: {e}")

    conn.close()
