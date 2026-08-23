import psycopg2
from datetime import date

print("=" * 70)
print("CARGA DOS 4 PREFEITOS FINAIS")
print("=" * 70)

senha = input("Senha do PostgreSQL: ")

conn = psycopg2.connect(
    host="localhost",
    dbname="endemiasbr",
    user="postgres",
    password=senha
)

cur = conn.cursor()

# ==========================================================
# 4 PREFEITOS CONFIRMADOS
# ==========================================================

prefeitos = {
    "2400208": "LUIS EDUARDO PIMENTEL SOARES",
    "2401206": "BERGSON IDUINO DE OLIVEIRA",
    "2401305": "FRANCISCO DAS CHAGAS EUFRASIO VIEIRA DE MELO",
    "3516101": "SERGIO LOPES DA SILVA",
}


print()
print(
    "PREFEITOS PARA ATUALIZAR:",
    len(prefeitos)
)

# ==========================================================
# CONFERIR ANTES DE GRAVAR
# ==========================================================

problemas = []

for codigo_ibge, nome_prefeito in prefeitos.items():

    cur.execute("""
        SELECT
            m.id,
            m.nome
        FROM municipios m
        WHERE m.codigo_ibge = %s
    """, (
        codigo_ibge,
    ))

    resultado = cur.fetchone()

    if not resultado:
        problemas.append(codigo_ibge)

    else:
        print(
            codigo_ibge,
            "|",
            resultado[1],
            "=>",
            nome_prefeito
        )


# ==========================================================
# PROTECAO
# ==========================================================

if problemas:

    print()
    print(
        "ERRO: MUNICIPIOS NAO ENCONTRADOS:"
    )

    for codigo in problemas:
        print(codigo)

    print()
    print("NENHUM DADO FOI ALTERADO.")

    conn.rollback()
    cur.close()
    conn.close()

    raise SystemExit


# ==========================================================
# GRAVAR
# ==========================================================

print()
print("Gravando...")

atualizados = 0

for codigo_ibge, nome_prefeito in prefeitos.items():

    cur.execute("""
        SELECT id
        FROM municipios
        WHERE codigo_ibge = %s
    """, (
        codigo_ibge,
    ))

    municipio_id = cur.fetchone()[0]

    cur.execute("""
        UPDATE autoridades
        SET
            nome = %s,
            ativo = TRUE,
            fonte =
                'Fontes oficiais municipais e governamentais - 2026',
            data_verificacao = %s,
            observacao =
                'Autoridade municipal confirmada em fonte oficial atual.'
        WHERE esfera = 'MUNICIPAL'
          AND municipio_id = %s
          AND cargo = 'Prefeito'
    """, (
        nome_prefeito,
        date.today(),
        municipio_id
    ))

    if cur.rowcount:
        atualizados += cur.rowcount


conn.commit()


# ==========================================================
# CONFERENCIA
# ==========================================================

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


print()
print("=" * 70)
print("CARGA CONCLUIDA")
print("=" * 70)

print(
    "ATUALIZADOS AGORA:",
    atualizados
)

print(
    "PREFEITOS PREENCHIDOS:",
    preenchidos
)

print(
    "PREFEITOS AINDA PENDENTES:",
    pendentes
)

print("=" * 70)

cur.close()
conn.close()