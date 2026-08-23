import psycopg

try:
    print("Tentando conectar...")
    conn = psycopg.connect(
        host="localhost",
        dbname="endemiasbr",
        user="postgres",
        password="Amor2806",
        port="5432"
    )
    print("Conectado com sucesso!")
    conn.close()
except Exception as e:
    print("ERRO COMPLETO:")
    print(type(e))
    print(e)