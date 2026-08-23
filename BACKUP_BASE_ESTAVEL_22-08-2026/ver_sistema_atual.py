import psycopg2

print("=" * 75)
print("SISLOC - SITUACAO ATUAL DO SISTEMA")
print("=" * 75)

senha = input("Senha do PostgreSQL: ")

conn = psycopg2.connect(
    host="localhost",
    dbname="endemiasbr",
    user="postgres",
    password=senha
)

cur = conn.cursor()


# ==========================================================
# TABELAS PRINCIPAIS
# ==========================================================

print()
print("=" * 75)
print("TABELAS DO BANCO")
print("=" * 75)

cur.execute("""
    SELECT
        table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_type = 'BASE TABLE'
    ORDER BY table_name
""")

for (tabela,) in cur.fetchall():
    print(tabela)


# ==========================================================
# CONTAGENS PRINCIPAIS
# ==========================================================

print()
print("=" * 75)
print("CONTAGENS")
print("=" * 75)

tabelas = [
    "estados",
    "municipios",
    "regionais",
    "localidades",
    "autoridades",
    "responsaveis"
]

for tabela in tabelas:

    try:

        cur.execute(
            f"SELECT COUNT(*) FROM {tabela}"
        )

        total = cur.fetchone()[0]

        print(
            f"{tabela.upper():20} : {total}"
        )

    except Exception as e:

        conn.rollback()

        print(
            f"{tabela.upper():20} : TABELA NAO ENCONTRADA"
        )


# ==========================================================
# AUTORIDADES POR ESFERA
# ==========================================================

print()
print("=" * 75)
print("AUTORIDADES POR ESFERA")
print("=" * 75)

try:

    cur.execute("""
        SELECT
            esfera,
            COUNT(*)
        FROM autoridades
        GROUP BY esfera
        ORDER BY esfera
    """)

    for esfera, total in cur.fetchall():

        print(
            f"{str(esfera):20} : {total}"
        )

except Exception as e:

    conn.rollback()
    print("ERRO:", e)


# ==========================================================
# AUTORIDADES POR CARGO
# ==========================================================

print()
print("=" * 75)
print("AUTORIDADES POR CARGO")
print("=" * 75)

try:

    cur.execute("""
        SELECT
            esfera,
            cargo,
            COUNT(*)
        FROM autoridades
        GROUP BY esfera, cargo
        ORDER BY
            CASE esfera
                WHEN 'FEDERAL' THEN 1
                WHEN 'ESTADUAL' THEN 2
                WHEN 'REGIONAL' THEN 3
                WHEN 'MUNICIPAL' THEN 4
                ELSE 5
            END,
            cargo
    """)

    for esfera, cargo, total in cur.fetchall():

        print(
            f"{str(esfera):12} | "
            f"{str(cargo):35} | "
            f"{total}"
        )

except Exception as e:

    conn.rollback()
    print("ERRO:", e)


# ==========================================================
# PREFEITOS
# ==========================================================

print()
print("=" * 75)
print("PREFEITOS")
print("=" * 75)

try:

    cur.execute("""
        SELECT COUNT(*)
        FROM autoridades
        WHERE esfera = 'MUNICIPAL'
          AND cargo = 'Prefeito'
          AND nome <> 'A CADASTRAR'
    """)

    preenchidos = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM autoridades
        WHERE esfera = 'MUNICIPAL'
          AND cargo = 'Prefeito'
          AND nome = 'A CADASTRAR'
    """)

    pendentes = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM autoridades
        WHERE esfera = 'MUNICIPAL'
          AND cargo = 'Prefeito'
          AND nome = 'NAO SE APLICA'
    """)

    nao_aplica = cur.fetchone()[0]

    print(
        "PREENCHIDOS     :",
        preenchidos
    )

    print(
        "A CADASTRAR     :",
        pendentes
    )

    print(
        "NAO SE APLICA   :",
        nao_aplica
    )

except Exception as e:

    conn.rollback()
    print("ERRO:", e)


# ==========================================================
# SECRETARIOS MUNICIPAIS
# ==========================================================

print()
print("=" * 75)
print("SECRETARIOS MUNICIPAIS DE SAUDE")
print("=" * 75)

try:

    cur.execute("""
        SELECT
            COUNT(*)
        FROM autoridades
        WHERE esfera = 'MUNICIPAL'
          AND (
              UPPER(cargo) LIKE '%SECRET%'
              OR UPPER(cargo) LIKE '%SAUDE%'
          )
    """)

    print(
        "REGISTROS EXISTENTES:",
        cur.fetchone()[0]
    )

except Exception as e:

    conn.rollback()
    print("ERRO:", e)


# ==========================================================
# FEDERAL
# ==========================================================

print()
print("=" * 75)
print("AUTORIDADES FEDERAIS")
print("=" * 75)

try:

    cur.execute("""
        SELECT
            cargo,
            nome
        FROM autoridades
        WHERE esfera = 'FEDERAL'
        ORDER BY cargo
    """)

    for cargo, nome in cur.fetchall():

        print(
            cargo,
            "=>",
            nome
        )

except Exception as e:

    conn.rollback()
    print("ERRO:", e)


# ==========================================================
# ESTADUAIS
# ==========================================================

print()
print("=" * 75)
print("AUTORIDADES ESTADUAIS")
print("=" * 75)

try:

    cur.execute("""
        SELECT
            COUNT(*)
        FROM autoridades
        WHERE esfera = 'ESTADUAL'
    """)

    print(
        "TOTAL:",
        cur.fetchone()[0]
    )

except Exception as e:

    conn.rollback()
    print("ERRO:", e)


# ==========================================================
# REGIONAIS
# ==========================================================

print()
print("=" * 75)
print("AUTORIDADES REGIONAIS")
print("=" * 75)

try:

    cur.execute("""
        SELECT
            COUNT(*)
        FROM autoridades
        WHERE esfera = 'REGIONAL'
    """)

    print(
        "TOTAL:",
        cur.fetchone()[0]
    )

except Exception as e:

    conn.rollback()
    print("ERRO:", e)


# ==========================================================
# USUARIOS / RESPONSAVEIS
# ==========================================================

print()
print("=" * 75)
print("USUARIOS / RESPONSAVEIS")
print("=" * 75)

try:

    cur.execute("""
        SELECT
            nivel,
            COUNT(*)
        FROM responsaveis
        GROUP BY nivel
        ORDER BY nivel
    """)

    for nivel, total in cur.fetchall():

        print(
            f"{str(nivel):20} : {total}"
        )

except Exception as e:

    conn.rollback()
    print("ERRO:", e)


# ==========================================================
# PROGRAMAS DOS USUARIOS
# ==========================================================

print()
print("=" * 75)
print("ACESSO DOS USUARIOS AOS PROGRAMAS")
print("=" * 75)

try:

    cur.execute("""
        SELECT
            COUNT(*) FILTER (
                WHERE gerencia_sisloc = TRUE
            ),
            COUNT(*) FILTER (
                WHERE gerencia_pcdch = TRUE
            ),
            COUNT(*) FILTER (
                WHERE gerencia_pce = TRUE
            )
        FROM responsaveis
    """)

    sisloc, pcdch, pce = cur.fetchone()

    print(
        "SISLOC :",
        sisloc
    )

    print(
        "PCDCH  :",
        pcdch
    )

    print(
        "PCE    :",
        pce
    )

except Exception as e:

    conn.rollback()
    print("ERRO:", e)


# ==========================================================
# FIM
# ==========================================================

print()
print("=" * 75)
print("FIM DA VERIFICACAO")
print("=" * 75)

print()
print("NENHUM DADO FOI ALTERADO.")

cur.close()
conn.close()