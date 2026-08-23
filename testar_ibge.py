import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="endemiasbr",
    user="postgres",
    password="Amor2806",
    port="5432",
    client_encoding="latin1"
)
cur = conn.cursor()

# Verifica como está o código IBGE de alguns municípios
cur.execute("SELECT codigo_ibge, nome FROM municipios WHERE nome ILIKE '%alagoinhas%' OR nome ILIKE '%jandaira%' OR nome ILIKE '%pedrao%' LIMIT 10")
for row in cur.fetchall():
    print(row)

cur.close()
conn.close()