import fitz
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

print("Abrindo PDF...")
doc = fitz.open(PDF_PATH)

localidades = []
print(f"Total de páginas: {len(doc)}")

for num, pagina in enumerate(doc, 1):
    texto = pagina.get_text("text")
    palavras = [p.strip() for p in texto.split("\n") if p.strip()]

    i = 0
    while i < len(palavras):
        # Procura um número (código da localidade)
        if palavras[i].isdigit() and len(palavras[i]) <= 4:
            codigo = palavras[i]
            
            # Próximas palavras podem ser o nome
            nome_partes = []
            j = i + 1
            while j < len(palavras) and not palavras[j].isdigit() and palavras[j].upper() not in ["VILA", "BAIRRO", "POVOADO", "FAZENDA", "SITIO", "DISTRITO", "CIDADE", "OUTRO", "CONJUNTO", "ATIVA", "EXTINTA", "RURAL", "URBANA"]:
                nome_partes.append(palavras[j])
                j += 1
                if len(nome_partes) > 6:
                    break

            nome = " ".join(nome_partes).strip()
            
            tipo = "Outro"
            status = "Ativa"
            cod_ibge = None

            # Procura tipo, status e código IBGE nas próximas palavras
            for k in range(i, min(i+20, len(palavras))):
                p = palavras[k].upper()
                if p in ["VILA", "BAIRRO", "POVOADO", "FAZENDA", "SITIO", "DISTRITO", "CIDADE", "CONJUNTO"]:
                    tipo = p.title()
                if p in ["ATIVA", "EXTINTA"]:
                    status = p.title()
                if re.match(r"^29\d{4}$", palavras[k]):
                    cod_ibge = palavras[k]

            if nome and cod_ibge and len(nome) > 2:
                localidades.append({
                    "nome": nome,
                    "tipo": tipo,
                    "cod_ibge": cod_ibge,
                    "status": status
                })
            
            i = j
        else:
            i += 1

    if num % 30 == 0:
        print(f"Processadas {num} páginas... ({len(localidades)} localidades)")

doc.close()
print(f"\nTotal extraído: {len(localidades)}")

print("Inserindo no banco...")
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

print("\n===== RESULTADO =====")
print(f"Inseridas:     {inseridos}")
print(f"Já existiam:   {ja_existem}")
print(f"Erros:         {erros}")
print("=====================")