import os
import xml.etree.ElementTree as ET
import psycopg2

BASE = r"C:\EndemiasBR\kml"
NS = {"k": "http://www.opengis.net/kml/2.2"}

senha = input("Senha do PostgreSQL: ")

conn = psycopg2.connect(
    host="localhost",
    dbname="endemiasbr",
    user="postgres",
    password=senha
)

cur = conn.cursor()

cur.execute("""
    SELECT codigo_ibge, id, nome
    FROM municipios
""")

municipios = {}

for codigo, municipio_id, nome in cur.fetchall():
    municipios[str(codigo).strip()] = (municipio_id, nome)

codigos_localidades = set()
municipios_kml = set()
sem_municipio = set()

arquivos = 0

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
        except Exception:
            continue

        for placemark in root.findall(".//k:Placemark", NS):

            dados = {}

            for campo in placemark.findall(".//k:SimpleData", NS):
                dados[campo.attrib.get("name")] = (campo.text or "").strip()

            codigo_localidade = dados.get("CD_LOCALIDADE", "")
            codigo_municipio = dados.get("CD_MUN", "")

            if not codigo_localidade:
                continue

            codigos_localidades.add(codigo_localidade)
            municipios_kml.add(codigo_municipio)

            if codigo_municipio not in municipios:
                sem_municipio.add(codigo_municipio)

cur.close()
conn.close()

print()
print("=" * 65)
print("VERIFICACAO DE VINCULO IBGE -> SISLOC")
print("=" * 65)

print("ARQUIVOS KML:", arquivos)
print("LOCALIDADES UNICAS:", len(codigos_localidades))
print("MUNICIPIOS ENCONTRADOS NOS KML:", len(municipios_kml))
print("MUNICIPIOS NO SISLOC:", len(municipios))

print()
print("CODIGOS DE MUNICIPIO SEM CORRESPONDENCIA:", len(sem_municipio))

if sem_municipio:
    print()
    print("MUNICIPIOS SEM CORRESPONDENCIA:")
    for codigo in sorted(sem_municipio):
        print(codigo)

print()
print("=" * 65)

if not sem_municipio:
    print("OK - TODAS AS LOCALIDADES POSSUEM MUNICIPIO NO SISLOC")
else:
    print("ATENCAO - EXISTEM LOCALIDADES SEM MUNICIPIO")

print("=" * 65)
print("NENHUM DADO FOI ALTERADO.")