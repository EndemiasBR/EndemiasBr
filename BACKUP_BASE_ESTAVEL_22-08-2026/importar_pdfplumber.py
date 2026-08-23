import pdfplumber
import psycopg2
import re

PDF_PATH = "localidades-BA01082026.pdf"
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

print("Abrindo PDF com pdfplumber...")
localidades = []

with pdfplumber.open(PDF_PATH) as pdf:
    print(f"Total de páginas: {len(pdf.pages)}")
    
    for i, pagina in enumerate(pdf.pages, 1):
        texto = pagina.extract_text() or ""
        linhas = texto.split("\n")
        
        for linha in linhas:
            # Ignora cabeçalhos e rodapés
            if any(x in linha for x in ["UF:", "Relatório", "Ministério", "Página", "Fonte de dados", "Filtros:", "Código", "Qtd"]):
                continue
                
            # Tenta encontrar padrão: número + nome + ... + código IBGE 29xxxx + status
            match = re.search(
                r"(\d+)\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-ZÁÉÍÓÚÂÊÔÃÕÇa-záéíóúâêôãõç0-9\s\.\-\']{2,40}?)\s+.*?(29\d{4}).*?(Ativa|Extinta)",
                linha, re.IGNORECASE
            )
            
            if match:
                codigo = match.group(1)
                nome = match.group(2).strip()
                cod_ibge = match.group(3)
                status = match.group(4).title()
                
                # Tenta capturar o tipo
                tipo = "Outro"
                for t in ["VILA", "BAIRRO", "POVOADO", "FAZENDA", "SITIO", "DISTRITO", "CIDADE", "CONJUNTO"]:
                    if t in linha.upper():
                        tipo = t.title()
                        break
                
                if len(nome) > 2:
                    localidades.append({
                        "nome": nome,
                        "tipo": tipo,
                        "cod_ibge": cod_ibge,
                        "status": status
                    })
        
        if i % 30 == 0:
            print(f"Página {i}... {len(localidades)} localidades")

print(f"\nTotal extraído: {len(localidades)}")

if localidades:
    print("Exemplos:")
    for loc in localidades[:5]:
        print(loc)

print("\nInserindo no banco...")
conn = conectar()
cur = conn.cursor()

inseridos = 0
erros = 0
ja_existem = 0

for loc in localidades:
    try:
        cur.execute("SELECT id FROM municipios WHERE codigo_ibge = %s", (loc["cod_ibge"],))
        res = cur.fetchone()
        if not res:
            erros += 1
            continue

        municipio_id = res[0]

        cur.execute("""
            SELECT 1 FROM localidades 
            WHERE municipio_id = %s AND upper(nome) = upper(%s)
        """, (municipio_id, loc["nome"]))
        
        if cur.fetchone():
            ja_existem += 1
            continue

        cur.execute("""
            INSERT INTO localidades (municipio_id, nome, tipo, status)
            VALUES (%s, %s, %s, %s)
        """, (municipio_id, loc["nome"], loc["tipo"], loc["status"]))
        inseridos += 1

    except Exception as e:
        erros += 1

conn.commit()
cur.close()
conn.close()

print("\n===== RESULTADO FINAL =====")
print(f"Inseridas:     {inseridos}")
print(f"Já existiam:   {ja_existem}")
print(f"Erros:         {erros}")
print("===========================")