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
print(f"Total de páginas: {len(doc)}")

localidades = []

for num, pagina in enumerate(doc, 1):
    texto = pagina.get_text("text")
    palavras = [p.strip() for p in texto.split("\n") if p.strip()]

    i = 0
    while i < len(palavras) - 5:
        # Procura código IBGE (6 dígitos começando com 29)
        if re.match(r"^29\d{4}$", palavras[i]):
            cod_ibge = palavras[i]
            
            # Volta algumas palavras para pegar o nome e o tipo
            # O padrão observado: ... NOME  TIPO  ...  CODIGO_IBGE ...
            nome = None
            tipo = "Outro"
            status = "Ativa"

            # Procura para trás o nome
            for k in range(i-1, max(0, i-15), -1):
                p = palavras[k]
                if p.upper() in ["VILA", "BAIRRO", "POVOADO", "FAZENDA", "SITIO", "DISTRITO", "CIDADE", "CONJUNTO"]:
                    tipo = p.title()
                elif p.upper() in ["ATIVA", "EXTINTA"]:
                    status = p.title()
                elif not p.isdigit() and len(p) > 2 and not p.startswith("0") and " " not in p:
                    # candidato a nome
                    if nome is None:
                        nome = p
                    else:
                        nome = p + " " + nome
                        break

            if nome and len(nome) > 2:
                localidades.append({
                    "nome": nome.strip(),
                    "tipo": tipo,
                    "cod_ibge": cod_ibge,
                    "status": status
                })
        i += 1

    if num % 30 == 0:
        print(f"Processadas {num} páginas... ({len(localidades)} localidades)")

doc.close()
print(f"\nTotal extraído: {len(localidades)}")

# Mostra alguns exemplos
print("\nExemplos extraídos:")
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

print("\n===== RESULTADO =====")
print(f"Inseridas:     {inseridos}")
print(f"Já existiam:   {ja_existem}")
print(f"Erros:         {erros}")
print("=====================")