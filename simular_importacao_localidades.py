import os
import xml.etree.ElementTree as ET
from collections import Counter

BASE = r"C:\EndemiasBR\kml"

NS = {"k": "http://www.opengis.net/kml/2.2"}

total_placemarks = 0
total_com_codigo = 0
total_sem_codigo = 0
total_unicos = 0
total_duplicados = 0

arquivos = 0
estados = 0

por_estado = Counter()
duplicados = Counter()

for uf in sorted(os.listdir(BASE)):
    pasta_uf = os.path.join(BASE, uf)

    if not os.path.isdir(pasta_uf):
        continue

    estados += 1

    for arquivo in os.listdir(pasta_uf):

        if not arquivo.lower().endswith(".kml"):
            continue

        caminho = os.path.join(pasta_uf, arquivo)
        arquivos += 1

        try:
            root = ET.parse(caminho).getroot()
        except Exception as e:
            print(f"ERRO AO LER: {caminho}")
            print(e)
            continue

        placemarks = root.findall(".//k:Placemark", NS)

        codigos = []

        for placemark in placemarks:

            total_placemarks += 1

            dados = {}

            for campo in placemark.findall(".//k:SimpleData", NS):
                nome = campo.attrib.get("name")
                dados[nome] = (campo.text or "").strip()

            codigo = dados.get("CD_LOCALIDADE", "").strip()

            # O Placemark do município não é uma localidade
            if not codigo:
                total_sem_codigo += 1
                continue

            total_com_codigo += 1
            codigos.append(codigo)

        unicos_arquivo = set(codigos)

        total_unicos += len(unicos_arquivo)

        repetidos = len(codigos) - len(unicos_arquivo)

        total_duplicados += repetidos

        if repetidos:
            for codigo, quantidade in Counter(codigos).items():
                if quantidade > 1:
                    duplicados[codigo] += quantidade - 1

        por_estado[uf] += len(unicos_arquivo)


print()
print("=" * 60)
print("SIMULACAO DA IMPORTACAO DE LOCALIDADES IBGE")
print("=" * 60)

print(f"ESTADOS ENCONTRADOS: {estados}")
print(f"ARQUIVOS KML: {arquivos}")
print(f"PLACEMARKS: {total_placemarks}")
print(f"COM CD_LOCALIDADE: {total_com_codigo}")
print(f"SEM CD_LOCALIDADE: {total_sem_codigo}")
print(f"LOCALIDADES UNICAS: {total_unicos}")
print(f"DUPLICADAS NOS KML: {total_duplicados}")

print()
print("LOCALIDADES UNICAS POR ESTADO")
print("-" * 60)

for uf in sorted(por_estado):
    print(f"{uf}: {por_estado[uf]}")

print()
print("CODIGOS DUPLICADOS ENCONTRADOS")
print("-" * 60)

for codigo, quantidade in sorted(duplicados.items()):
    print(f"{codigo}: {quantidade} duplicacao(oes)")

print()
print("=" * 60)
print("SIMULACAO CONCLUIDA - NENHUM DADO FOI GRAVADO NO BANCO")
print("=" * 60)