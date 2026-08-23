import streamlit as st
import psycopg
import pandas as pd
from datetime import date

st.set_page_config(page_title="EndemiasBR", page_icon="mosquito", layout="wide")

def conectar_banco():
    try:
        conn = psycopg.connect(
            host="localhost",
            dbname="endemiasbr",
            user="postgres",
            password="Amor2806",
            port="5432"
        )
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar: {e}")
        return None

st.sidebar.title("EndemiasBR")
menu = st.sidebar.radio("Navegacao", [
    "Tela Inicial",
    "Ver Localidades",
    "Nova Localidade",
    "Imoveis",
    "Chagas - Visitas",
    "Chagas - Capturas",
    "Esquistossomose"
])

conn = conectar_banco()

if menu == "Tela Inicial":
    st.title("EndemiasBR")
    st.write("Sistema de Apoio a Vigilancia de Endemias")
    
    if conn:
        st.success("Conectado ao banco com sucesso!")
        
        st.markdown("---")
        st.subheader("Resumo Operacional")
        
        try:
            total_localidades = pd.read_sql("SELECT COUNT(*) AS total FROM localidades", conn).iloc[0]["total"]
            total_imoveis = pd.read_sql("SELECT COUNT(*) AS total FROM imoveis", conn).iloc[0]["total"]
            total_visitas = pd.read_sql("SELECT COUNT(*) AS total FROM chagas_visitas", conn).iloc[0]["total"]
            total_capturas = pd.read_sql("SELECT COUNT(*) AS total FROM chagas_capturas", conn).iloc[0]["total"]
            total_esquisto = pd.read_sql("SELECT COUNT(*) AS total FROM esquistossomose_atividades", conn).iloc[0]["total"]
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Localidades", total_localidades)
            with col2:
                st.metric("Imoveis", total_imoveis)
            with col3:
                st.metric("Visitas Chagas", total_visitas)
            with col4:
                st.metric("Capturas", total_capturas)
            with col5:
                st.metric("Esquistossomose", total_esquisto)
                
        except Exception as e:
            st.warning("Nao foi possivel carregar o resumo.")
    else:
        st.warning("Nao foi possivel conectar ao banco.")

elif menu == "Ver Localidades":
    st.title("Localidades Cadastradas")
    if conn:
        try:
            df = pd.read_sql("""
                SELECT 
                    l.id,
                    l.nome AS localidade,
                    l.tipo,
                    m.nome AS municipio,
                    e.sigla AS uf
                FROM localidades l
                JOIN municipios m ON m.id = l.municipio_id
                JOIN estados e ON e.id = m.estado_id
                ORDER BY l.nome
            """, conn)
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao buscar: {e}")

elif menu == "Nova Localidade":
    st.title("Cadastrar Nova Localidade")
    if conn:
        df_mun = pd.read_sql("SELECT id, nome FROM municipios ORDER BY nome", conn)
        municipios = {row["nome"]: row["id"] for _, row in df_mun.iterrows()}

        nome = st.text_input("Nome da Localidade")
        tipo = st.selectbox("Tipo", ["Bairro", "Povoado", "Vila", "Distrito", "Outro"])
        municipio_nome = st.selectbox("Municipio", list(municipios.keys()))

        if st.button("Salvar Localidade"):
            if nome.strip() == "":
                st.warning("Digite o nome da localidade.")
            else:
                try:
                    with conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO localidades (municipio_id, nome, tipo) VALUES (%s, %s, %s)",
                            (municipios[municipio_nome], nome, tipo)
                        )
                        conn.commit()
                    st.success(f"Localidade {nome} salva com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

elif menu == "Imoveis":
    st.title("Cadastro de Imoveis")
    
    if conn:
        df_loc = pd.read_sql("SELECT id, nome FROM localidades ORDER BY nome", conn)
        localidades = {row["nome"]: row["id"] for _, row in df_loc.iterrows()}

        with st.form("form_imovel"):
            st.subheader("Novo Imovel")
            
            localidade_nome = st.selectbox("Localidade", list(localidades.keys()))
            identificacao = st.text_input("Identificacao (ex: Rua X, Casa 10)")
            tipo = st.selectbox("Tipo de Imovel", [
                "Residencial", "Comercial", "Terreno Baldio", "Igreja", "Escola", "Outro"
            ])
            situacao = st.selectbox("Situacao", [
                "Trabalhado", "Fechado", "Recusado", "Recuperado", "Outro"
            ])
            
            botao_salvar = st.form_submit_button("Salvar Imovel")
            
            if botao_salvar:
                if identificacao.strip() == "":
                    st.warning("Informe a identificacao do imovel.")
                else:
                    try:
                        with conn.cursor() as cur:
                            cur.execute(
                                """
                                INSERT INTO imoveis (localidade_id, identificacao, tipo, situacao)
                                VALUES (%s, %s, %s, %s)
                                """,
                                (localidades[localidade_nome], identificacao, tipo, situacao)
                            )
                            conn.commit()
                        st.success("Imovel cadastrado com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

        st.subheader("Imoveis Cadastrados")
        try:
            df = pd.read_sql("""
                SELECT i.id, l.nome AS localidade, i.identificacao, i.tipo, i.situacao
                FROM imoveis i
                LEFT JOIN localidades l ON l.id = i.localidade_id
                ORDER BY i.id DESC
            """, conn)
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.warning("Nenhum imovel cadastrado ainda.")

elif menu == "Chagas - Visitas":
    st.title("Chagas - Registro de Visitas")
    
    if conn:
        df_imoveis = pd.read_sql("""
            SELECT i.id, i.identificacao, l.nome AS localidade
            FROM imoveis i
            LEFT JOIN localidades l ON l.id = i.localidade_id
            ORDER BY l.nome, i.identificacao
        """, conn)
        
        imoveis_opcoes = {
            f"{row['identificacao']} ({row['localidade']})": row['id'] 
            for _, row in df_imoveis.iterrows()
        }

        with st.form("form_visita"):
            st.subheader("Nova Visita")
            
            if len(imoveis_opcoes) == 0:
                st.warning("Nenhum imovel cadastrado. Cadastre um imovel antes.")
                imovel_selecionado = None
            else:
                imovel_label = st.selectbox("Imovel", list(imoveis_opcoes.keys()))
                imovel_selecionado = imoveis_opcoes[imovel_label]
            
            data_visita = st.date_input("Data da Visita", value=date.today())
            agente_nome = st.text_input("Nome do Agente")
            tipo_atividade = st.selectbox("Tipo de Atividade", [
                "Pesquisa", "Captura", "Tratamento", "Educacao em Saude", "Outro"
            ])
            resultado = st.selectbox("Resultado", [
                "Positivo", "Negativo", "Pendente", "Nao realizado"
            ])
            observacao = st.text_area("Observacao")
            
            botao_salvar = st.form_submit_button("Salvar Visita")
            
            if botao_salvar:
                if agente_nome.strip() == "":
                    st.warning("Informe o nome do agente.")
                elif imovel_selecionado is None:
                    st.warning("Cadastre um imovel antes.")
                else:
                    try:
                        with conn.cursor() as cur:
                            cur.execute(
                                """
                                INSERT INTO chagas_visitas 
                                (imovel_id, data_visita, agente_nome, tipo_atividade, resultado, observacao)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                """,
                                (imovel_selecionado, data_visita, agente_nome, tipo_atividade, resultado, observacao)
                            )
                            conn.commit()
                        st.success("Visita registrada com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

        st.subheader("Visitas Registradas")
        try:
            df = pd.read_sql("""
                SELECT 
                    v.id, 
                    to_char(v.data_visita, 'DD/MM/YYYY') AS data_visita,
                    i.identificacao AS imovel,
                    l.nome AS localidade,
                    v.agente_nome, 
                    v.tipo_atividade, 
                    v.resultado
                FROM chagas_visitas v
                LEFT JOIN imoveis i ON i.id = v.imovel_id
                LEFT JOIN localidades l ON l.id = i.localidade_id
                ORDER BY v.data_visita DESC
            """, conn)
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.warning("Nenhuma visita registrada ainda.")

elif menu == "Chagas - Capturas":
    st.title("Chagas - Captura de Triatomineos")
    
    if conn:
        df_visitas = pd.read_sql("""
            SELECT 
                v.id,
                to_char(v.data_visita, 'DD/MM/YYYY') AS data_visita,
                i.identificacao AS imovel,
                l.nome AS localidade,
                v.agente_nome
            FROM chagas_visitas v
            LEFT JOIN imoveis i ON i.id = v.imovel_id
            LEFT JOIN localidades l ON l.id = i.localidade_id
            ORDER BY v.data_visita DESC
        """, conn)
        
        visitas_opcoes = {
            f"Visita {row['id']} - {row['data_visita']} - {row['imovel']} ({row['localidade']})": row['id']
            for _, row in df_visitas.iterrows()
        }

        with st.form("form_captura"):
            st.subheader("Nova Captura")
            
            if len(visitas_opcoes) == 0:
                st.warning("Nenhuma visita registrada. Registre uma visita antes.")
                visita_selecionada = None
            else:
                visita_label = st.selectbox("Visita", list(visitas_opcoes.keys()))
                visita_selecionada = visitas_opcoes[visita_label]
            
            especie = st.selectbox("Especie", [
                "Triatoma infestans",
                "Triatoma brasiliensis",
                "Triatoma sordida",
                "Panstrongylus megistus",
                "Rhodnius neglectus",
                "Outra"
            ])
            quantidade = st.number_input("Quantidade", min_value=1, value=1)
            local_captura = st.selectbox("Local da Captura", [
                "Intradomicilio", "Peridomicilio", "Anexo", "Outro"
            ])
            
            botao_salvar = st.form_submit_button("Salvar Captura")
            
            if botao_salvar:
                if visita_selecionada is None:
                    st.warning("Registre uma visita antes.")
                else:
                    try:
                        with conn.cursor() as cur:
                            cur.execute(
                                """
                                INSERT INTO chagas_capturas 
                                (visita_id, especie, quantidade, local_captura)
                                VALUES (%s, %s, %s, %s)
                                """,
                                (visita_selecionada, especie, quantidade, local_captura)
                            )
                            conn.commit()
                        st.success("Captura registrada com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

        st.subheader("Capturas Registradas")
        try:
            df = pd.read_sql("""
                SELECT 
                    c.id,
                    to_char(v.data_visita, 'DD/MM/YYYY') AS data_visita,
                    i.identificacao AS imovel,
                    l.nome AS localidade,
                    c.especie,
                    c.quantidade,
                    c.local_captura
                FROM chagas_capturas c
                LEFT JOIN chagas_visitas v ON v.id = c.visita_id
                LEFT JOIN imoveis i ON i.id = v.imovel_id
                LEFT JOIN localidades l ON l.id = i.localidade_id
                ORDER BY c.id DESC
            """, conn)
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.warning("Nenhuma captura registrada ainda.")

elif menu == "Esquistossomose":
    st.title("Esquistossomose - Registro de Atividades")
    
    if conn:
        df_loc = pd.read_sql("SELECT id, nome FROM localidades ORDER BY nome", conn)
        localidades = {row["nome"]: row["id"] for _, row in df_loc.iterrows()}

        with st.form("form_esquisto"):
            st.subheader("Nova Atividade")
            
            localidade_nome = st.selectbox("Localidade", list(localidades.keys()))
            data_atividade = st.date_input("Data da Atividade", value=date.today())
            tipo_atividade = st.selectbox("Tipo de Atividade", [
                "Pesquisa Malacologica",
                "Exame Parasitologico",
                "Tratamento",
                "Educacao em Saude",
                "Outro"
            ])
            agente_nome = st.text_input("Nome do Agente")
            resultado = st.selectbox("Resultado", [
                "Positivo", "Negativo", "Pendente", "Nao realizado"
            ])
            observacao = st.text_area("Observacao")
            
            botao_salvar = st.form_submit_button("Salvar Atividade")
            
            if botao_salvar:
                if agente_nome.strip() == "":
                    st.warning("Informe o nome do agente.")
                else:
                    try:
                        with conn.cursor() as cur:
                            cur.execute(
                                """
                                INSERT INTO esquistossomose_atividades 
                                (localidade_id, data_atividade, tipo_atividade, agente_nome, resultado, observacao)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                """,
                                (localidades[localidade_nome], data_atividade, tipo_atividade, agente_nome, resultado, observacao)
                            )
                            conn.commit()
                        st.success("Atividade registrada com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

        st.subheader("Atividades Registradas")
        try:
            df = pd.read_sql("""
                SELECT 
                    a.id,
                    to_char(a.data_atividade, 'DD/MM/YYYY') AS data_atividade,
                    l.nome AS localidade,
                    a.tipo_atividade,
                    a.agente_nome,
                    a.resultado
                FROM esquistossomose_atividades a
                LEFT JOIN localidades l ON l.id = a.localidade_id
                ORDER BY a.data_atividade DESC
            """, conn)
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.warning("Nenhuma atividade registrada ainda.")

if conn:
    conn.close()