import re
import psycopg2

PDF_TXT = "localidades_raw.txt"   # o texto que extraímos
SENHA = "Amor2806"

def conectar():
    return psycopg2.connect(
        host="localhost",
        database="endemiasbr",
        user="postgres",
        password=SENHA,
        port="5432",
        client_encoding="latin1"
    )

with open(PDF_TXT, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

pattern = re.compile(
    r'^\s*(\d+)\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-ZÁÉÍÓÚÂÊÔÃÕÇa-záéíóúâêôãõç0-9\s\.\-\']{1,50}?)\s+(VILA|BAIRRO|POVOADO|FAZENDA|SITIO|DISTRITO|CIDADE|OUTRO|CONJUNTO|ACENTAMENTO|ACAMPAMENTO)?.*?(\d{6}).*?(Ativa|Extinta)',
    re.MULTILINE | re.IGNORECASE
)

matches = pattern.findall(content)
print(f"Encontradas: {len(matches)}")

conn = conectar()
cur = conn.cursor()

inseridos = 0
erros = 0

for m in matches:
    codigo, nome, tipo, cod_ibge, status = m
    nome = nome.strip()
    tipo = tipo.strip().title() if tipo else "Outro"
    status = status.strip().title()

    if len(nome) < 2:
        continue

    try:
        cur.execute("SELECT id FROM municipios WHERE codigo_ibge = %s", (cod_ibge,))
        res = cur.fetchone()
        if not res:
            erros += 1
            continue

        cur.execute("""
            INSERT INTO localidades (municipio_id, nome, tipo, status)
            SELECT %s, %s, %s, %s
            WHERE NOT EXISTS (
                SELECT 1 FROM localidades 
                WHERE municipio_id = %s AND upper(nome) = upper(%s)
            )
        """, (res[0], nome, tipo, status, res[0], nome))
        inseridos += 1
    except Exception as e:
        erros += 1

conn.commit()
cur.close()
conn.close()

print(f"Inseridos: {inseridos}")
print(f"Erros/ignorados: {erros}")