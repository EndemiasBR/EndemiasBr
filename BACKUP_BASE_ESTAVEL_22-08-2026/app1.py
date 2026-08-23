import streamlit as st
import psycopg2
import pandas as pd
from datetime import date
import os
import re
import hashlib
import base64

st.set_page_config(page_title="EndemiasBR", page_icon="mosquito", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #006B3F 0%, #004d2c 100%); }
    [data-testid="stSidebar"] * { color: white !important; }
    [data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #009C3B, #007A2E); color: white !important;
        border: 1px solid #FFD700; border-radius: 10px; height: 48px; font-weight: 600;
    }
    .main { background: linear-gradient(180deg, #f0fff4 0%, #ffffff 100%); }
    h1, h2, h3 { color: #006B3F !important; }
    .module-header {
        padding: 18px 24px; border-radius: 12px; margin-bottom: 20px;
        background: linear-gradient(135deg, #006B3F, #009C3B); border-left: 6px solid #FFD700;
    }
    .module-header h1 { color: white !important; margin: 0; font-size: 28px; }
    .module-header p { margin: 4px 0 0 0; font-size: 15px; color: #FFD700 !important; }
    .card-header {
        padding: 16px 10px; text-align: center; font-size: 22px; font-weight: 700; color: #1a1a1a;
        border-radius: 12px 12px 0 0; background: linear-gradient(135deg, #FFD700, #F4C430);
        border-bottom: 3px solid #006B3F;
    }
    .card-subtitle { text-align: center; font-size: 16px; font-weight: 700; margin: 10px 0 6px 0; color: #006B3F; }
    .card-text {
        text-align: justify; font-size: 14.5px; line-height: 1.55; color: #333; padding: 12px 14px;
        border-radius: 0 0 12px 12px; min-height: 175px; background: linear-gradient(180deg, #e8f8ee, #c8ecd4);
        border: 1px solid #a8d5b5; border-top: none; box-sizing: border-box;
    }
    .auth-box {
        background: #f7fbf8; border: 1px solid #c8e6d0; border-radius: 8px; padding: 12px 16px;
        margin: 12px 0 18px 0; font-size: 14px; color: #333; line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

def conectar_banco():
    try:
        return psycopg2.connect(
            host="localhost", database="endemiasbr", user="postgres",
            password="Amor2806", port="5432", client_encoding="latin1"
        )
    except Exception as e:
        st.error(f"Erro ao conectar: {e}")
        return None

def so_numeros(t):
    return re.sub(r"\D", "", str(t or ""))

def formatar_cpf(cpf):
    n = so_numeros(cpf)
    return f"{n[:3]}.{n[3:6]}.{n[6:9]}-{n[9:]}" if len(n) == 11 else str(cpf or "")

def hash_senha(senha, cpf):
    return hashlib.sha256((str(senha) + so_numeros(cpf)).encode("utf-8")).hexdigest()

def senha_valida(senha):
    if len(senha) < 8:
        return False, "Mínimo 8 caracteres."
    if not re.search(r"[A-Z]", senha):
        return False, "Precisa de 1 letra maiúscula."
    if not re.search(r"[0-9]", senha):
        return False, "Precisa de 1 número."
    if not re.search(r"[^A-Za-z0-9]", senha):
        return False, "Precisa de 1 símbolo."
    return True, ""

def buscar_usuario_por_cpf(cpf):
    conn = conectar_banco()
    if not conn:
        return None
    try:
        df = pd.read_sql("""
            SELECT r.*, e.nome as estado_nome, e.sigla as estado_sigla
            FROM responsaveis r
            LEFT JOIN estados e ON e.id = r.estado_id
            WHERE regexp_replace(r.cpf, '[^0-9]', '', 'g') = %s AND r.ativo = TRUE
        """, conn, params=(so_numeros(cpf),))
        return None if df.empty else df.iloc[0].to_dict()
    except Exception as e:
        st.error(f"Erro ao buscar usuário: {e}")
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
        if df.empty:
            return None
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
        df = pd.read_sql(
            "SELECT nome, prefeito, secretario_saude, status FROM municipios WHERE id = %s",
            conn, params=(int(mun_id),)
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
    return pd.read_sql("""
        SELECT id, data_pesquisa, tipo_pesquisa, status
        FROM pesquisas_entomologicas
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
        df = pd.read_sql(
            "SELECT proximo_numero FROM etiquetas_controle WHERE municipio_id = %s",
            conn, params=(int(municipio_id),)
        )
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
        lista = [
            "Triatoma infestans", "Panstrongylus megistus", "Triatoma brasiliensis",
            "Triatoma sordida", "Rhodnius neglectus"
        ]
    if "Outra" not in lista:
        lista = lista + ["Outra"]
    return lista

def lista_inseticidas(conn):
    try:
        df = pd.read_sql(
            "SELECT nome FROM inseticidas WHERE ativo IS NULL OR ativo = TRUE ORDER BY nome",
            conn
        )
        return df["nome"].tolist() if not df.empty else ["K-Othrine", "Demand", "Actellic", "Ficam", "Outro"]
    except Exception:
        return ["K-Othrine", "Demand", "Actellic", "Ficam", "Outro"]

def form_campos_imovel(prefixo, valores=None):
    v = valores or {}
    identificacao = st.text_input(
        "Identificação / Endereço *",
        value=str(v.get("identificacao") or ""),
        key=f"{prefixo}_ident"
    )
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
    tipo = st.selectbox(
        "Tipo de imóvel", tipos,
        index=tipos.index(tipo_atual) if tipo_atual in tipos else 0,
        key=f"{prefixo}_tipo"
    )
    consts = ["Alvenaria", "Madeira", "Mista", "Taipa", "Outro", ""]
    tc_atual = str(v.get("tipo_construcao") or "")
    tipo_const = st.selectbox(
        "Tipo de construção", consts,
        index=consts.index(tc_atual) if tc_atual in consts else 0,
        key=f"{prefixo}_tconst"
    )
    sits = ["Existente", "Fechado", "Desabitado", "Em construção", "Demolido"]
    sit_atual = str(v.get("situacao") or "Existente")
    situacao = st.selectbox(
        "Situação", sits,
        index=sits.index(sit_atual) if sit_atual in sits else 0,
        key=f"{prefixo}_sit"
    )
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

for k, v in {"usuario": None, "pagina": "Inicio", "modulo": None, "forcar_troca_senha": False}.items():
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.usuario is None and not st.session_state.forcar_troca_senha:
    st.markdown(
        '<div class="module-header"><h1>EndemiasBR</h1><p>Sistema de Apoio à Vigilância de Endemias</p></div>',
        unsafe_allow_html=True
    )
    st.subheader("Acesso ao sistema")
    _, c2, _ = st.columns([1, 2, 1])
    with c2:
        cpf_in = st.text_input("CPF")
        senha_in = st.text_input("Senha", type="password")
        if st.button("Entrar", type="primary", use_container_width=True):
            if not so_numeros(cpf_in) or not senha_in:
                st.warning("Informe CPF e senha.")
            else:
                u = buscar_usuario_por_cpf(cpf_in)
                if u is None:
                    st.error("CPF não encontrado ou inativo.")
                elif hash_senha(senha_in, u["cpf"]) != (u.get("senha_hash") or "").lower():
                    st.error("Senha incorreta.")
                else:
                    st.session_state.usuario = u
                    st.session_state.forcar_troca_senha = bool(u.get("deve_trocar_senha"))
                    if not st.session_state.forcar_troca_senha:
                        st.session_state.pagina = "Inicio"
                    st.rerun()
    st.stop()

if st.session_state.forcar_troca_senha and st.session_state.usuario:
    u = st.session_state.usuario
    st.markdown('<div class="module-header"><h1>Troca de senha obrigatória</h1></div>', unsafe_allow_html=True)
    n1 = st.text_input("Nova senha", type="password")
    n2 = st.text_input("Confirmar", type="password")
    if st.button("Salvar nova senha", type="primary"):
        ok, msg = senha_valida(n1)
        if not ok:
            st.warning(msg)
        elif n1 != n2:
            st.warning("Senhas não conferem.")
        elif n1 == "12345678":
            st.warning("Não use a senha padrão.")
        else:
            conn = conectar_banco()
            if conn:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE responsaveis SET senha_hash=%s, deve_trocar_senha=FALSE WHERE id=%s",
                    (hash_senha(n1, u["cpf"]), int(u["id"]))
                )
                conn.commit()
                cur.close()
                conn.close()
                st.session_state.forcar_troca_senha = False
                st.rerun()
    st.stop()

usuario = st.session_state.usuario
nivel = usuario.get("nivel", "")

with st.sidebar:
    st.markdown("## EndemiasBR")
    st.markdown(f"**{usuario['nome']}**")
    st.caption(f"{formatar_cpf(usuario['cpf'])} | {nivel}")
    if usuario.get("estado_nome"):
        st.caption(f"Estado: {usuario['estado_nome']}")
    st.markdown("---")
    if st.session_state.modulo is None:
        if st.button("Início", use_container_width=True):
            st.session_state.pagina = "Inicio"
            st.rerun()
        st.markdown("### Administração")
        if st.button("Responsáveis", use_container_width=True):
            st.session_state.pagina = "Responsaveis"
            st.rerun()
        if st.button("Autoridades", use_container_width=True):
            st.session_state.pagina = "Autoridades"
            st.rerun()
        if st.button("Trocar minha senha", use_container_width=True):
            st.session_state.pagina = "TrocarSenha"
            st.rerun()
        st.markdown("### Módulos")
        if st.button("Sisloc", use_container_width=True):
            st.session_state.modulo = "Sisloc"
            st.session_state.pagina = "Sisloc"
            st.rerun()
        if st.button("PCDCh", use_container_width=True):
            st.session_state.modulo = "PCDCh"
            st.session_state.pagina = "PCDCh"
            st.rerun()
        if st.button("PCE", use_container_width=True):
            st.session_state.modulo = "PCE"
            st.session_state.pagina = "PCE"
            st.rerun()
    else:
        st.markdown(f"### {st.session_state.modulo}")
        if st.button("← Voltar", use_container_width=True):
            st.session_state.modulo = None
            st.session_state.pagina = "Inicio"
            st.rerun()
    st.markdown("---")
    if st.button("Sair", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

if st.session_state.pagina == "Inicio":
    st.title("EndemiasBR")
    st.markdown("### Sistema de Apoio à Vigilância de Endemias")
    st.write(f"Olá, **{usuario['nome']}** — **{nivel}**")
    if nivel == "Federal":
        st.success("Escopo: **Nacional** (cadastro e visualização)")
    elif usuario.get("estado_nome"):
        st.success(f"Cadastro: **{usuario['estado_nome']}** · Visualização: **todos os estados**")
    conn = conectar_banco()
    if conn:
        nac = carregar_nacional(conn)
        linhas = [
            f"<b>Presidente da República:</b> {nac['presidente']}",
            f"<b>Ministro da Saúde:</b> {nac['ministro_saude']}"
        ]
        estado_id = usuario.get("estado_id")
        if estado_id is not None and not (isinstance(estado_id, float) and pd.isna(estado_id)):
            info_est = carregar_estado_info(conn, int(estado_id))
            if info_est:
                linhas.append(f"<b>Governador ({info_est['sigla']}):</b> {info_est['governador']}")
                linhas.append(f"<b>Secretário(a) Estadual de Saúde:</b> {info_est['secretario_saude']}")
                if info_est["secretaria_nome"] and info_est["secretaria_nome"] != "—":
                    linhas.append(f"<b>Secretaria:</b> {info_est['secretaria_nome']}")
        mun_id = usuario.get("municipio_id")
        if mun_id is not None and not (isinstance(mun_id, float) and pd.isna(mun_id)):
            info_m = carregar_municipio_info(conn, int(mun_id))
            if info_m:
                linhas.append(f"<b>Prefeito(a):</b> {info_m['prefeito']}")
                linhas.append(f"<b>Secretário(a) Municipal de Saúde:</b> {info_m['secretario_saude']}")
        st.markdown(f'<div class="auth-box">{"<br>".join(linhas)}</div>', unsafe_allow_html=True)
        conn.close()
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="card-header">Sisloc</div>', unsafe_allow_html=True)
        st.markdown(imagem_card(caminho_imagem("sisloc.jpg", "SISLOC.jpg")), unsafe_allow_html=True)
        st.markdown('<div class="card-subtitle">Reconhecimento Geográfico</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="card-text">As localidades são a base de todo o trabalho de campo. '
            'É nelas que os agentes identificam imóveis, quarteirões e áreas de risco.</div>',
            unsafe_allow_html=True
        )
    with col2:
        st.markdown('<div class="card-header">PCDCh</div>', unsafe_allow_html=True)
        st.markdown(
            imagem_card(caminho_imagem("pcdch.jpg", "PCDCh.jpg", "barbeiro.jpg", "BARBEIRO.jpg", "chagas.jpg")),
            unsafe_allow_html=True
        )
        st.markdown('<div class="card-subtitle">Doença de Chagas</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="card-text">Transmitida principalmente pelas fezes do barbeiro infectado com o '
            '<i>Trypanosoma cruzi</i>.</div>',
            unsafe_allow_html=True
        )
    with col3:
        st.markdown('<div class="card-header">PCE</div>', unsafe_allow_html=True)
        st.markdown(
            imagem_card(caminho_imagem("pce.jpg", "PCE.jpg", "caramujo.jpg", "esquistossomose.jpg")),
            unsafe_allow_html=True
        )
        st.markdown('<div class="card-subtitle">Esquistossomose</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="card-text">Doença causada pelo parasito <i>Schistosoma mansoni</i>.</div>',
            unsafe_allow_html=True
        )

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
            if not ok:
                st.warning(msg)
            elif n1 != n2:
                st.warning("Senhas não conferem.")
            else:
                conn = conectar_banco()
                if conn:
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE responsaveis SET senha_hash=%s, deve_trocar_senha=FALSE WHERE id=%s",
                        (hash_senha(n1, usuario["cpf"]), int(usuario["id"]))
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                    st.success("Senha alterada!")

elif st.session_state.pagina == "Responsaveis":
    st.markdown('<div class="module-header"><h1>Responsáveis</h1></div>', unsafe_allow_html=True)
    conn = conectar_banco()
    if conn:
        try:
            df = pd.read_sql("""
                SELECT r.id, r.cpf, r.nome, r.nivel, e.nome as estado, r.ativo
                FROM responsaveis r
                LEFT JOIN estados e ON e.id = r.estado_id
                ORDER BY r.nivel, r.nome
            """, conn)
            if not df.empty:
                df["cpf"] = df["cpf"].apply(formatar_cpf)
                st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Erro: {e}")
        conn.close()

elif st.session_state.pagina == "Autoridades":
    st.markdown('<div class="module-header"><h1>Autoridades</h1></div>', unsafe_allow_html=True)
    conn = conectar_banco()
    if not conn:
        st.stop()
    nac = carregar_nacional(conn)
    if nivel == "Federal":
        st.subheader("Nível Federal")
        pres = st.text_input("Presidente da República", value=nac["presidente"] if nac["presidente"] != "—" else "")
        mini = st.text_input("Ministro da Saúde", value=nac["ministro_saude"] if nac["ministro_saude"] != "—" else "")
        if st.button("Salvar Federal", type="primary"):
            try:
                cur = conn.cursor()
                cur.execute("SELECT id FROM config_nacional ORDER BY id LIMIT 1")
                row = cur.fetchone()
                if row:
                    cur.execute(
                        "UPDATE config_nacional SET presidente=%s, ministro_saude=%s, atualizado_em=CURRENT_TIMESTAMP WHERE id=%s",
                        (pres.strip() or None, mini.strip() or None, row[0])
                    )
                else:
                    cur.execute(
                        "INSERT INTO config_nacional (presidente, ministro_saude) VALUES (%s,%s)",
                        (pres.strip() or None, mini.strip() or None)
                    )
                conn.commit()
                cur.close()
                st.success("Salvo!")
            except Exception as e:
                st.error(f"Erro: {e}")
        st.markdown("---")
    if nivel in ("Federal", "Estadual"):
        st.subheader("Nível Estadual")
        df_est = carregar_estados_cadastro(conn, usuario) if nivel == "Estadual" else carregar_estados_todos(conn)
        if not df_est.empty:
            est_nome = st.selectbox("Estado", df_est["nome"].tolist(), key="aut_est")
            eid = int(df_est[df_est["nome"] == est_nome].iloc[0]["id"])
            info = carregar_estado_info(conn, eid)
            gov = st.text_input(
                "Governador",
                value=(info["governador"] if info and info["governador"] != "—" else ""),
                key="aut_gov"
            )
            sec = st.text_input(
                "Secretário(a) Estadual de Saúde",
                value=(info["secretario_saude"] if info and info["secretario_saude"] != "—" else ""),
                key="aut_sec"
            )
            if st.button("Salvar Estado", type="primary"):
                try:
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE estados SET governador=%s, secretario_saude=%s WHERE id=%s",
                        (gov.strip() or None, sec.strip() or None, eid)
                    )
                    conn.commit()
                    cur.close()
                    st.success("Salvo!")
                except Exception as e:
                    st.error(f"Erro: {e}")
    if nivel in ("Federal", "Estadual", "Municipal"):
        st.subheader("Nível Municipal")
        df_est2 = carregar_estados_cadastro(conn, usuario) if nivel != "Federal" else carregar_estados_todos(conn)
        if not df_est2.empty:
            est2 = st.selectbox("Estado (município)", df_est2["nome"].tolist(), key="aut_est2")
            eid2 = int(df_est2[df_est2["nome"] == est2].iloc[0]["id"])
            df_m = municipios_por_estado(conn, eid2)
            if not df_m.empty:
                mun_n = st.selectbox("Município", df_m["nome"].tolist(), key="aut_mun")
                mid = int(df_m[df_m["nome"] == mun_n].iloc[0]["id"])
                info_m = carregar_municipio_info(conn, mid)
                pref = st.text_input(
                    "Prefeito(a)",
                    value=(info_m["prefeito"] if info_m and info_m["prefeito"] != "—" else ""),
                    key="aut_pref"
                )
                sec_m = st.text_input(
                    "Secretário(a) Municipal",
                    value=(info_m["secretario_saude"] if info_m and info_m["secretario_saude"] != "—" else ""),
                    key="aut_secm"
                )
                if st.button("Salvar Município", type="primary"):
                    try:
                        cur = conn.cursor()
                        cur.execute(
                            "UPDATE municipios SET prefeito=%s, secretario_saude=%s WHERE id=%s",
                            (pref.strip() or None, sec_m.strip() or None, mid)
                        )
                        conn.commit()
                        cur.close()
                        st.success("Salvo!")
                    except Exception as e:
                        st.error(f"Erro: {e}")
    conn.close()

elif st.session_state.pagina == "Sisloc":
    st.markdown('<div class="module-header"><h1>Sisloc</h1><p>Reconhecimento Geográfico</p></div>', unsafe_allow_html=True)
    menu_sisloc = st.radio(
        "Opções:",
        [
            "Navegação Hierárquica", "Localidades", "Cadastrar Localidade",
            "Editar / Arquivar Localidade", "Editar / Arquivar Município",
            "Imóveis", "Editar / Excluir Imóvel"
        ],
        horizontal=True,
        key="menu_sisloc_v3",
    )
    conn = conectar_banco()
    if not conn:
        st.stop()
    df_estados_view = carregar_estados_todos(conn)
    df_estados_cad = carregar_estados_cadastro(conn, usuario)

    if menu_sisloc == "Navegação Hierárquica":
        st.subheader("Navegação Hierárquica")
        try:
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                estado_sel = st.selectbox(
                    "Estado",
                    ["Selecione..."] + df_estados_view["nome"].tolist(),
                    key="nav_estado"
                )
            estado_id = None
            df_nucleos = pd.DataFrame()
            df_regionais = pd.DataFrame()
            df_mun = pd.DataFrame()
            nucleo_id = None
            if estado_sel != "Selecione...":
                estado_id = int(df_estados_view[df_estados_view["nome"] == estado_sel].iloc[0]["id"])
                info_est = carregar_estado_info(conn, estado_id)
                if info_est:
                    st.markdown(
                        f'<div class="auth-box"><b>Estado:</b> {info_est["nome"]} ({info_est["sigla"]})<br>'
                        f'<b>Governador:</b> {info_est["governador"]}<br>'
                        f'<b>Secretário(a):</b> {info_est["secretario_saude"]}</div>',
                        unsafe_allow_html=True
                    )
                try:
                    df_nucleos = pd.read_sql(
                        "SELECT id, nome FROM regionais_saude WHERE estado_id=%s AND (parent_id IS NULL OR parent_id=0) ORDER BY nome",
                        conn, params=(estado_id,)
                    )
                except Exception:
                    df_nucleos = pd.read_sql(
                        "SELECT id, nome FROM regionais_saude WHERE estado_id=%s ORDER BY nome",
                        conn, params=(estado_id,)
                    )
            with c2:
                lista_n = (["Selecione..."] + df_nucleos["nome"].tolist()) if estado_id and not df_nucleos.empty else ["Selecione o estado primeiro"]
                nucleo_sel = st.selectbox("Núcleo", lista_n, key="nav_nucleo")
            if estado_id and nucleo_sel not in ["Selecione...", "Selecione o estado primeiro"]:
                nucleo_id = int(df_nucleos[df_nucleos["nome"] == nucleo_sel].iloc[0]["id"])
                try:
                    df_regionais = pd.read_sql(
                        "SELECT id, nome FROM regionais_saude WHERE parent_id=%s ORDER BY nome",
                        conn, params=(nucleo_id,)
                    )
                except Exception:
                    df_regionais = pd.DataFrame()
            with c3:
                lista_r = (["Todos do núcleo"] + df_regionais["nome"].tolist()) if nucleo_id and not df_regionais.empty else (["Todos do núcleo"] if nucleo_id else ["Selecione o núcleo"])
                reg_sel = st.selectbox("Regional", lista_r, key="nav_regional")
            if nucleo_id is not None:
                if reg_sel not in ["Todos do núcleo", "Selecione o núcleo"] and not df_regionais.empty:
                    reg_id = int(df_regionais[df_regionais["nome"] == reg_sel].iloc[0]["id"])
                    df_mun = pd.read_sql(
                        "SELECT id, nome, codigo_ibge, status FROM municipios WHERE regional_id=%s ORDER BY nome",
                        conn, params=(reg_id,)
                    )
                elif not df_regionais.empty:
                    ids = [nucleo_id] + df_regionais["id"].tolist()
                    ph = ",".join(["%s"] * len(ids))
                    df_mun = pd.read_sql(
                        f"SELECT id, nome, codigo_ibge, status FROM municipios WHERE regional_id IN ({ph}) ORDER BY nome",
                        conn, params=tuple(ids)
                    )
                else:
                    df_mun = pd.read_sql(
                        "SELECT id, nome, codigo_ibge, status FROM municipios WHERE regional_id=%s ORDER BY nome",
                        conn, params=(nucleo_id,)
                    )
            elif estado_id is not None:
                df_mun = pd.read_sql(
                    """
                    SELECT m.id, m.nome, m.codigo_ibge, m.status
                    FROM municipios m
                    LEFT JOIN regionais_saude r ON r.id = m.regional_id
                    WHERE r.estado_id=%s
                    ORDER BY m.nome
                    """,
                    conn, params=(estado_id,)
                )
            with c4:
                lista_m = (["Selecione..."] + df_mun["nome"].tolist()) if not df_mun.empty else ["Sem municípios"]
                mun_sel = st.selectbox("Município", lista_m, key="nav_mun")
            if mun_sel not in ["Selecione...", "Sem municípios"] and not df_mun.empty:
                mid = int(df_mun[df_mun["nome"] == mun_sel].iloc[0]["id"])
                st.markdown(f"### Localidades de **{mun_sel}**")
                df_loc = pd.read_sql(
                    "SELECT id, nome, tipo, status FROM localidades WHERE municipio_id=%s ORDER BY nome",
                    conn, params=(mid,)
                )
                st.dataframe(df_loc if not df_loc.empty else pd.DataFrame(), use_container_width=True, hide_index=True)
            elif estado_sel != "Selecione..." and not df_mun.empty:
                st.dataframe(df_mun, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Erro: {e}")

    elif menu_sisloc == "Localidades":
        st.subheader("Localidades")
        try:
            est_f = st.selectbox("Estado", ["Todos"] + df_estados_view["nome"].tolist(), key="loc_est")
            sql = """
                SELECT l.id, e.nome as estado, m.nome as municipio, l.nome as localidade, l.tipo, l.status
                FROM localidades l
                LEFT JOIN municipios m ON m.id = l.municipio_id
                LEFT JOIN regionais_saude r ON r.id = m.regional_id
                LEFT JOIN estados e ON e.id = r.estado_id
                WHERE 1=1
            """
            params = []
            if est_f != "Todos":
                sql += " AND e.nome = %s"
                params.append(est_f)
            sql += " ORDER BY e.nome, m.nome, l.nome LIMIT 5000"
            df = pd.read_sql(sql, conn, params=tuple(params) if params else None)
            st.dataframe(df if not df.empty else pd.DataFrame(), use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Erro: {e}")

    elif menu_sisloc == "Cadastrar Localidade":
        st.subheader("Cadastrar Nova Localidade")
        try:
            if nivel == "Federal":
                estado_sel = st.selectbox(
                    "Estado",
                    ["Selecione o estado..."] + df_estados_cad["nome"].tolist(),
                    key="cad_est"
                )
            else:
                estado_sel = df_estados_cad.iloc[0]["nome"]
                st.selectbox("Estado", [estado_sel], disabled=True, key="cad_est")
            df_mun = pd.DataFrame()
            if estado_sel != "Selecione o estado...":
                eid = int(df_estados_cad[df_estados_cad["nome"] == estado_sel].iloc[0]["id"])
                df_mun = municipios_por_estado(conn, eid, False)
            mun_sel = st.selectbox(
                "Município",
                ["Selecione..."] + df_mun["nome"].tolist() if not df_mun.empty else ["Selecione o estado"],
                key="cad_mun"
            )
            nome = st.text_input("Nome da Localidade", key="cad_nome_loc")
            tipo = st.selectbox("Tipo", ["Bairro", "Povoado", "Vila", "Distrito", "Outro"], key="cad_tipo_loc")
            if st.button("Salvar Localidade", type="primary", key="cad_btn_loc"):
                if estado_sel == "Selecione o estado..." or mun_sel in ["Selecione...", "Selecione o estado"] or not nome.strip():
                    st.warning("Preencha os campos.")
                else:
                    mid = int(df_mun[df_mun["nome"] == mun_sel].iloc[0]["id"])
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO localidades (municipio_id, nome, tipo, status) VALUES (%s,%s,%s,'Ativa')",
                        (mid, nome.strip(), tipo)
                    )
                    conn.commit()
                    cur.close()
                    st.success("Localidade salva!")
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
            df_mun_e = municipios_por_estado(
                conn, int(df_estados_cad[df_estados_cad["nome"] == est_e].iloc[0]["id"])
            ) if est_e and est_e != "Selecione..." else pd.DataFrame()
            mun_e = st.selectbox(
                "Município",
                ["Selecione..."] + df_mun_e["nome"].tolist() if not df_mun_e.empty else ["Selecione o estado"],
                key="edloc_mun"
            )
            if mun_e not in ["Selecione...", "Selecione o estado"]:
                mid = int(df_mun_e[df_mun_e["nome"] == mun_e].iloc[0]["id"])
                df_loc_e = pd.read_sql(
                    "SELECT id, nome, tipo, status FROM localidades WHERE municipio_id=%s ORDER BY nome",
                    conn, params=(mid,)
                )
                if not df_loc_e.empty:
                    loc_e = st.selectbox(
                        "Localidade",
                        [f"{r['nome']}  [{r['status']}]" for _, r in df_loc_e.iterrows()],
                        key="edloc_loc"
                    )
                    nome_puro = loc_e.split("  [")[0]
                    row = df_loc_e[df_loc_e["nome"] == nome_puro].iloc[0]
                    lid = int(row["id"])
                    novo_nome = st.text_input("Nome", value=str(row["nome"]), key="edloc_nome")
                    tipos = ["Bairro", "Povoado", "Vila", "Distrito", "Outro"]
                    tipo_atual = str(row["tipo"]) if row["tipo"] in tipos else "Outro"
                    novo_tipo = st.selectbox("Tipo", tipos, index=tipos.index(tipo_atual), key="edloc_tipo")
                    status_atual = str(row["status"]) if row["status"] in ("Ativa", "Arquivada") else "Ativa"
                    novo_status = st.selectbox(
                        "Status", ["Ativa", "Arquivada"],
                        index=0 if status_atual == "Ativa" else 1,
                        key="edloc_status"
                    )
                    if st.button("Salvar", type="primary", key="edloc_salvar"):
                        cur = conn.cursor()
                        cur.execute(
                            "UPDATE localidades SET nome=%s, tipo=%s, status=%s WHERE id=%s",
                            (novo_nome.strip(), novo_tipo, novo_status, lid)
                        )
                        conn.commit()
                        cur.close()
                        st.success("Atualizado!")
                        st.rerun()
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
            df_mun_m = municipios_por_estado(
                conn, int(df_estados_cad[df_estados_cad["nome"] == est_m].iloc[0]["id"]), True
            ) if est_m and est_m != "Selecione..." else pd.DataFrame()
            if not df_mun_m.empty:
                mun_m = st.selectbox(
                    "Município",
                    [f"{r['nome']}  [{r['status'] or 'Ativo'}]" for _, r in df_mun_m.iterrows()],
                    key="edmun_mun"
                )
                nome_puro = mun_m.split("  [")[0]
                row = df_mun_m[df_mun_m["nome"] == nome_puro].iloc[0]
                mid = int(row["id"])
                status_atual = str(row["status"]) if row["status"] in ("Ativo", "Arquivado") else "Ativo"
                novo_status = st.selectbox(
                    "Status", ["Ativo", "Arquivado"],
                    index=0 if status_atual == "Ativo" else 1,
                    key="edmun_status"
                )
                if st.button("Salvar status", type="primary", key="edmun_salvar"):
                    cur = conn.cursor()
                    cur.execute("UPDATE municipios SET status=%s WHERE id=%s", (novo_status, mid))
                    conn.commit()
                    cur.close()
                    st.success("Atualizado!")
                    st.rerun()
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
                    ORDER BY e.nome, m.nome, i.quarteirao, i.sequencia
                    LIMIT 3000
                """, conn)
                if df.empty:
                    st.info("Nenhum imóvel cadastrado ainda.")
                else:
                    st.dataframe(df, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"Erro: {e}")
        with tab2:
            try:
                if nivel == "Federal":
                    estado_sel = st.selectbox(
                        "Estado",
                        ["Selecione o estado..."] + df_estados_cad["nome"].tolist(),
                        key="imv_cad_est"
                    )
                else:
                    estado_sel = df_estados_cad.iloc[0]["nome"]
                    st.selectbox("Estado", [estado_sel], disabled=True, key="imv_cad_est")
                df_mun = municipios_por_estado(
                    conn, int(df_estados_cad[df_estados_cad["nome"] == estado_sel].iloc[0]["id"]), False
                ) if estado_sel != "Selecione o estado..." else pd.DataFrame()
                mun_sel = st.selectbox(
                    "Município",
                    ["Selecione..."] + df_mun["nome"].tolist() if not df_mun.empty else ["Selecione o estado"],
                    key="imv_cad_mun"
                )
                df_loc = pd.DataFrame()
                if mun_sel not in ["Selecione...", "Selecione o estado"]:
                    mid = int(df_mun[df_mun["nome"] == mun_sel].iloc[0]["id"])
                    df_loc = pd.read_sql(
                        "SELECT id, nome FROM localidades WHERE municipio_id=%s AND (status IS NULL OR status='Ativa') ORDER BY nome",
                        conn, params=(mid,)
                    )
                loc_sel = st.selectbox(
                    "Localidade",
                    ["Selecione..."] + df_loc["nome"].tolist() if not df_loc.empty else ["Selecione o município"],
                    key="imv_cad_loc"
                )
                campos = form_campos_imovel("sis_imv")
                if st.button("Salvar Imóvel", type="primary", key="imv_cad_btn"):
                    if loc_sel in ["Selecione...", "Selecione o município"] or not campos["identificacao"]:
                        st.warning("Preencha localidade e identificação.")
                    else:
                        lid = int(df_loc[df_loc["nome"] == loc_sel].iloc[0]["id"])
                        cur = conn.cursor()
                        cur.execute("""
                            INSERT INTO imoveis
                            (localidade_id, identificacao, quarteirao, lado, sequencia, numero, complemento,
                             tipo, tipo_construcao, situacao, observacao, ativo, data_cadastro)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,TRUE,CURRENT_DATE)
                        """, (
                            lid, campos["identificacao"], campos["quarteirao"], campos["lado"], campos["sequencia"],
                            campos["numero"], campos["complemento"], campos["tipo"], campos["tipo_construcao"],
                            campos["situacao"], campos["observacao"]
                        ))
                        conn.commit()
                        cur.close()
                        st.success("Imóvel salvo!")
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
            df_mun_i = municipios_por_estado(
                conn, int(df_estados_cad[df_estados_cad["nome"] == est_i].iloc[0]["id"])
            ) if est_i and est_i != "Selecione..." else pd.DataFrame()
            mun_i = st.selectbox(
                "Município",
                ["Selecione..."] + df_mun_i["nome"].tolist() if not df_mun_i.empty else ["Selecione o estado"],
                key="edim_mun"
            )
            df_loc_i = pd.DataFrame()
            if mun_i not in ["Selecione...", "Selecione o município"]:
                mid = int(df_mun_i[df_mun_i["nome"] == mun_i].iloc[0]["id"])
                df_loc_i = pd.read_sql(
                    "SELECT id, nome FROM localidades WHERE municipio_id=%s ORDER BY nome",
                    conn, params=(mid,)
                )
            loc_i = st.selectbox(
                "Localidade",
                ["Selecione..."] + df_loc_i["nome"].tolist() if not df_loc_i.empty else ["Selecione o município"],
                key="edim_loc"
            )
            if loc_i not in ["Selecione...", "Selecione o município"]:
                lid = int(df_loc_i[df_loc_i["nome"] == loc_i].iloc[0]["id"])
                df_imv = pd.read_sql("""
                    SELECT id, identificacao, quarteirao, lado, sequencia, numero, complemento,
                           tipo, tipo_construcao, situacao, observacao
                    FROM imoveis
                    WHERE localidade_id=%s
                    ORDER BY quarteirao, sequencia, id
                """, conn, params=(lid,))
                if df_imv.empty:
                    st.info("Nenhum imóvel nesta localidade.")
                else:
                    opcoes = [
                        f"#{int(r['id'])} — Q{r['quarteirao'] or '-'} Seq{r['sequencia'] or '-'} | {r['identificacao'] or '(sem id.)'}"
                        for _, r in df_imv.iterrows()
                    ]
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
                            """, (
                                campos["identificacao"], campos["quarteirao"], campos["lado"], campos["sequencia"],
                                campos["numero"], campos["complemento"], campos["tipo"], campos["tipo_construcao"],
                                campos["situacao"], campos["observacao"], iid
                            ))
                            conn.commit()
                            cur.close()
                            st.success("Imóvel atualizado!")
                            st.rerun()
                    st.markdown("---")
                    confirmar = st.checkbox("Confirmo exclusão definitiva deste imóvel", key="edim_conf")
                    if st.button("Excluir imóvel", disabled=not confirmar, key="edim_excluir"):
                        cur = conn.cursor()
                        cur.execute("DELETE FROM imoveis WHERE id=%s", (iid,))
                        conn.commit()
                        cur.close()
                        st.success("Excluído.")
                        st.rerun()
        except Exception as e:
            st.error(f"Erro: {e}")
    conn.close()

elif st.session_state.pagina == "PCDCh":
    st.markdown('<div class="module-header"><h1>PCDCh</h1><p>Pesquisas, Capturas e Diário</p></div>', unsafe_allow_html=True)
    menu = st.radio(
        "Menu",
        ["Cadastro", "Pesquisa", "Captura", "Diário"],
        horizontal=True,
        label_visibility="collapsed",
        key="pcdch_menu_v2"
    )
    conn = conectar_banco()
    if not conn:
        st.stop()
    df_estados_cad = carregar_estados_cadastro(conn, usuario)

    def seletor_estado_cadastro(key):
        if nivel == "Federal":
            return st.selectbox("Estado", ["Selecione..."] + df_estados_cad["nome"].tolist(), key=key)
        nome = df_estados_cad.iloc[0]["nome"] if not df_estados_cad.empty else "—"
        st.selectbox("Estado", [nome], key=key, disabled=True)
        return nome

    def estado_id_de_nome(nome, df_ref):
        if not nome or nome == "Selecione...":
            return None
        row = df_ref[df_ref["nome"] == nome]
        return int(row.iloc[0]["id"]) if not row.empty else None

    if menu == "Cadastro":
        sub = st.radio(
            "Cadastro",
            ["Agente", "Imóvel", "Etiqueta", "Triatomínio", "Inseticida"],
            horizontal=True,
            key="pcdch_cad_sub"
        )
        st.markdown("---")
        if sub == "Agente":
            ag_sub = st.radio("Agente", ["Novo", "Listar", "Editar / Inativar"], horizontal=True, key="ag_sub")
            st.markdown("---")
            if ag_sub == "Novo":
                st.subheader("Cadastro de Agente")
                est = seletor_estado_cadastro("ag_est")
                eid = estado_id_de_nome(est, df_estados_cad)
                df_mun = municipios_por_estado(conn, eid, False) if eid else pd.DataFrame()
                mun_sel = st.selectbox(
                    "Município",
                    ["Selecione..."] + df_mun["nome"].tolist(),
                    key="ag_mun"
                ) if not df_mun.empty else None
                nome = st.text_input("Nome do agente", key="ag_nome")
                cpf = st.text_input("CPF (opcional)", key="ag_cpf")
                matricula = st.text_input("Matrícula (opcional)", key="ag_mat")
                telefone = st.text_input("Telefone (opcional)", key="ag_tel")
                if st.button("Salvar Agente", type="primary", key="ag_btn"):
                    if not nome.strip() or not mun_sel or mun_sel == "Selecione...":
                        st.warning("Informe nome e município.")
                    else:
                        mid = int(df_mun[df_mun["nome"] == mun_sel].iloc[0]["id"])
                        try:
                            cur = conn.cursor()
                            cur.execute(
                                "INSERT INTO agentes (nome, cpf, matricula, telefone, municipio_id, ativo) VALUES (%s,%s,%s,%s,%s,TRUE)",
                                (nome.strip(), so_numeros(cpf) or None, matricula.strip() or None, telefone.strip() or None, mid)
                            )
                            conn.commit()
                            cur.close()
                            st.success(f"Agente **{nome}** salvo!")
                        except Exception as e:
                            st.error(f"Erro: {e}")
            elif ag_sub == "Listar":
                try:
                    df = pd.read_sql("""
                        SELECT a.id, a.nome, a.cpf, a.matricula, a.ativo, m.nome as municipio, e.nome as estado
                        FROM agentes a
                        LEFT JOIN municipios m ON m.id = a.municipio_id
                        LEFT JOIN regionais_saude r ON r.id = m.regional_id
                        LEFT JOIN estados e ON e.id = r.estado_id
                        ORDER BY e.nome, m.nome, a.nome
                        LIMIT 2000
                    """, conn)
                    if df.empty:
                        st.info("Nenhum agente.")
                    else:
                        df["ativo"] = df["ativo"].apply(lambda x: "Ativo" if x is None or x else "Inativo")
                        st.dataframe(df, use_container_width=True, hide_index=True)
                except Exception as e:
                    st.error(f"Erro: {e}")
            else:
                try:
                    df_ag = pd.read_sql(
                        "SELECT a.id, a.nome, a.ativo, m.nome as municipio FROM agentes a LEFT JOIN municipios m ON m.id = a.municipio_id ORDER BY a.nome LIMIT 500",
                        conn
                    )
                    if not df_ag.empty:
                        opcoes = [
                            f"#{int(r['id'])} — {r['nome']} [{'Ativo' if r['ativo'] is None or r['ativo'] else 'Inativo'}]"
                            for _, r in df_ag.iterrows()
                        ]
                        escolhido = st.selectbox("Agente", opcoes, key="ag_ed_sel")
                        aid = int(escolhido.split("—")[0].replace("#", "").strip())
                        row = df_ag[df_ag["id"] == aid].iloc[0]
                        novo_nome = st.text_input("Nome", value=str(row["nome"] or ""), key="ag_ed_nome")
                        novo_ativo = st.selectbox(
                            "Situação", ["Ativo", "Inativo"],
                            index=0 if (row["ativo"] is None or row["ativo"]) else 1,
                            key="ag_ed_ativo"
                        )
                        if st.button("Salvar", type="primary", key="ag_ed_salvar"):
                            cur = conn.cursor()
                            cur.execute(
                                "UPDATE agentes SET nome=%s, ativo=%s WHERE id=%s",
                                (novo_nome.strip(), novo_ativo == "Ativo", aid)
                            )
                            conn.commit()
                            cur.close()
                            st.success("Atualizado!")
                            st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

        elif sub == "Imóvel":
            st.subheader("Cadastro de Imóvel (PCDCh)")
            est = seletor_estado_cadastro("im_est")
            eid = estado_id_de_nome(est, df_estados_cad)
            df_mun = municipios_por_estado(conn, eid, False) if eid else pd.DataFrame()
            mun_sel = st.selectbox(
                "Município",
                ["Selecione..."] + df_mun["nome"].tolist(),
                key="im_mun"
            ) if not df_mun.empty else None
            df_loc = pd.DataFrame()
            loc_sel = None
            if mun_sel and mun_sel != "Selecione...":
                mid = int(df_mun[df_mun["nome"] == mun_sel].iloc[0]["id"])
                df_loc = pd.read_sql(
                    "SELECT id, nome FROM localidades WHERE municipio_id=%s ORDER BY nome",
                    conn, params=(mid,)
                )
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
                        """, (
                            lid, campos["identificacao"], campos["quarteirao"], campos["lado"], campos["sequencia"],
                            campos["numero"], campos["complemento"], campos["tipo"], campos["tipo_construcao"],
                            campos["situacao"], campos["observacao"]
                        ))
                        conn.commit()
                        cur.close()
                        st.success("Imóvel salvo!")
                    except Exception as e:
                        st.error(f"Erro: {e}")

        elif sub == "Etiqueta":
            st.subheader("Controle de Etiquetas")
            est = seletor_estado_cadastro("etq_est")
            eid = estado_id_de_nome(est, df_estados_cad)
            df_mun = municipios_por_estado(conn, eid, False) if eid else pd.DataFrame()
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
                        conn.commit()
                        cur.close()
                        st.success("Salvo!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")

        elif sub == "Triatomínio":
            st.subheader("Cadastro de Triatomínio")
            tab_t1, tab_t2 = st.tabs(["Listar / Novo", "Inativar"])
            with tab_t1:
                try:
                    df_t = pd.read_sql(
                        "SELECT id, nome_cientifico, nome_popular, ativo FROM triatominios ORDER BY nome_cientifico",
                        conn
                    )
                    if df_t.empty:
                        st.info("Nenhuma espécie.")
                    else:
                        df_show = df_t.copy()
                        df_show["ativo"] = df_show["ativo"].apply(lambda x: "Ativo" if x is None or x else "Inativo")
                        st.dataframe(df_show, use_container_width=True, hide_index=True)
                except Exception as e:
                    st.error(f"Erro: {e}")
                nc = st.text_input("Nome científico *", key="tri_nc")
                npop = st.text_input("Nome popular", key="tri_np")
                if st.button("Salvar espécie", type="primary", key="tri_btn"):
                    if not nc.strip():
                        st.warning("Informe o nome científico.")
                    else:
                        try:
                            cur = conn.cursor()
                            cur.execute(
                                "INSERT INTO triatominios (nome_cientifico, nome_popular, ativo) VALUES (%s,%s,TRUE)",
                                (nc.strip(), npop.strip() or None)
                            )
                            conn.commit()
                            cur.close()
                            st.success("Salva!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")
            with tab_t2:
                try:
                    df_t2 = pd.read_sql(
                        "SELECT id, nome_cientifico, ativo FROM triatominios ORDER BY nome_cientifico",
                        conn
                    )
                    if not df_t2.empty:
                        op = [f"#{int(r['id'])} — {r['nome_cientifico']}" for _, r in df_t2.iterrows()]
                        esc = st.selectbox("Espécie", op, key="tri_ed_sel")
                        tid = int(esc.split("—")[0].replace("#", "").strip())
                        sit = st.selectbox("Situação", ["Ativo", "Inativo"], key="tri_ed_sit")
                        if st.button("Salvar situação", type="primary", key="tri_ed_btn"):
                            cur = conn.cursor()
                            cur.execute("UPDATE triatominios SET ativo=%s WHERE id=%s", (sit == "Ativo", tid))
                            conn.commit()
                            cur.close()
                            st.success("Atualizado!")
                            st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

        elif sub == "Inseticida":
            st.subheader("Cadastro de Inseticida")
            tab_i1, tab_i2 = st.tabs(["Listar / Novo", "Inativar"])
            with tab_i1:
                try:
                    df_i = pd.read_sql(
                        "SELECT id, nome, principio_ativo, formulacao, ativo FROM inseticidas ORDER BY nome",
                        conn
                    )
                    if df_i.empty:
                        st.info("Nenhum inseticida.")
                    else:
                        df_show = df_i.copy()
                        df_show["ativo"] = df_show["ativo"].apply(lambda x: "Ativo" if x is None or x else "Inativo")
                        st.dataframe(df_show, use_container_width=True, hide_index=True)
                except Exception as e:
                    st.error(f"Erro: {e}")
                nome_i = st.text_input("Nome do produto *", key="ins_nome")
                pa = st.text_input("Princípio ativo", key="ins_pa")
                form = st.text_input("Formulação", key="ins_form")
                if st.button("Salvar inseticida", type="primary", key="ins_btn"):
                    if not nome_i.strip():
                        st.warning("Informe o nome.")
                    else:
                        try:
                            cur = conn.cursor()
                            cur.execute(
                                "INSERT INTO inseticidas (nome, principio_ativo, formulacao, ativo) VALUES (%s,%s,%s,TRUE)",
                                (nome_i.strip(), pa.strip() or None, form.strip() or None)
                            )
                            conn.commit()
                            cur.close()
                            st.success("Salvo!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")
            with tab_i2:
                try:
                    df_i2 = pd.read_sql("SELECT id, nome, ativo FROM inseticidas ORDER BY nome", conn)
                    if not df_i2.empty:
                        op = [f"#{int(r['id'])} — {r['nome']}" for _, r in df_i2.iterrows()]
                        esc = st.selectbox("Inseticida", op, key="ins_ed_sel")
                        iid = int(esc.split("—")[0].replace("#", "").strip())
                        sit = st.selectbox("Situação", ["Ativo", "Inativo"], key="ins_ed_sit")
                        if st.button("Salvar situação", type="primary", key="ins_ed_btn"):
                            cur = conn.cursor()
                            cur.execute("UPDATE inseticidas SET ativo=%s WHERE id=%s", (sit == "Ativo", iid))
                            conn.commit()
                            cur.close()
                            st.success("Atualizado!")
                            st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

    elif menu == "Pesquisa":
        sub = st.radio("Pesquisa", ["Nova Pesquisa", "Listar", "Editar / Arquivar"], horizontal=True, key="pcdch_pesq_sub")
        st.markdown("---")
        if sub == "Nova Pesquisa":
            st.subheader("Nova Pesquisa Entomológica")
            est = seletor_estado_cadastro("pq_est")
            eid = estado_id_de_nome(est, df_estados_cad)
            df_mun = municipios_por_estado(conn, eid, False) if eid else pd.DataFrame()
            mun_sel = st.selectbox(
                "Município",
                ["Selecione..."] + df_mun["nome"].tolist(),
                key="pq_mun"
            ) if not df_mun.empty else None
            df_loc = pd.DataFrame()
            loc_sel = None
            lid = None
            mid = None
            if mun_sel and mun_sel != "Selecione...":
                mid = int(df_mun[df_mun["nome"] == mun_sel].iloc[0]["id"])
                df_loc = pd.read_sql(
                    "SELECT id, nome FROM localidades WHERE municipio_id=%s ORDER BY nome",
                    conn, params=(mid,)
                )
                if not df_loc.empty:
                    loc_sel = st.selectbox("Localidade", ["Selecione..."] + df_loc["nome"].tolist(), key="pq_loc")
                    if loc_sel and loc_sel != "Selecione...":
                        lid = int(df_loc[df_loc["nome"] == loc_sel].iloc[0]["id"])
            imovel_id = None
            if lid:
                df_imv = imoveis_da_localidade(conn, lid)
                if not df_imv.empty:
                    opcoes_i = ["Sem imóvel específico"] + [
                        f"#{int(r['id'])} — Q{r['quarteirao'] or '-'} | {r['identificacao'] or '-'}"
                        for _, r in df_imv.iterrows()
                    ]
                    imv_sel = st.selectbox("Imóvel (opcional)", opcoes_i, key="pq_imv")
                    if imv_sel != "Sem imóvel específico":
                        imovel_id = int(imv_sel.split("—")[0].replace("#", "").strip())
            agente_id = None
            if mid:
                try:
                    df_ag = pd.read_sql(
                        "SELECT id, nome FROM agentes WHERE municipio_id=%s AND (ativo IS NULL OR ativo=TRUE) ORDER BY nome",
                        conn, params=(mid,)
                    )
                except Exception:
                    df_ag = pd.DataFrame()
                if not df_ag.empty:
                    op_ag = ["Selecione..."] + [f"#{int(r['id'])} — {r['nome']}" for _, r in df_ag.iterrows()]
                    ag_sel = st.selectbox("Agente", op_ag, key="pq_ag")
                    if ag_sel != "Selecione...":
                        agente_id = int(ag_sel.split("—")[0].replace("#", "").strip())
            sugestao = obter_proximo_etiqueta(conn, mid) if mid else 1
            data_p = st.date_input("Data", value=date.today(), key="pq_data")
            tipo = st.selectbox(
                "Tipo",
                ["Ativa", "Passiva", "Notificação de morador", "Pesquisa de foco", "Outra"],
                key="pq_tipo"
            )
            metodo = st.selectbox(
                "Método",
                ["Captura manual", "Armadilha adesiva", "Armadilha luminosa", "Outro"],
                key="pq_met"
            )
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
                        conn.commit()
                        cur.close()
                        st.success("Pesquisa salva!")
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
                    ORDER BY p.data_pesquisa DESC
                    LIMIT 500
                """, conn)
                st.dataframe(df if not df.empty else pd.DataFrame(), use_container_width=True, hide_index=True)
            except Exception as e:
                st.warning(str(e))
        else:
            try:
                df_p = pd.read_sql(
                    "SELECT p.id, p.data_pesquisa, p.status, m.nome as municipio FROM pesquisas_entomologicas p LEFT JOIN localidades l ON l.id = p.localidade_id LEFT JOIN municipios m ON m.id = l.municipio_id ORDER BY p.data_pesquisa DESC LIMIT 300",
                    conn
                )
                if not df_p.empty:
                    opcoes = [
                        f"#{int(r['id'])} — {r['data_pesquisa']} | {r['municipio'] or '-'} [{r['status'] or 'Ativa'}]"
                        for _, r in df_p.iterrows()
                    ]
                    escolhido = st.selectbox("Pesquisa", opcoes, key="edpq_sel")
                    pid = int(escolhido.split("—")[0].replace("#", "").strip())
                    row = df_p[df_p["id"] == pid].iloc[0]
                    status_atual = str(row["status"]) if row["status"] in ("Ativa", "Arquivada") else "Ativa"
                    novo_status = st.selectbox(
                        "Status", ["Ativa", "Arquivada"],
                        index=0 if status_atual == "Ativa" else 1,
                        key="edpq_status"
                    )
                    if st.button("Salvar", type="primary", key="edpq_salvar"):
                        cur = conn.cursor()
                        cur.execute("UPDATE pesquisas_entomologicas SET status=%s WHERE id=%s", (novo_status, pid))
                        conn.commit()
                        cur.close()
                        st.success("Atualizado!")
                        st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")

    elif menu == "Captura":
        sub = st.radio("Captura", ["Nova Captura", "Listar", "Editar / Arquivar"], horizontal=True, key="pcdch_cap_sub")
        st.markdown("---")
        if sub == "Nova Captura":
            st.subheader("Nova Captura")
            est = seletor_estado_cadastro("cp_est")
            eid = estado_id_de_nome(est, df_estados_cad)
            df_mun = municipios_por_estado(conn, eid, False) if eid else pd.DataFrame()
            mun_sel = st.selectbox(
                "Município",
                ["Selecione..."] + df_mun["nome"].tolist(),
                key="cp_mun"
            ) if not df_mun.empty else None
            df_loc = pd.DataFrame()
            loc_sel = None
            lid = None
            mid = None
            if mun_sel and mun_sel != "Selecione...":
                mid = int(df_mun[df_mun["nome"] == mun_sel].iloc[0]["id"])
                df_loc = pd.read_sql(
                    "SELECT id, nome FROM localidades WHERE municipio_id=%s ORDER BY nome",
                    conn, params=(mid,)
                )
                if not df_loc.empty:
                    loc_sel = st.selectbox("Localidade", ["Selecione..."] + df_loc["nome"].tolist(), key="cp_loc")
                    if loc_sel and loc_sel != "Selecione...":
                        lid = int(df_loc[df_loc["nome"] == loc_sel].iloc[0]["id"])
            pesquisa_id = None
            if lid:
                df_pesq = pesquisas_da_localidade(conn, lid)
                if not df_pesq.empty:
                    opcoes_p = ["Sem vínculo"] + [
                        f"#{int(r['id'])} — {r['data_pesquisa']}" for _, r in df_pesq.iterrows()
                    ]
                    pesq_sel = st.selectbox("Pesquisa (opcional)", opcoes_p, key="cp_pesq")
                    if pesq_sel != "Sem vínculo":
                        pesquisa_id = int(pesq_sel.split("—")[0].replace("#", "").strip())
            agente_id = None
            if mid:
                try:
                    df_ag = pd.read_sql(
                        "SELECT id, nome FROM agentes WHERE municipio_id=%s AND (ativo IS NULL OR ativo=TRUE) ORDER BY nome",
                        conn, params=(mid,)
                    )
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
            estagio = st.selectbox(
                "Estágio",
                ["Ovo", "Ninfa 1", "Ninfa 2", "Ninfa 3", "Ninfa 4", "Ninfa 5", "Adulto"],
                key="cp_estagio"
            )
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
                        """, (
                            lid, pesquisa_id, agente_id, data_c, especie, qtd, estagio,
                            None if sexo == "Não se aplica" else sexo, local_c,
                            num_etq if num_etq > 0 else None, examinado, positivo_tc, obs.strip() or None
                        ))
                        if mid and num_etq and num_etq > 0:
                            cur.execute("""
                                INSERT INTO etiquetas_controle (municipio_id, proximo_numero, atualizado_em)
                                VALUES (%s, %s, CURRENT_TIMESTAMP)
                                ON CONFLICT (municipio_id)
                                DO UPDATE SET proximo_numero = GREATEST(etiquetas_controle.proximo_numero, EXCLUDED.proximo_numero),
                                              atualizado_em = CURRENT_TIMESTAMP
                            """, (mid, int(num_etq) + 1))
                        conn.commit()
                        cur.close()
                        st.success("Captura salva!")
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
                    ORDER BY c.data_captura DESC
                    LIMIT 500
                """, conn)
                st.dataframe(df if not df.empty else pd.DataFrame(), use_container_width=True, hide_index=True)
            except Exception as e:
                st.warning(str(e))
        else:
            try:
                df_c = pd.read_sql(
                    "SELECT id, data_captura, especie, status FROM capturas ORDER BY data_captura DESC LIMIT 300",
                    conn
                )
                if not df_c.empty:
                    opcoes = [
                        f"#{int(r['id'])} — {r['data_captura']} | {r['especie']} [{r['status'] or 'Ativa'}]"
                        for _, r in df_c.iterrows()
                    ]
                    escolhido = st.selectbox("Captura", opcoes, key="edcp_sel")
                    cid = int(escolhido.split("—")[0].replace("#", "").strip())
                    row = df_c[df_c["id"] == cid].iloc[0]
                    status_atual = str(row["status"]) if row["status"] in ("Ativa", "Arquivada") else "Ativa"
                    novo_status = st.selectbox(
                        "Status", ["Ativa", "Arquivada"],
                        index=0 if status_atual == "Ativa" else 1,
                        key="edcp_status"
                    )
                    if st.button("Salvar", type="primary", key="edcp_salvar"):
                        cur = conn.cursor()
                        cur.execute("UPDATE capturas SET status=%s WHERE id=%s", (novo_status, cid))
                        conn.commit()
                        cur.close()
                        st.success("Atualizado!")
                        st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")

    elif menu == "Diário":
        sub = st.radio("Diário", ["Novo", "Listar", "Arquivar"], horizontal=True, key="diario_v2_sub")
        st.markdown("---")

        if sub == "Novo":
            st.subheader("Diário de Pesquisa e/ou Borrifação")
            st.caption("Município → Localidade → Data → marcar atividade")

            if nivel == "Federal":
                est = st.selectbox(
                    "Estado",
                    ["Selecione..."] + df_estados_cad["nome"].tolist(),
                    key="d2_estado"
                )
            else:
                est = df_estados_cad.iloc[0]["nome"] if not df_estados_cad.empty else "—"
                st.selectbox("Estado", [est], key="d2_estado", disabled=True)

            eid = estado_id_de_nome(est, df_estados_cad)
            df_mun = municipios_por_estado(conn, eid, False) if eid else pd.DataFrame()
            mun_sel = st.selectbox(
                "Município",
                ["Selecione..."] + (df_mun["nome"].tolist() if not df_mun.empty else []),
                key="d2_mun"
            )
            mid = None
            if mun_sel and mun_sel != "Selecione..." and not df_mun.empty:
                mid = int(df_mun[df_mun["nome"] == mun_sel].iloc[0]["id"])

            df_loc = pd.DataFrame()
            if mid:
                df_loc = pd.read_sql(
                    """
                    SELECT id, nome, tipo
                    FROM localidades
                    WHERE municipio_id = %s
                      AND (status IS NULL OR status = 'Ativa')
                    ORDER BY nome
                    """,
                    conn, params=(mid,)
                )
            loc_sel = st.selectbox(
                "Localidade",
                ["Selecione..."] + (df_loc["nome"].tolist() if not df_loc.empty else []),
                key="d2_loc"
            )
            lid = None
            categoria_sugerida = ""
            if loc_sel and loc_sel != "Selecione..." and not df_loc.empty:
                lid = int(df_loc[df_loc["nome"] == loc_sel].iloc[0]["id"])
                categoria_sugerida = str(df_loc[df_loc["nome"] == loc_sel].iloc[0].get("tipo") or "")

            data_ativ = st.date_input("Data da atividade", value=date.today(), key="d2_data")

            st.markdown("### ATIVIDADE")
            st.info("Marque as atividades trabalhadas.")
            c_a, c_b, c_c = st.columns(3)
            with c_a:
                faz_pesquisa = st.checkbox("Pesquisa", key="d2_pesq")
            with c_b:
                faz_borrifacao = st.checkbox("Borrifação", key="d2_borr")
            with c_c:
                faz_pit = st.checkbox("At. PIT", key="d2_pit")

            st.markdown("### 1 — Unidade domiciliar")
            categoria = st.text_input("Categoria", value=categoria_sugerida, key="d2_cat")
            q1, q2, q3 = st.columns(3)
            with q1:
                quarteirao = st.text_input("Quarteirão", key="d2_quart")
            with q2:
                casa = st.text_input("Casa", key="d2_casa")
            with q3:
                complemento = st.text_input("Complemento", key="d2_comp")
            p1, p2 = st.columns(2)
            with p1:
                pend_pesq = st.text_input("Pendência na Pesquisa", key="d2_pend_p")
            with p2:
                pend_borr = st.text_input("Pendência na Borrifação", key="d2_pend_b")
            morador = st.text_input("Morador / colaborador", key="d2_mor")
            h1, h2, h3 = st.columns(3)
            with h1:
                hab = st.number_input("Habitantes", min_value=0, value=0, key="d2_hab")
            with h2:
                anexos = st.number_input("Anexos", min_value=0, value=0, key="d2_anx")
            with h3:
                situacao = st.selectbox(
                    "Situação",
                    ["", "Existente", "Fechado", "Desabitado", "Recusado", "Destruído", "Outro"],
                    key="d2_sit"
                )
            t1, t2 = st.columns(2)
            with t1:
                tipo_parede = st.selectbox(
                    "Tipo parede",
                    ["", "Alvenaria", "Madeira", "Taipa", "Mista", "Outro"],
                    key="d2_parede"
                )
            with t2:
                tipo_teto = st.selectbox(
                    "Tipo teto",
                    ["", "Telha", "Laje", "Palha", "Zinco", "Outro"],
                    key="d2_teto"
                )

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
                st.markdown("### 2 — Dados da Pesquisa")
                st.markdown("**Intradomicílio**")
                i1, i2 = st.columns(2)
                with i1:
                    captura_intra = st.number_input("Captura (intra)", min_value=0, value=0, key="d2_cap_in")
                with i2:
                    vestigios_intra = st.checkbox("Vestígios (intra)", key="d2_ves_in")
                st.markdown("**Peridomicílio**")
                r1, r2 = st.columns(2)
                with r1:
                    captura_peri = st.number_input("Captura (peri)", min_value=0, value=0, key="d2_cap_pe")
                with r2:
                    vestigios_peri = st.checkbox("Vestígios (peri)", key="d2_ves_pe")
                usa_idet = st.checkbox("Utilizando inseto de detecção", key="d2_idet")

            if faz_borrifacao or faz_pit:
                st.markdown("### 2 — Dados da Borrifação / At. PIT")
                b1, b2 = st.columns(2)
                with b1:
                    desalojante = st.text_input("Desalojante", key="d2_des")
                    qtde_des = st.number_input("Qtde desalojante", min_value=0.0, value=0.0, step=0.1, key="d2_qdes")
                with b2:
                    lista_ins = lista_inseticidas(conn)
                    inseticida = st.selectbox("Inseticida", ["Selecione..."] + lista_ins, key="d2_ins")
                    if inseticida == "Selecione...":
                        inseticida = None
                    qtde_ins = st.number_input("Qtde inseticida", min_value=0.0, value=0.0, step=0.1, key="d2_qins")
                num_pit = st.text_input("Num. PIT", key="d2_npit")
                notificacao = st.text_input("Notificação", key="d2_notif")
                agente_saude = st.text_input("Agente de saúde", key="d2_ags")
                etq_sug = obter_proximo_etiqueta(conn, mid) if mid else 0
                etiqueta = st.number_input("Etiqueta", min_value=0, value=int(etq_sug), key="d2_etq")

            if st.button("Salvar diário", type="primary", key="d2_salvar"):
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
                                DO UPDATE SET
                                    proximo_numero = GREATEST(etiquetas_controle.proximo_numero, EXCLUDED.proximo_numero),
                                    atualizado_em = CURRENT_TIMESTAMP
                            """, (mid, int(etiqueta) + 1))
                        conn.commit()
                        cur.close()
                        st.success("Diário salvo!")
                    except Exception as e:
                        st.error(f"Erro: {e}")

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
                    ORDER BY d.data_atividade DESC
                    LIMIT 300
                """, conn)
                if df_d.empty:
                    st.info("Nenhum registro.")
                else:
                    opcoes = [
                        f"#{int(r['id'])} — {r['data_atividade']} | {r['municipio'] or '-'} "
                        f"Q{r['quarteirao'] or '-'} Casa {r['casa'] or '-'} [{r['status'] or 'Ativo'}]"
                        for _, r in df_d.iterrows()
                    ]
                    escolhido = st.selectbox("Registro", opcoes, key="d2_arq_sel")
                    did = int(escolhido.split("—")[0].replace("#", "").strip())
                    row = df_d[df_d["id"] == did].iloc[0]
                    status_atual = str(row["status"]) if row["status"] in ("Ativo", "Arquivado") else "Ativo"
                    novo_status = st.selectbox(
                        "Status",
                        ["Ativo", "Arquivado"],
                        index=0 if status_atual == "Ativo" else 1,
                        key="d2_arq_status"
                    )
                    if st.button("Salvar", type="primary", key="d2_arq_btn"):
                        cur = conn.cursor()
                        cur.execute("UPDATE diario_pcdch SET status=%s WHERE id=%s", (novo_status, did))
                        conn.commit()
                        cur.close()
                        st.success("Atualizado!")
                        st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")
    conn.close()

elif st.session_state.pagina == "PCE":
    st.markdown('<div class="module-header"><h1>PCE</h1><p>Programa de Controle da Esquistossomose</p></div>', unsafe_allow_html=True)
    menu = st.radio(
        "Menu",
        ["Cadastro", "Pesquisa malacológica"],
        horizontal=True,
        label_visibility="collapsed",
        key="pce_menu"
    )
    conn = conectar_banco()
    if not conn:
        st.stop()
    df_estados_cad = carregar_estados_cadastro(conn, usuario)

    def seletor_estado_pce(key):
        if nivel == "Federal":
            return st.selectbox("Estado", ["Selecione..."] + df_estados_cad["nome"].tolist(), key=key)
        nome = df_estados_cad.iloc[0]["nome"] if not df_estados_cad.empty else "—"
        st.selectbox("Estado", [nome], key=key, disabled=True)
        return nome

    def estado_id_pce(nome, df_ref):
        if not nome or nome == "Selecione...":
            return None
        row = df_ref[df_ref["nome"] == nome]
        return int(row.iloc[0]["id"]) if not row.empty else None

    if menu == "Cadastro":
        st.subheader("Cadastro de Coleção Hídrica")
        est = seletor_estado_pce("pce_col_est")
        eid = estado_id_pce(est, df_estados_cad)
        df_mun = municipios_por_estado(conn, eid, False) if eid else pd.DataFrame()
        mun_sel = st.selectbox(
            "Município",
            ["Selecione..."] + df_mun["nome"].tolist(),
            key="pce_col_mun"
        ) if not df_mun.empty else None
        df_loc = pd.DataFrame()
        loc_sel = None
        if mun_sel and mun_sel != "Selecione...":
            mid = int(df_mun[df_mun["nome"] == mun_sel].iloc[0]["id"])
            df_loc = pd.read_sql(
                "SELECT id, nome FROM localidades WHERE municipio_id=%s AND (status IS NULL OR status='Ativa') ORDER BY nome",
                conn, params=(mid,)
            )
            if not df_loc.empty:
                loc_sel = st.selectbox("Localidade", ["Selecione..."] + df_loc["nome"].tolist(), key="pce_col_loc")
        nome_col = st.text_input("Nome da coleção / ponto de água *", key="pce_col_nome")
        tipo_col = st.selectbox(
            "Tipo",
            ["Rio", "Córrego", "Lagoa", "Açude", "Vala", "Poço", "Reservatório", "Outro"],
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
                        "INSERT INTO colecoes_hidricas (localidade_id, nome, tipo, status, observacao) VALUES (%s,%s,%s,'Ativa',%s)",
                        (lid, nome_col.strip(), tipo_col, obs_col.strip() or None)
                    )
                    conn.commit()
                    cur.close()
                    st.success(f"Coleção **{nome_col}** salva!")
                except Exception as e:
                    st.error(f"Erro: {e}")
        try:
            df_c = pd.read_sql("""
                SELECT c.id, c.nome, c.tipo, c.status, l.nome as localidade, m.nome as municipio
                FROM colecoes_hidricas c
                LEFT JOIN localidades l ON l.id = c.localidade_id
                LEFT JOIN municipios m ON m.id = l.municipio_id
                ORDER BY m.nome, c.nome
                LIMIT 1000
            """, conn)
            st.dataframe(df_c if not df_c.empty else pd.DataFrame(), use_container_width=True, hide_index=True)
        except Exception as e:
            st.caption(str(e))

    elif menu == "Pesquisa malacológica":
        sub = st.radio("Pesquisa", ["Nova", "Listar", "Arquivar"], horizontal=True, key="pce_pesq_sub")
        st.markdown("---")
        if sub == "Nova":
            st.subheader("Nova Pesquisa Malacológica")
            est = seletor_estado_pce("pce_pm_est")
            eid = estado_id_pce(est, df_estados_cad)
            df_mun = municipios_por_estado(conn, eid, False) if eid else pd.DataFrame()
            mun_sel = st.selectbox(
                "Município",
                ["Selecione..."] + df_mun["nome"].tolist(),
                key="pce_pm_mun"
            ) if not df_mun.empty else None
            df_loc = pd.DataFrame()
            loc_sel = None
            lid = None
            mid = None
            if mun_sel and mun_sel != "Selecione...":
                mid = int(df_mun[df_mun["nome"] == mun_sel].iloc[0]["id"])
                df_loc = pd.read_sql(
                    "SELECT id, nome FROM localidades WHERE municipio_id=%s AND (status IS NULL OR status='Ativa') ORDER BY nome",
                    conn, params=(mid,)
                )
                if not df_loc.empty:
                    loc_sel = st.selectbox("Localidade", ["Selecione..."] + df_loc["nome"].tolist(), key="pce_pm_loc")
                    if loc_sel and loc_sel != "Selecione...":
                        lid = int(df_loc[df_loc["nome"] == loc_sel].iloc[0]["id"])
            colecao_id = None
            if lid:
                try:
                    df_col = pd.read_sql(
                        "SELECT id, nome, tipo FROM colecoes_hidricas WHERE localidade_id=%s AND (status IS NULL OR status='Ativa') ORDER BY nome",
                        conn, params=(lid,)
                    )
                except Exception:
                    df_col = pd.DataFrame()
                if not df_col.empty:
                    op_col = ["Sem coleção específica"] + [
                        f"#{int(r['id'])} — {r['nome']} ({r['tipo'] or '-'})" for _, r in df_col.iterrows()
                    ]
                    col_sel = st.selectbox("Coleção hídrica", op_col, key="pce_pm_col")
                    if col_sel != "Sem coleção específica":
                        colecao_id = int(col_sel.split("—")[0].replace("#", "").strip())
            agente_id = None
            if mid:
                try:
                    df_ag = pd.read_sql(
                        "SELECT id, nome FROM agentes WHERE municipio_id=%s AND (ativo IS NULL OR ativo=TRUE) ORDER BY nome",
                        conn, params=(mid,)
                    )
                except Exception:
                    df_ag = pd.DataFrame()
                if not df_ag.empty:
                    op_ag = ["Selecione..."] + [f"#{int(r['id'])} — {r['nome']}" for _, r in df_ag.iterrows()]
                    ag_sel = st.selectbox("Agente", op_ag, key="pce_pm_ag")
                    if ag_sel != "Selecione...":
                        agente_id = int(ag_sel.split("—")[0].replace("#", "").strip())
            data_p = st.date_input("Data", value=date.today(), key="pce_pm_data")
            especie = st.selectbox(
                "Espécie",
                ["Biomphalaria glabrata", "Biomphalaria straminea", "Biomphalaria tenagophila", "Biomphalaria spp.", "Outra"],
                key="pce_pm_esp"
            )
            metodo = st.selectbox(
                "Método",
                ["Concha / peneira", "Pinça", "Armadilha", "Observação direta", "Outro"],
                key="pce_pm_met"
            )
            c1, c2 = st.columns(2)
            with c1:
                coletados = st.number_input("Moluscos coletados", min_value=0, value=0, key="pce_pm_col_n")
            with c2:
                positivos = st.number_input("Moluscos positivos", min_value=0, value=0, key="pce_pm_pos")
            obs = st.text_area("Observações", key="pce_pm_obs")
            if st.button("Salvar pesquisa malacológica", type="primary", key="pce_pm_btn"):
                if not loc_sel or loc_sel == "Selecione...":
                    st.warning("Selecione a localidade.")
                else:
                    try:
                        cur = conn.cursor()
                        cur.execute("""
                            INSERT INTO pesquisas_malacologicas
                            (localidade_id, colecao_id, agente_id, data_pesquisa, especie, moluscos_coletados,
                             moluscos_positivos, metodo, observacao, status, status_envio)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'Ativa','Rascunho')
                        """, (lid, colecao_id, agente_id, data_p, especie, coletados, positivos, metodo, obs.strip() or None))
                        conn.commit()
                        cur.close()
                        st.success("Pesquisa malacológica salva!")
                    except Exception as e:
                        st.error(f"Erro: {e}")
        elif sub == "Listar":
            try:
                df = pd.read_sql("""
                    SELECT p.id, p.data_pesquisa, p.especie, p.moluscos_coletados, p.moluscos_positivos, p.status,
                           a.nome as agente, l.nome as localidade, m.nome as municipio
                    FROM pesquisas_malacologicas p
                    LEFT JOIN agentes a ON a.id = p.agente_id
                    LEFT JOIN localidades l ON l.id = p.localidade_id
                    LEFT JOIN municipios m ON m.id = l.municipio_id
                    ORDER BY p.data_pesquisa DESC
                    LIMIT 500
                """, conn)
                st.dataframe(df if not df.empty else pd.DataFrame(), use_container_width=True, hide_index=True)
            except Exception as e:
                st.warning(str(e))
        else:
            try:
                df_p = pd.read_sql("""
                    SELECT p.id, p.data_pesquisa, p.especie, p.status, m.nome as municipio
                    FROM pesquisas_malacologicas p
                    LEFT JOIN localidades l ON l.id = p.localidade_id
                    LEFT JOIN municipios m ON m.id = l.municipio_id
                    ORDER BY p.data_pesquisa DESC
                    LIMIT 300
                """, conn)
                if not df_p.empty:
                    opcoes = [
                        f"#{int(r['id'])} — {r['data_pesquisa']} | {r['especie'] or '-'} [{r['status'] or 'Ativa'}]"
                        for _, r in df_p.iterrows()
                    ]
                    escolhido = st.selectbox("Pesquisa", opcoes, key="pce_arq_sel")
                    pid = int(escolhido.split("—")[0].replace("#", "").strip())
                    row = df_p[df_p["id"] == pid].iloc[0]
                    status_atual = str(row["status"]) if row["status"] in ("Ativa", "Arquivada") else "Ativa"
                    novo_status = st.selectbox(
                        "Status", ["Ativa", "Arquivada"],
                        index=0 if status_atual == "Ativa" else 1,
                        key="pce_arq_status"
                    )
                    if st.button("Salvar", type="primary", key="pce_arq_btn"):
                        cur = conn.cursor()
                        cur.execute("UPDATE pesquisas_malacologicas SET status=%s WHERE id=%s", (novo_status, pid))
                        conn.commit()
                        cur.close()
                        st.success("Atualizado!")
                        st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")
    conn.close()