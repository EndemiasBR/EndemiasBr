import os
import xml.etree.ElementTree as ET
from collections import Counter
import psycopg2

BASE = r"C:\EndemiasBR\kml"

NS = {"k": "http://www.opengis.net/kml/2.2"}

print("=" * 70)
print("DIAGNOSTICO - LOCALIDADES IBGE x SISLOC")
print("=" * 70)

# ---------------------------------------------------------
# 1. Ler localidades existentes no SISLOC
# ---------------------------------------------------------

print()
print("Lendo localidades existentes no SisLoc...")

senha = input("Senha do PostgreSQL: ")

conn = psycopg2.connect(
    host="localhost",
    dbname="endemiasbr",
    user="postgres",
    password=senha
)

cur = conn.cursor()

cur.execute("""
    SELECT
        id,
        municipio_id,
        codigo_localidade,
        nome
    FROM localidades
    WHERE codigo_localidade IS NOT NULL
      AND TRIM(codigo_localidade) <> ''
""")

sisloc = {}

for id_localidade, municipio_id, codigo, nome in cur.fetchall():
    codigo = str(codigo).strip()

    if codigo not in sisloc:
        sisloc[codigo] = {
            "id": id_localidade,
            "municipio_id": municipio_id,
            "nome": nome
        }

cur.close()
conn.close()

print("LOCALIDADES NO SISLOC:", len(sisloc))

# ---------------------------------------------------------
# 2. Ler todos os KML do IBGE
# ---------------------------------------------------------

print()
print("Lendo arquivos KML do IBGE...")
print("Aguarde...")

ibge = {}
duplicados = Counter()

arquivos = 0
placemarks = 0
sem_codigo = 0
erros = 0

for uf in sorted(os.listdir(BASE)):

    pasta = os.path.join(BASE, uf)

    if not os.path.isdir(pasta):
        continue

    for arquivo in os.listdir(pasta):

        if not arquivo.lower().endswith(".kml"):
            continue

        arquivos += 1

        caminho = os.path.join(pasta, arquivo)

        try:
            root = ET.parse(caminho).getroot()
        except Exception as e:
            erros += 1
            print("ERRO:", caminho)
            print(e)
            continue

        for placemark in root.findall(".//k:Placemark", NS):

            placemarks += 1

            dados = {}

            for campo in placemark.findall(".//k:SimpleData", NS):
                nome_campo = campo.attrib.get("name")
                dados[nome_campo] = (campo.text or "").strip()

            codigo_localidade = dados.get("CD_LOCALIDADE", "").strip()

            if not codigo_localidade:
                sem_codigo += 1
                continue

            registro = {
                "codigo_localidade": codigo_localidade,
                "codigo_municipio": dados.get("CD_MUN", "").strip(),
                "nome_municipio": dados.get("NM_MUN", "").strip(),
                "nome_localidade": dados.get("NM_LOCALIDADE", "").strip(),
                "tipo": dados.get("CT_LOCALIDADE", "").strip(),
                "subtipo": dados.get("SCT_LOCALIDADE", "").strip(),
                "latitude": dados.get("LAT_LOCALIDADE", "").strip(),
                "longitude": dados.get("LONG_LOCALIDADE", "").strip(),
                "uf": dados.get("SIGLA_UF", "").strip()
            }

            if codigo_localidade in ibge:
                duplicados[codigo_localidade] += 1
            else:
                ibge[codigo_localidade] = registro

# ---------------------------------------------------------
# 3. Comparação
# ---------------------------------------------------------

codigos_ibge = set(ibge.keys())
codigos_sisloc = set(sisloc.keys())

novas = codigos_ibge - codigos_sisloc
existentes = codigos_ibge & codigos_sisloc

sisloc_sem_ibge = codigos_sisloc - codigos_ibge

# ---------------------------------------------------------
# 4. Verificar município
# ---------------------------------------------------------

cur = conn = None

# ---------------------------------------------------------
# 5. Resultado
# ---------------------------------------------------------

print()
print("=" * 70)
print("RESULTADO")
print("=" * 70)

print("ARQUIVOS KML:", arquivos)
print("PLACEMARKS:", placemarks)
print("SEM CD_LOCALIDADE:", sem_codigo)
print("ERROS DE LEITURA:", erros)

print()
print("LOCALIDADES IBGE UNICAS:", len(codigos_ibge))
print("LOCALIDADES SISLOC:", len(codigos_sisloc))

print()
print("NOVAS LOCALIDADES:", len(novas))
print("JA EXISTEM NO SISLOC:", len(existentes))
print("SISLOC SEM CORRESPONDENCIA NO IBGE:", len(sisloc_sem_ibge))

print()
print("DUPLICACOES NOS KML:", sum(duplicados.values()))
print("CODIGOS QUE SE REPETEM:", len(duplicados))

# ---------------------------------------------------------
# 6. Mostrar algumas novas
# ---------------------------------------------------------

print()
print("-" * 70)
print("PRIMEIRAS 30 LOCALIDADES QUE SERIAM NOVAS")
print("-" * 70)

for codigo in sorted(novas)[:30]:

    r = ibge[codigo]

    print(
        codigo,
        "|",
        r["uf"],
        "|",
        r["nome_municipio"],
        "|",
        r["nome_localidade"],
        "|",
        r["tipo"]
    )

# ---------------------------------------------------------
# 7. Mostrar registros existentes
# ---------------------------------------------------------

print()
print("-" * 70)
print("PRIMEIRAS 20 LOCALIDADES QUE JA EXISTEM")
print("-" * 70)

for codigo in sorted(existentes)[:20]:

    r = ibge[codigo]

    print(
        codigo,
        "| IBGE:",
        r["nome_localidade"],
        "| SISLOC:",
        sisloc[codigo]["nome"]
    )

# ---------------------------------------------------------
# 8. Mostrar localidades do SISLOC sem IBGE
# ---------------------------------------------------------

print()
print("-" * 70)
print("PRIMEIRAS 20 LOCALIDADES DO SISLOC SEM IBGE")
print("-" * 70)

for codigo in sorted(sisloc_sem_ibge)[:20]:

    r = sisloc[codigo]

    print(
        codigo,
        "|",
        r["nome"]
    )

print()
print("=" * 70)
print("DIAGNOSTICO CONCLUIDO")
print("NENHUM DADO FOI ALTERADO NO BANCO.")
print("=" * 70)