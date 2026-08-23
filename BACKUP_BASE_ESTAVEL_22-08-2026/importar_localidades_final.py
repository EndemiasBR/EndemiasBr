import fitz  # PyMuPDF
import psycopg2
import re

# ==================== CONFIGURAÇÃO ====================
PDF_PATH = "localidades-BA01082026.pdf"
SENHA_BANCO = "Amor2806"
# ======================================================

def conectar():
    return psycopg2.connect(
        host="localhost",
        database="endemiasbr",
        user="postgres",
        password=SENHA_BANCO,
        port="5432",
        client_encoding="latin1"
    )

print("Abrindo PDF...")
doc = fitz.open(PDF_PATH)

localidades = []
print(f"Total de páginas: {len(doc)}")

for num, pagina in enumerate(doc, 1):
    texto = pagina.get_text("text")
    linhas = texto.split("\n")

    for i, linha in enumerate(linhas):
        # Padrão principal
        match = re.search(
            r"(\d+)\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-ZÁÉÍÓÚÂÊÔÃÕÇa-záéíóúâêôãõç0-9\s\.\-\']{1,45}?)\s+(VILA|BAIRRO|POVOADO|FAZENDA|SITIO|DISTRITO|CIDADE|OUTRO|CONJUNTO|ACENTAMENTO|ACAMPAMENTO)?",
            linha, re.IGNORECASE
        )
        if match:
            codigo = match.group(1)
            nome = match.group(2).strip()
            tipo = match.group(3).title() if match.group(3) else "Outro"

            # Pega bloco das próximas linhas para encontrar IBGE e Status
            bloco = " ".join(linhas[i:i+6])
            
            status_match = re.search(r"(Ativa|Extinta)", bloco, re.IGNORECASE)
            status = status_match.group(1).title() if status_match else "Ativa"

            ibge_match = re.search(r"\b(29\d{4})\b", bloco)
            if ibge_match and len(nome) > 2:
                localidades.append({
                    "nome": nome,
                    "tipo": tipo,
                    "cod_ibge": ibge_match.group(1),
                    "status": status
                })

    if num % 20 == 0:
        print(f"Processadas {num} páginas... ({len(localidades)} localidades até agora)")

doc.close()
print(f"\nTotal de localidades extraídas: {len(localidades)}")

print("Conectando ao banco...")
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

        # Verifica se já existe
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

print("\n===== RESULTADO =====")
print(f"Inseridas:     {inseridos}")
print(f"Já existiam:   {ja_existem}")
print(f"Erros:         {erros}")
print("=====================")