def conectar_banco():
    try:
        conn = psycopg2.connect(
            "host=localhost dbname=endemiasbr user=postgres password=Amor2806 port=5432"
        )
        conn.set_client_encoding('UTF8')
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar: {e}")
        return None