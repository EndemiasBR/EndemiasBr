import os
import xml.etree.ElementTree as ET
import psycopg2

BASE = r"C:\EndemiasBR\kml"
NS = {"k": "http://www.opengis.net/kml/2.2"}

print("=" * 70)
print("IMPORTACAO NACIONAL DE LOCALIDADES IBGE 2022")
print("=" * 70)

senha = input("Senha do PostgreSQL: ")

conn = psycopg2.connect(
    host="localhost",
    dbname="endemiasbr",
    user="postgres",
    password=senha
)

cur = conn.cursor()

# ---------------------------------------------------------
# MUNICIPIOS DO SISLOC
# ---------------------------------------------------------

cur.execute("""
    SELECT id, codigo_ibge, nome, regional_id
    FROM municipios
""")

municipios = {}

for municipio_id, codigo_ibge, nome, regional_id in cur.fetchall():
    codigo_ibge = str(codigo_ibge).strip()

    municipios[codigo_ibge] = {
        "id": municipio_id,
        "nome": nome,
        "regional_id": regional_id
    }

print("MUNICIPIOS CARREGADOS:", len(municipios))

# ---------------------------------------------------------
# LER KMLS
# ---------------------------------------------------------

localidades = {}

arquivos = 0
placemarks = 0
sem_codigo = 0
duplicados = 0
erros = 0

print()
print("Lendo os KML do IBGE...")

for uf in sorted(os.listdir(BASE)):

    pasta_uf = os.path.join(BASE, uf)

    if not os.path.isdir(pasta_uf):
        continue

    for arquivo in os.listdir(pasta_uf):

        if not arquivo.lower().endswith(".kml"):
            continue

        arquivos += 1

        caminho = os.path.join(pasta_uf, arquivo)

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

            # Placemark do municipio, sem codigo de localidade
            if not codigo_localidade:
                sem_codigo += 1
                continue

            # Elimina duplicidade pelo codigo oficial
            if codigo_localidade in localidades:
                duplicados += 1
                continue

            codigo_municipio = dados.get("CD_MUN", "").strip()

            if codigo_municipio not in municipios:
                raise Exception(
                    f"Municipio nao encontrado no SisLoc: "
                    f"{codigo_municipio} - "
                    f"{dados.get('NM_MUN', '')}"
                )

            localidades[codigo_localidade] = {
                "municipio_id": municipios[codigo_municipio]["id"],
                "regional_id": municipios[codigo_municipio]["regional_id"],
                "nome": dados.get("NM_LOCALIDADE", "").strip(),
                "tipo": dados.get("CT_LOCALIDADE", "").strip(),
                "codigo": codigo_localidade,
                "latitude": dados.get("LAT_LOCALIDADE", "").strip(),
                "longitude": dados.get("LONG_LOCALIDADE", "").strip(),
                "codigo_localidade": codigo_localidade
            }

print()
print("ARQUIVOS KML:", arquivos)
print("PLACEMARKS:", placemarks)
print("SEM CD_LOCALIDADE:", sem_codigo)
print("DUPLICADOS IGNORADOS:", duplicados)
print("LOCALIDADES UNICAS:", len(localidades))
print("ERROS DE LEITURA:", erros)

# ---------------------------------------------------------
# IMPORTACAO
# ---------------------------------------------------------

print()
print("Gravando localidades no banco...")

inseridos = 0

try:

    for codigo, r in localidades.items():

        cur.execute("""
            INSERT INTO localidades (
                municipio_id,
                nome,
                tipo,
                codigo,
                latitude,
                longitude,
                ativa,
                status,
                regional_id,
                codigo_localidade
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                NULLIF(%s, '')::numeric,
                NULLIF(%s, '')::numeric,
                TRUE,
                'Ativa',
                %s,
                %s
            )
        """, (
            r["municipio_id"],
            r["nome"][:150],
            r["tipo"][:50],
            r["codigo"][:30],
            r["latitude"],
            r["longitude"],
            r["regional_id"],
            r["codigo_localidade"][:20]
        ))

        inseridos += 1

    conn.commit()

except Exception as e:

    conn.rollback()

    print()
    print("=" * 70)
    print("ERRO - ROLLBACK EXECUTADO")
    print("=" * 70)
    print(e)
    print("NENHUM REGISTRO DESTA IMPORTACAO FOI GRAVADO.")

    cur.close()
    conn.close()

    raise SystemExit(1)

# ---------------------------------------------------------
# CONFERENCIA FINAL
# ---------------------------------------------------------

cur.execute("SELECT COUNT(*) FROM localidades")
total_banco = cur.fetchone()[0]

cur.execute("""
    SELECT COUNT(DISTINCT codigo_localidade)
    FROM localidades
    WHERE codigo_localidade IS NOT NULL
""")

codigos_unicos = cur.fetchone()[0]

cur.close()
conn.close()

print()
print("=" * 70)
print("IMPORTACAO CONCLUIDA")
print("=" * 70)

print("REGISTROS INSERIDOS:", inseridos)
print("TOTAL DE LOCALIDADES NO BANCO:", total_banco)
print("CODIGOS DE LOCALIDADE UNICOS:", codigos_unicos)

print()
print("IMPORTACAO REALIZADA COM SUCESSO.")
print("=" * 70)