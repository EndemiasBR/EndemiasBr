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
print("===== TABELAS RELACIONADAS A AUTORIDADES =====")

x.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND (
          table_name ILIKE '%autor%'
          OR table_name ILIKE '%respons%'
          OR table_name ILIKE '%gestor%'
      )
    ORDER BY table_name
""")

tabelas = [r[0] for r in x.fetchall()]

if not tabelas:
    print("NENHUMA TABELA ENCONTRADA")
else:
    for tabela in tabelas:
        print()
        print("TABELA:", tabela)

        x.execute("""
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
            ORDER BY ordinal_position
        """, (tabela,))

        for coluna in x.fetchall():
            print(" | ".join(
                str(v) if v is not None else "-"
                for v in coluna
            ))

print()
print("===== FIM =====")

x.close()
c.close()