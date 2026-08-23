import psycopg2
import urllib.request
import urllib.parse
import re
import unicodedata
from datetime import date


# ==========================================================
# 16 MUNICIPIOS QUE AINDA ESTAO PENDENTES
# ==========================================================

PENDENTES = {
    "5300108": ("DF", "Brasília"),
    "5200852": ("GO", "Americano do Brasil"),
    "5210208": ("GO", "Iporá"),
    "2100709": ("MA", "Anajatuba"),
    "2104909": ("MA", "Guimarães"),
    "2110237": ("MA", "Santana do Maranhão"),
    "2605459": ("PE", "Fernando de Noronha"),
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

    return texto


def slug(texto):
    texto = normalizar(texto)

    texto = texto.replace(
        "(", ""
    ).replace(
        ")", ""
    )

    texto = texto.replace(
        "'",
        ""
    )

    texto = re.sub(
        r"[^A-Z0-9]+",
        "-",
        texto
    )

    return texto.strip("-").lower()


def consultar_ibge(uf, nome):
    """
    Consulta a pagina Cidades e Estados do IBGE.
    O IBGE apresenta o campo Prefeito na pagina municipal.
    """

    tentativas = []

    nome_sem_parenteses = re.sub(
        r"\s*\([^)]*\)",
        "",
        nome
    ).strip()

    tentativas.append(
        slug(nome)
    )

    if nome_sem_parenteses != nome:
        tentativas.append(
            slug(nome_sem_parenteses)
        )

    # Algumas grafias especiais
    tentativas.append(
        slug(
            nome.replace(
                "D'Água",
                "Dagua"
            )
        )
    )

    tentativas = list(
        dict.fromkeys(tentativas)
    )

    for municipio_slug in tentativas:

        url = (
            "https://www.ibge.gov.br/"
            "cidades-e-estados/"
            + uf.lower()
            + "/"
            + municipio_slug
            + ".html"
        )

        print(
            "CONSULTANDO:",
            url
        )

        try:

            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent":
                    "Mozilla/5.0"
                }
            )

            with urllib.request.urlopen(
                req,
                timeout=30
            ) as resposta:

                html = resposta.read().decode(
                    "utf-8",
                    errors="ignore"
                )

        except Exception as e:

            print(
                "  nao abriu:",
                e
            )

            continue


        # Procurar o campo "Prefeito"
        padroes = [
            r'Prefeito</[^>]+>\s*([^<]+)',
            r'Prefeito[^<]{0,100}</[^>]+>\s*([^<]+)',
        ]

        for padrao in padroes:

            encontrados = re.findall(
                padrao,
                html,
                flags=re.IGNORECASE
            )

            for nome_prefeito in encontrados:

                nome_prefeito = re.sub(
                    r"\s+",
                    " ",
                    nome_prefeito
                ).strip()

                nome_prefeito = (
                    nome_prefeito
                    .replace("&nbsp;", " ")
                )

                if (
                    len(nome_prefeito) > 2
                    and len(nome_prefeito) < 150
                ):

                    # Evitar capturar texto que não seja nome
                    if (
                        "SAIBA" not in normalizar(
                            nome_prefeito
                        )
                    ):

                        return nome_prefeito


    return None


print("=" * 70)
print("CARGA FINAL - 16 PREFEITOS PENDENTES")
print("=" * 70)

senha = input(
    "Senha do PostgreSQL: "
)

conn = psycopg2.connect(
    host="localhost",
    dbname="endemiasbr",
    user="postgres",
    password=senha
)

cur = conn.cursor()


# ==========================================================
# CONSULTAR TODOS ANTES DE ALTERAR
# ==========================================================

resultados = {}
problemas = []

print()

for codigo_ibge, (
    uf,
    municipio
) in PENDENTES.items():

    print()
    print(
        codigo_ibge,
        "|",
        uf,
        "|",
        municipio
    )

    # ------------------------------------------------------
    # BRASILIA
    # ------------------------------------------------------

    if codigo_ibge == "5300108":

        resultados[codigo_ibge] = {
            "tipo": "ESPECIAL",
            "nome": None
        }

        print(
            "  BRASILIA/DF: nao possui prefeito municipal."
        )

        continue


    # ------------------------------------------------------
    # FERNANDO DE NORONHA
    # ------------------------------------------------------

    if codigo_ibge == "2605459":

        resultados[codigo_ibge] = {
            "tipo": "ESPECIAL",
            "nome": None
        }

        print(
            "  FERNANDO DE NORONHA: nao e municipio."
        )

        continue


    # ------------------------------------------------------
    # CONSULTA IBGE
    # ------------------------------------------------------

    nome_prefeito = consultar_ibge(
        uf,
        municipio
    )

    if nome_prefeito:

        resultados[codigo_ibge] = {
            "tipo": "PREFEITO",
            "nome": nome_prefeito
        }

        print(
            "  PREFEITO ENCONTRADO:",
            nome_prefeito
        )

    else:

        problemas.append(
            (
                codigo_ibge,
                uf,
                municipio
            )
        )

        print(
            "  PREFEITO NAO ENCONTRADO"
        )


# ==========================================================
# CONFERENCIA ANTES DA GRAVACAO
# ==========================================================

print()
print("=" * 70)
print("CONFERENCIA ANTES DA GRAVACAO")
print("=" * 70)

prefeitos_encontrados = [
    codigo
    for codigo, dados in resultados.items()
    if dados["tipo"] == "PREFEITO"
]

especiais = [
    codigo
    for codigo, dados in resultados.items()
    if dados["tipo"] == "ESPECIAL"
]

print(
    "PREFEITOS ENCONTRADOS:",
    len(prefeitos_encontrados)
)

print(
    "CASOS ESPECIAIS:",
    len(especiais)
)

print(
    "SEM RESULTADO:",
    len(problemas)
)


# ==========================================================
# MOSTRAR TUDO
# ==========================================================

print()

for codigo, dados in resultados.items():

    uf, municipio = PENDENTES[codigo]

    if dados["tipo"] == "PREFEITO":

        print(
            codigo,
            "|",
            uf,
            "|",
            municipio,
            "=>",
            dados["nome"]
        )

    else:

        print(
            codigo,
            "|",
            uf,
            "|",
            municipio,
            "=> CASO ESPECIAL"
        )


if problemas:

    print()
    print(
        "ATENCAO: EXISTEM MUNICIPIOS SEM RESULTADO."
    )

    for codigo, uf, municipio in problemas:

        print(
            codigo,
            "|",
            uf,
            "|",
            municipio
        )

    print()
    print(
        "A CARGA FOI CANCELADA."
    )

    print(
        "NENHUM DADO FOI ALTERADO."
    )

    conn.rollback()
    cur.close()
    conn.close()

    raise SystemExit


# ==========================================================
# GRAVAR SOMENTE OS PREFEITOS ENCONTRADOS
# ==========================================================

print()
print(
    "Todos os municipios normais foram identificados."
)

print(
    "Gravando..."
)

atualizados = 0

for codigo, dados in resultados.items():

    if dados["tipo"] != "PREFEITO":
        continue

    nome_prefeito = dados["nome"]

    cur.execute("""
        SELECT id
        FROM municipios
        WHERE codigo_ibge = %s
    """, (
        codigo,
    ))

    resultado = cur.fetchone()

    if not resultado:
        print(
            "MUNICIPIO NAO ENCONTRADO NO BANCO:",
            codigo
        )
        continue

    municipio_id = resultado[0]

    cur.execute("""
        UPDATE autoridades
        SET
            nome = %s,
            ativo = TRUE,
            fonte =
                'IBGE - Cidades e Estados',
            data_verificacao = %s,
            observacao =
                'Prefeito obtido da pagina municipal do IBGE.'
        WHERE esfera = 'MUNICIPAL'
          AND municipio_id = %s
          AND cargo = 'Prefeito'
    """, (
        nome_prefeito,
        date.today(),
        municipio_id
    ))

    atualizados += cur.rowcount


# ==========================================================
# CASOS ESPECIAIS
# ==========================================================

# Brasília:
# não existe prefeito municipal.
# Não alteramos o registro.


# Fernando de Noronha:
# não é município.
# Não alteramos o registro.


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

pendentes_finais = cur.fetchone()[0]


print()
print("=" * 70)
print("CARGA FINAL CONCLUIDA")
print("=" * 70)

print(
    "PREFEITOS ATUALIZADOS AGORA:",
    atualizados
)

print(
    "PREFEITOS PREENCHIDOS NO BANCO:",
    preenchidos
)

print(
    "REGISTROS AINDA A CADASTRAR:",
    pendentes_finais
)

print("=" * 70)

cur.close()
conn.close()