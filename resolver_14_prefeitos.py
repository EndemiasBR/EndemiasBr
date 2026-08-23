import psycopg2
import zipfile
import csv
import io
import unicodedata
import re


ARQUIVO = r"C:\EndemiasBR\tse_prefeitos\resultado_tse_2024"


PENDENTES = {
    "5200852": ("GO", "Americano do Brasil"),
    "5210208": ("GO", "Iporá"),
    "2100709": ("MA", "Anajatuba"),
    "2104909": ("MA", "Guimarães"),
    "2110237": ("MA", "Santana do Maranhão"),
    "2400208": ("RN", "Açu"),
    "2401206": ("RN", "Arês"),
    "2401305": ("RN", "Augusto Severo (Campo Grande)"),
    "2405306": ("RN", "Januário Cicco (Boa Saúde)"),
    "2800605": ("SE", "Barra dos Coqueiros"),
    "2801603": ("SE", "Cedro de São João"),
    "2804805": ("SE", "Nossa Senhora do Socorro"),
    "3516101": ("SP", "Florínia"),
    "1708254": ("TO", "Fortaleza do Tabocão"),
}


def normalizar(texto):
    texto = str(texto or "").strip().upper()

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
    )

    return texto.strip()


print("=" * 70)
print("RESOLUCAO DOS 14 PREFEITOS PENDENTES")
print("=" * 70)

resultados = {}

with zipfile.ZipFile(
    ARQUIVO,
    "r"
) as z:

    arquivos = [
        x for x in z.namelist()
        if x.lower().endswith(".csv")
    ]

    print(
        "CSV ENCONTRADOS:",
        len(arquivos)
    )

    for arquivo_zip in arquivos:

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

                chave = normalizar(
                    nome
                ).replace(
                    " ",
                    "_"
                )

                if chave in campos:
                    return campos[chave]

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

            municipio = normalizar(
                linha.get(
                    municipio_col,
                    ""
                )
            )


            # procurar somente pelos municipios pendentes
            codigo_ibge = None

            for codigo, (
                uf_p,
                nome_p
            ) in PENDENTES.items():

                if (
                    uf == normalizar(uf_p)
                    and municipio == normalizar(nome_p)
                ):

                    codigo_ibge = codigo
                    break


            if not codigo_ibge:
                continue


            candidato = str(
                linha.get(
                    candidato_col,
                    ""
                )
            ).strip()


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
                    votos = float(valor)
                except:
                    votos = 0


            resultados.setdefault(
                codigo_ibge,
                []
            ).append(
                (
                    candidato,
                    votos
                )
            )


print()
print("=" * 70)
print("RESULTADO")
print("=" * 70)


for codigo, (
    uf,
    municipio
) in PENDENTES.items():

    print()
    print("-" * 70)
    print(
        codigo,
        "|",
        uf,
        "|",
        municipio
    )
    print("-" * 70)

    candidatos = resultados.get(
        codigo,
        []
    )

    if not candidatos:

        print(
            "NENHUM REGISTRO ENCONTRADO"
        )

        continue


    # ordenar pelos votos
    candidatos.sort(
        key=lambda x: x[1],
        reverse=True
    )


    for posicao, (
        nome,
        votos
    ) in enumerate(
        candidatos,
        1
    ):

        print(
            f"{posicao:02d}.",
            nome,
            "|",
            int(votos),
            "votos"
        )


print()
print("=" * 70)
print("FIM")
print("=" * 70)

print()
print("NENHUM DADO FOI ALTERADO NO BANCO.")