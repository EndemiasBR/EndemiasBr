import psycopg2
import zipfile
import csv
import os
import io
import unicodedata
from datetime import date

ARQUIVO_ZIP = r"C:\EndemiasBR\tse_prefeitos\resultado_tse_2024"


def normalizar(texto):
    if texto is None:
        return ""

    texto = str(texto).strip().upper()

    texto = unicodedata.normalize(
        "NFKD",
        texto
    )

    texto = "".join(
        c for c in texto
        if not unicodedata.combining(c)
    )

    return texto


print("=" * 70)
print("IMPORTACAO DE PREFEITOS - TSE 2024")
print("=" * 70)

print()
print("Usando arquivo TSE ja baixado:")
print(ARQUIVO_ZIP)

if not os.path.exists(ARQUIVO_ZIP):
    print()
    print("ERRO: arquivo TSE nao encontrado.")
    print(ARQUIVO_ZIP)
    raise SystemExit


senha = input("Senha do PostgreSQL: ")

conn = psycopg2.connect(
    host="localhost",
    dbname="endemiasbr",
    user="postgres",
    password=senha
)

cur = conn.cursor()


# ==========================================================
# MUNICIPIOS DO SISLOC
# ==========================================================

print()
print("Carregando municipios do SisLoc...")

cur.execute("""
    SELECT
        m.id,
        m.codigo_ibge,
        m.nome,
        e.sigla
    FROM municipios m
    LEFT JOIN estados e
        ON e.id = m.estado_id
    WHERE m.codigo_ibge IS NOT NULL
""")

municipios = {}

for municipio_id, codigo_ibge, nome, sigla in cur.fetchall():

    codigo = str(codigo_ibge).strip()

    if len(codigo) != 7:
        continue

    chave = (
        normalizar(sigla or ""),
        normalizar(nome)
    )

    municipios[chave] = {
        "id": municipio_id,
        "codigo_ibge": codigo,
        "nome": nome,
        "uf": sigla
    }


print(
    "MUNICIPIOS NO SISLOC:",
    len(municipios)
)


# ==========================================================
# ABRIR ZIP
# ==========================================================

print()
print("Abrindo base do TSE...")

eleitos = {}

with zipfile.ZipFile(
    ARQUIVO_ZIP,
    "r"
) as z:

    arquivos = [
        n for n in z.namelist()
        if n.lower().endswith(".csv")
    ]

    print(
        "ARQUIVOS CSV:",
        len(arquivos)
    )

    for numero, nome_arquivo in enumerate(
        arquivos,
        1
    ):

        print()
        print(
            f"[{numero}/{len(arquivos)}] LENDO:",
            nome_arquivo
        )

        with z.open(nome_arquivo) as arquivo:

            texto = arquivo.read()

        try:
            texto = texto.decode(
                "latin1"
            )
        except:
            texto = texto.decode(
                "utf-8",
                errors="replace"
            )

        leitor = csv.DictReader(
            io.StringIO(texto),
            delimiter=";"
        )

        if not leitor.fieldnames:
            print("SEM CABECALHO")
            continue

        # --------------------------------------------------
        # localizar colunas
        # --------------------------------------------------

        campos = {}

        for coluna in leitor.fieldnames:

            chave = normalizar(
                coluna
            ).replace(" ", "_")

            campos[chave] = coluna


        def campo(*nomes):

            for nome in nomes:

                nome = normalizar(
                    nome
                ).replace(" ", "_")

                if nome in campos:
                    return campos[nome]

            return None


        uf_col = campo(
            "SG_UF"
        )

        municipio_col = campo(
            "NM_MUNICIPIO"
        )

        cargo_col = campo(
            "DS_CARGO"
        )

        candidato_col = campo(
            "NM_CANDIDATO"
        )

        votos_col = campo(
            "QT_VOTOS_NOMINAIS"
        )

        situacao_col = campo(
            "DS_SIT_TOT_TURNO"
        )


        print(
            "UF:",
            uf_col,
            "| MUNICIPIO:",
            municipio_col,
            "| CARGO:",
            cargo_col
        )

        if not (
            uf_col
            and municipio_col
            and cargo_col
            and candidato_col
        ):
            print(
                "COLUNAS NECESSARIAS NAO ENCONTRADAS"
            )
            continue


        # --------------------------------------------------
        # processar registros
        # --------------------------------------------------

        registros = 0

        for linha in leitor:

            cargo = normalizar(
                linha.get(
                    cargo_col,
                    ""
                )
            )

            if "PREFEITO" not in cargo:
                continue


            uf = normalizar(
                linha.get(
                    uf_col,
                    ""
                )
            )

            municipio = normalizar(
                linha.get(
                    municipio_col,
                    ""
                )
            )

            candidato = str(
                linha.get(
                    candidato_col,
                    ""
                )
            ).strip()

            if not (
                uf
                and municipio
                and candidato
            ):
                continue


            chave = (
                uf,
                municipio
            )

            if chave not in municipios:
                continue


            # ------------------------------------------------
            # votos
            # ------------------------------------------------

            votos = 0

            if votos_col:

                valor = str(
                    linha.get(
                        votos_col,
                        "0"
                    )
                ).strip()

                valor = valor.replace(
                    ".",
                    ""
                ).replace(
                    ",",
                    "."
                )

                try:
                    votos = float(
                        valor
                    )
                except:
                    votos = 0


            # ------------------------------------------------
            # guardar maior votação
            # ------------------------------------------------

            codigo_ibge = municipios[
                chave
            ]["codigo_ibge"]


            chave_eleito = codigo_ibge

            atual = eleitos.get(
                chave_eleito
            )

            if (
                atual is None
                or votos > atual["votos"]
            ):

                eleitos[
                    chave_eleito
                ] = {
                    "nome": candidato,
                    "votos": votos,
                    "municipio": municipios[
                        chave
                    ]["nome"],
                    "uf": municipios[
                        chave
                    ]["uf"]
                }

            registros += 1


        print(
            "REGISTROS DE PREFEITO:",
            registros
        )


# ==========================================================
# CONFERENCIA
# ==========================================================

print()
print("=" * 70)
print("CONFERENCIA")
print("=" * 70)

print(
    "PREFEITOS ENCONTRADOS:",
    len(eleitos)
)

print(
    "MUNICIPIOS NO SISLOC:",
    len(municipios)
)


# ==========================================================
# PROTECAO
# ==========================================================

if len(eleitos) == 0:

    print()
    print(
        "NENHUM PREFEITO FOI ENCONTRADO."
    )

    print(
        "NENHUM DADO FOI ALTERADO."
    )

    conn.rollback()
    cur.close()
    conn.close()

    raise SystemExit


# ==========================================================
# MOSTRAR AMOSTRA
# ==========================================================

print()
print("AMOSTRA DOS PREFEITOS ENCONTRADOS:")

for codigo, dados in list(
    eleitos.items()
)[:20]:

    print(
        codigo,
        "|",
        dados["uf"],
        "|",
        dados["municipio"],
        "|",
        dados["nome"]
    )


# ==========================================================
# ATUALIZAR BANCO
# ==========================================================

print()
print(
    "Atualizando autoridades municipais..."
)

atualizados = 0

for codigo_ibge, dados in eleitos.items():

    municipio_id = municipios[
        (
            normalizar(dados["uf"]),
            normalizar(dados["municipio"])
        )
    ]["id"]


    cur.execute("""
        UPDATE autoridades
        SET
            nome = %s,
            ativo = TRUE,
            fonte =
                'Tribunal Superior Eleitoral - Eleicoes 2024',
            data_verificacao = %s,
            observacao =
                'Prefeito identificado na base oficial de resultados do TSE.'
        WHERE esfera = 'MUNICIPAL'
          AND municipio_id = %s
          AND cargo = 'Prefeito'
    """, (
        dados["nome"],
        date.today(),
        municipio_id
    ))

    if cur.rowcount:
        atualizados += cur.rowcount


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
print("IMPORTACAO CONCLUIDA")
print("=" * 70)

print(
    "PREFEITOS ENCONTRADOS NO TSE:",
    len(eleitos)
)

print(
    "PREFEITOS ATUALIZADOS:",
    atualizados
)

print(
    "PREFEITOS PREENCHIDOS NO BANCO:",
    preenchidos
)

print(
    "PREFEITOS AINDA PENDENTES:",
    pendentes
)

print("=" * 70)

cur.close()
conn.close()