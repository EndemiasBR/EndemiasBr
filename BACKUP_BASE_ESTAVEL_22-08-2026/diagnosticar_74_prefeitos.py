import psycopg2
import zipfile
import csv
import io
import unicodedata
import re
from difflib import SequenceMatcher


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

    texto = texto.replace("'", "")
    texto = texto.replace("-", " ")

    texto = re.sub(
        r"\([^)]*\)",
        "",
        texto
    )

    texto = re.sub(
        r"[^A-Z0-9 ]",
        " ",
        texto
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    ).strip()

    return texto


def similar(a, b):
    return SequenceMatcher(
        None,
        normalizar(a),
        normalizar(b)
    ).ratio()


print("=" * 70)
print("DIAGNOSTICO DOS PREFEITOS PENDENTES")
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
# MUNICIPIOS PENDENTES
# ==========================================================

print()
print("Buscando municipios sem prefeito...")

cur.execute("""
    SELECT
        m.id,
        m.codigo_ibge,
        m.nome,
        e.sigla
    FROM municipios m
    LEFT JOIN estados e
        ON e.id = m.estado_id
    LEFT JOIN autoridades a
        ON a.municipio_id = m.id
       AND a.esfera = 'MUNICIPAL'
       AND a.cargo = 'Prefeito'
    WHERE a.nome = 'A CADASTRAR'
    ORDER BY e.sigla, m.nome
""")

pendentes = cur.fetchall()

print(
    "PENDENTES ENCONTRADOS:",
    len(pendentes)
)


# ==========================================================
# LER TSE
# ==========================================================

print()
print("Lendo base TSE ja baixada...")
print()

tse_municipios = {}


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

    for numero, arquivo_zip in enumerate(
        arquivos,
        1
    ):

        print(
            f"[{numero}/{len(arquivos)}]",
            arquivo_zip
        )

        with z.open(
            arquivo_zip
        ) as f:

            dados = f.read()

        try:
            texto = dados.decode(
                "latin1"
            )
        except:
            texto = dados.decode(
                "utf-8",
                errors="replace"
            )

        leitor = csv.DictReader(
            io.StringIO(texto),
            delimiter=";"
        )

        if not leitor.fieldnames:
            continue


        campos = {}

        for coluna in leitor.fieldnames:

            chave = normalizar(
                coluna
            ).replace(
                " ",
                "_"
            )

            campos[chave] = coluna


        def campo(*nomes):

            for nome in nomes:

                nome = normalizar(
                    nome
                ).replace(
                    " ",
                    "_"
                )

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


        if not (
            uf_col
            and municipio_col
            and cargo_col
            and candidato_col
        ):
            continue


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

            municipio = str(
                linha.get(
                    municipio_col,
                    ""
                )
            ).strip()

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

                valor = (
                    valor
                    .replace(".", "")
                    .replace(",", ".")
                )

                try:
                    votos = float(
                        valor
                    )
                except:
                    votos = 0


            chave = (
                uf,
                normalizar(municipio)
            )


            atual = tse_municipios.get(
                chave
            )


            if (
                atual is None
                or votos > atual["votos"]
            ):

                tse_municipios[chave] = {
                    "municipio": municipio,
                    "nome": candidato,
                    "votos": votos
                }


# ==========================================================
# DIAGNOSTICO
# ==========================================================

print()
print("=" * 70)
print("RESULTADO DO DIAGNOSTICO")
print("=" * 70)

print()

exatos = []
aproximados = []
nao_encontrados = []


for municipio_id, codigo_ibge, nome, uf in pendentes:

    uf_n = normalizar(uf)
    nome_n = normalizar(nome)

    chave = (
        uf_n,
        nome_n
    )


    # ------------------------------------------------------
    # Brasília
    # ------------------------------------------------------

    if codigo_ibge == "5300108":

        print(
            codigo_ibge,
            "|",
            uf,
            "|",
            nome,
            "=> BRASILIA/DF - CASO ESPECIAL"
        )

        continue


    # ------------------------------------------------------
    # Fernando de Noronha
    # ------------------------------------------------------

    if codigo_ibge == "2605459":

        print(
            codigo_ibge,
            "|",
            uf,
            "|",
            nome,
            "=> FERNANDO DE NORONHA - CASO ESPECIAL"
        )

        continue


    # ------------------------------------------------------
    # Correspondência exata
    # ------------------------------------------------------

    if chave in tse_municipios:

        dado = tse_municipios[chave]

        exatos.append(
            (
                codigo_ibge,
                uf,
                nome,
                dado["municipio"],
                dado["nome"],
                dado["votos"]
            )
        )

        continue


    # ------------------------------------------------------
    # Procurar aproximação dentro da mesma UF
    # ------------------------------------------------------

    candidatos = []

    for (
        chave_tse,
        dado
    ) in tse_municipios.items():

        uf_tse, nome_tse = chave_tse

        if uf_tse != uf_n:
            continue

        score = similar(
            nome,
            nome_tse
        )

        candidatos.append(
            (
                score,
                dado
            )
        )


    candidatos.sort(
        key=lambda x: x[0],
        reverse=True
    )


    if candidatos:

        melhor_score, melhor = candidatos[0]

        if melhor_score >= 0.80:

            aproximados.append(
                (
                    codigo_ibge,
                    uf,
                    nome,
                    melhor["municipio"],
                    melhor["nome"],
                    melhor_score,
                    melhor["votos"]
                )
            )

        else:

            nao_encontrados.append(
                (
                    codigo_ibge,
                    uf,
                    nome,
                    melhor["municipio"],
                    melhor_score
                )
            )

    else:

        nao_encontrados.append(
            (
                codigo_ibge,
                uf,
                nome,
                "NENHUM",
                0
            )
        )


# ==========================================================
# EXATOS
# ==========================================================

print()
print("=" * 70)
print("CORRESPONDENCIAS EXATAS")
print("=" * 70)

print(
    "TOTAL:",
    len(exatos)
)

for item in exatos:

    print(
        item[0],
        "|",
        item[1],
        "|",
        item[2],
        "=>",
        item[3],
        "|",
        item[4],
        "| VOTOS:",
        int(item[5])
    )


# ==========================================================
# APROXIMADOS
# ==========================================================

print()
print("=" * 70)
print("CORRESPONDENCIAS APROXIMADAS")
print("=" * 70)

print(
    "TOTAL:",
    len(aproximados)
)

for item in aproximados:

    print(
        item[0],
        "|",
        item[1],
        "|",
        item[2],
        "=>",
        item[3],
        "|",
        item[4],
        "| CONFIANCA:",
        f"{item[5] * 100:.1f}%",
        "| VOTOS:",
        int(item[6])
    )


# ==========================================================
# NAO ENCONTRADOS
# ==========================================================

print()
print("=" * 70)
print("SEM CORRESPONDENCIA SEGURA")
print("=" * 70)

print(
    "TOTAL:",
    len(nao_encontrados)
)

for item in nao_encontrados:

    print(
        item[0],
        "|",
        item[1],
        "|",
        item[2],
        "=> MELHOR:",
        item[3],
        "|",
        f"{item[4] * 100:.1f}%"
    )


# ==========================================================
# RESUMO
# ==========================================================

print()
print("=" * 70)
print("RESUMO")
print("=" * 70)

print(
    "PENDENTES:",
    len(pendentes)
)

print(
    "CORRESPONDENCIAS EXATAS:",
    len(exatos)
)

print(
    "CORRESPONDENCIAS APROXIMADAS:",
    len(aproximados)
)

print(
    "SEM CORRESPONDENCIA SEGURA:",
    len(nao_encontrados)
)

print()
print(
    "NENHUM DADO FOI ALTERADO NO BANCO."
)

print("=" * 70)


cur.close()
conn.close()