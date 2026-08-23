import psycopg2
import csv
import os
import unicodedata
from datetime import date

ARQUIVO = r"C:\EndemiasBR\autoridades_municipais.csv"


def normalizar(texto):
    if texto is None:
        return ""

    texto = str(texto).strip().upper()

    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        c for c in texto
        if not unicodedata.combining(c)
    )

    return texto


print("=" * 70)
print("IMPORTADOR DE AUTORIDADES MUNICIPAIS")
print("=" * 70)

if not os.path.exists(ARQUIVO):
    print()
    print("ERRO: arquivo nao encontrado:")
    print(ARQUIVO)
    print()
    print("O arquivo deve conter:")
    print("codigo_ibge;prefeito;secretario_saude")
    print()
    raise SystemExit


senha = input("Senha do PostgreSQL: ")

conn = psycopg2.connect(
    host="localhost",
    dbname="endemiasbr",
    user="postgres",
    password=senha
)

cur = conn.cursor()


# ----------------------------------------------------------
# CARREGAR MUNICIPIOS
# ----------------------------------------------------------

print()
print("Carregando municipios do SisLoc...")

cur.execute("""
    SELECT
        id,
        codigo_ibge,
        nome
    FROM municipios
""")

municipios = {}

for municipio_id, codigo_ibge, nome in cur.fetchall():

    if codigo_ibge:
        codigo = str(codigo_ibge).strip()

        if len(codigo) == 7:
            municipios[codigo] = (
                municipio_id,
                nome
            )

print("MUNICIPIOS CARREGADOS:", len(municipios))


# ----------------------------------------------------------
# LER CSV
# ----------------------------------------------------------

print()
print("Lendo arquivo de autoridades...")

with open(
    ARQUIVO,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    leitor = csv.DictReader(
        f,
        delimiter=";"
    )

    colunas = [
        normalizar(c)
        for c in leitor.fieldnames
    ]

    print("COLUNAS:", leitor.fieldnames)

    linhas = list(leitor)


print("LINHAS NO ARQUIVO:", len(linhas))


# ----------------------------------------------------------
# ATUALIZAR
# ----------------------------------------------------------

atualizados_prefeitos = 0
atualizados_secretarios = 0
nao_encontrados = 0
sem_prefeito = 0
sem_secretario = 0


for linha in linhas:

    codigo = (
        linha.get("codigo_ibge")
        or linha.get("CODIGO_IBGE")
        or linha.get("codigo")
        or ""
    )

    codigo = str(codigo).strip()

    # Remove .0 caso venha de Excel
    if codigo.endswith(".0"):
        codigo = codigo[:-2]

    codigo = codigo.zfill(7)

    prefeito = (
        linha.get("prefeito")
        or linha.get("PREFEITO")
        or ""
    ).strip()

    secretario = (
        linha.get("secretario_saude")
        or linha.get("SECRETARIO_SAUDE")
        or linha.get("secretario")
        or ""
    ).strip()


    if codigo not in municipios:

        nao_encontrados += 1

        print(
            "MUNICIPIO NAO ENCONTRADO:",
            codigo
        )

        continue


    municipio_id, municipio_nome = municipios[codigo]


    # ------------------------------------------------------
    # PREFEITO
    # ------------------------------------------------------

    if prefeito:

        cur.execute("""
            UPDATE autoridades
               SET nome = %s,
                   ativo = TRUE,
                   fonte = 'Base oficial de autoridades municipais',
                   data_verificacao = %s,
                   observacao =
                       'Nome atualizado por carga nacional.'
             WHERE esfera = 'MUNICIPAL'
               AND municipio_id = %s
               AND cargo = 'Prefeito'
        """, (
            prefeito,
            date.today(),
            municipio_id
        ))

        if cur.rowcount:
            atualizados_prefeitos += cur.rowcount

    else:
        sem_prefeito += 1


    # ------------------------------------------------------
    # SECRETARIO
    # ------------------------------------------------------

    if secretario:

        cur.execute("""
            UPDATE autoridades
               SET nome = %s,
                   ativo = TRUE,
                   fonte = 'Base oficial de autoridades municipais',
                   data_verificacao = %s,
                   observacao =
                       'Nome atualizado por carga nacional.'
             WHERE esfera = 'MUNICIPAL'
               AND municipio_id = %s
               AND cargo = 'Secretário Municipal de Saúde'
        """, (
            secretario,
            date.today(),
            municipio_id
        ))

        if cur.rowcount:
            atualizados_secretarios += cur.rowcount

    else:
        sem_secretario += 1


# ----------------------------------------------------------
# GRAVAR
# ----------------------------------------------------------

conn.commit()


# ----------------------------------------------------------
# CONFERENCIA
# ----------------------------------------------------------

cur.execute("""
    SELECT COUNT(*)
    FROM autoridades
    WHERE esfera = 'MUNICIPAL'
      AND cargo = 'Prefeito'
      AND ativo = TRUE
      AND nome <> 'A CADASTRAR'
""")

prefeitos_preenchidos = cur.fetchone()[0]


cur.execute("""
    SELECT COUNT(*)
    FROM autoridades
    WHERE esfera = 'MUNICIPAL'
      AND cargo = 'Secretário Municipal de Saúde'
      AND ativo = TRUE
      AND nome <> 'A CADASTRAR'
""")

secretarios_preenchidos = cur.fetchone()[0]


cur.execute("""
    SELECT COUNT(*)
    FROM autoridades
    WHERE esfera = 'MUNICIPAL'
      AND nome = 'A CADASTRAR'
""")

pendentes = cur.fetchone()[0]


print()
print("=" * 70)
print("IMPORTACAO CONCLUIDA")
print("=" * 70)

print()
print("PREFEITOS ATUALIZADOS:", atualizados_prefeitos)
print("SECRETARIOS ATUALIZADOS:", atualizados_secretarios)

print()
print("PREFEITOS PREENCHIDOS:", prefeitos_preenchidos)
print("SECRETARIOS PREENCHIDOS:", secretarios_preenchidos)

print()
print("SEM PREFEITO NO ARQUIVO:", sem_prefeito)
print("SEM SECRETARIO NO ARQUIVO:", sem_secretario)
print("MUNICIPIOS NAO ENCONTRADOS:", nao_encontrados)

print()
print("AUTORIDADES MUNICIPAIS AINDA PENDENTES:", pendentes)

print("=" * 70)


cur.close()
conn.close()