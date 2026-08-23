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

cur.execute("""
    SELECT codigo_ibge, nome 
    FROM municipios 
    WHERE codigo_ibge IN ('291790', '292660', '292410', '293190', '290070', '290030')
""")
for row in cur.fetchall():
    print(row)

print("---")
cur.execute("SELECT COUNT(*) FROM municipios WHERE codigo_ibge LIKE '29%'")
print("Total BA:", cur.fetchone()[0])

cur.close()
conn.close()