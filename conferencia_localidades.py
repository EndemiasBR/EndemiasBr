import psycopg2

senha = input("Senha do PostgreSQL: ")

c = psycopg2.connect(
    host="localhost",
    dbname="endemiasbr",
    user="postgres",
    password=senha
)

x = c.cursor()

print()
print("===== CONFERENCIA FINAL =====")

x.execute("SELECT COUNT(*) FROM municipios")
print("MUNICIPIOS:", x.fetchone()[0])

x.execute("SELECT COUNT(*) FROM localidades")
print("LOCALIDADES:", x.fetchone()[0])

x.execute("""
    SELECT COUNT(*)
    FROM localidades
    WHERE codigo_localidade IS NOT NULL
      AND TRIM(codigo_localidade) <> ''
""")
print("COM CODIGO IBGE:", x.fetchone()[0])

x.execute("""
    SELECT COUNT(*)
    FROM localidades
    WHERE codigo_localidade IS NULL
       OR TRIM(codigo_localidade) = ''
""")
print("SEM CODIGO IBGE:", x.fetchone()[0])

x.execute("""
    SELECT
        COUNT(*) - COUNT(DISTINCT codigo_localidade)
    FROM localidades
    WHERE codigo_localidade IS NOT NULL
      AND TRIM(codigo_localidade) <> ''
""")
print("DUPLICIDADES DE CODIGO:", x.fetchone()[0])

x.execute("""
    SELECT COUNT(*)
    FROM municipios m
    LEFT JOIN localidades l
        ON l.municipio_id = m.id
    WHERE l.id IS NULL
""")
print("MUNICIPIOS SEM LOCALIDADE:", x.fetchone()[0])

x.close()
c.close()

print()
print("===== FIM DA CONFERENCIA =====")