import psycopg2
from datetime import date

print("=" * 70)
print("FECHAMENTO DOS 12 PREFEITOS PENDENTES")
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
# 10 MUNICIPIOS COM PREFEITO CONFIRMADO
# ==========================================================

prefeitos = {
    "5200852": "RAPHAEL DE OLIVEIRA CARVALHO",
    "5210208": "MAYSA PERES CUNHA PEIXOTO",
    "2100709": "HELDER LOPES ARAGAO",
    "2104909": "ARIOMAGNO FERREIRA CARTAGENES",
    "2110237": "MARCIO JOSE MELO SANTIAGO",
    "2405306": "JOAO MARIA MESQUITA",
    "2800605": "AIRTON SAMPAIO MARTINS",
    "2801603": "NEUDO ALVES",
    "2804805": "SAMUEL CARVALHO DOS SANTOS JUNIOR",
    "1708254": "JASON MARINHO DE OLIVEIRA",
}


# ==========================================================
# CASOS QUE NAO POSSUEM PREFEITO MUNICIPAL
# ==========================================================

casos_especiais = {
    "5300108": (
        "BRASILIA/DF - NAO POSSUI PREFEITO MUNICIPAL"
    ),
    "2605459": (
        "FERNANDO DE NORONHA/PE - NAO E MUNICIPIO"
    ),
}


print()
print("PREFEITOS CONFIRMADOS:", len(prefeitos))
print("CASOS ESPECIAIS:", len(casos_especiais))


# ==========================================================
# CONFERIR OS MUNICIPIOS
# ==========================================================

problemas = []

print()
print("CONFERENCIA DOS 10 MUNICIPIOS:")

for codigo, nome_prefeito in prefeitos.items():

    cur.execute("""
        SELECT id, nome
        FROM municipios
        WHERE codigo_ibge = %s
    """, (codigo,))

    resultado = cur.fetchone()

    if not resultado:

        problemas.append(codigo)

    else:

        print(
            codigo,
            "|",
            resultado[1],
            "=>",
            nome_prefeito
        )


if problemas:

    print()
    print("ERRO: MUNICIPIOS NAO ENCONTRADOS:")

    for codigo in problemas:
        print(codigo)

    print()
    print("NENHUM DADO FOI ALTERADO.")

    conn.rollback()
    cur.close()
    conn.close()

    raise SystemExit


# ==========================================================
# GRAVAR OS 10 PREFEITOS
# ==========================================================

print()
print("Gravando os 10 prefeitos...")

atualizados = 0

for codigo, nome_prefeito in prefeitos.items():

    cur.execute("""
        SELECT id
        FROM municipios
        WHERE codigo_ibge = %s
    """, (codigo,))

    municipio_id = cur.fetchone()[0]

    cur.execute("""
        UPDATE autoridades
        SET
            nome = %s,
            ativo = TRUE,
            fonte =
                'Fontes oficiais municipais e IBGE - 2025/2026',
            data_verificacao = %s,
            observacao =
                'Prefeito confirmado em fonte oficial atual.'
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


# ==========================================================
# MARCAR OS DOIS CASOS ESPECIAIS
# ==========================================================
#
# Eles nao devem permanecer como "A CADASTRAR",
# porque nao existe prefeito municipal nesses casos.
#
# Mantemos o registro para que o sistema saiba por que
# aquele campo nao possui prefeito.
# ==========================================================

for codigo, observacao in casos_especiais.items():

    cur.execute("""
        SELECT id
        FROM municipios
        WHERE codigo_ibge = %s
    """, (codigo,))

    resultado = cur.fetchone()

    if resultado:

        municipio_id = resultado[0]

        cur.execute("""
            UPDATE autoridades
            SET
                nome = 'NAO SE APLICA',
                ativo = FALSE,
                fonte =
                    'Classificacao territorial oficial',
                data_verificacao = %s,
                observacao = %s
            WHERE esfera = 'MUNICIPAL'
              AND municipio_id = %s
              AND cargo = 'Prefeito'
        """, (
            date.today(),
            observacao,
            municipio_id
        ))


conn.commit()


# ==========================================================
# CONFERENCIA FINAL
# ==========================================================

cur.execute("""
    SELECT COUNT(*)
    FROM autoridades
    WHERE esfera = 'MUNICIPAL'
      AND cargo = 'Prefeito'
      AND nome <> 'A CADASTRAR'
""")

total_resolvidos = cur.fetchone()[0]


cur.execute("""
    SELECT COUNT(*)
    FROM autoridades
    WHERE esfera = 'MUNICIPAL'
      AND cargo = 'Prefeito'
      AND nome = 'A CADASTRAR'
""")

total_pendentes = cur.fetchone()[0]


print()
print("=" * 70)
print("FECHAMENTO CONCLUIDO")
print("=" * 70)

print(
    "PREFEITOS ATUALIZADOS AGORA:",
    atualizados
)

print(
    "PREFEITOS RESOLVIDOS NO BANCO:",
    total_resolvidos
)

print(
    "REGISTROS AINDA A CADASTRAR:",
    total_pendentes
)

print()
print("CASOS ESPECIAIS:")
print(
    "5300108 | Brasilia/DF | NAO SE APLICA"
)
print(
    "2605459 | Fernando de Noronha/PE | NAO SE APLICA"
)

print("=" * 70)

cur.close()
conn.close()