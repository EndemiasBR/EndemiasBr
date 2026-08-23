import fitz  # PyMuPDF
import psycopg2
import re

# ==================== CONFIGURAÇÃO ====================
PDF_PATH = "localidades-BA01082026.pdf"
SENHA = "Amor2806"
# ======================================================

def conectar():
    return psycopg2.connect(
        host="localhost",
        database="endemiasbr",
        user="postgres",
        password=SENHA,
        port="5432",
        client_encoding="latin1"
    )

def processar_pdf(caminho):
    doc = fitz.open(caminho)
    localidades = []

    for pagina in doc:
        texto = pagina.get_text("text")
        linhas = texto.split("\n")

        for i, linha in enumerate(linhas):
            # Procura padrões de código + nome + categoria + município + status
            match = re.search(
                r"(\d+)\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-ZÁÉÍÓÚÂÊÔÃÕÇa-záéíóúâêôãõç\s\.\-\']{2,40}?)\s+(VILA|BAIRRO|POVOADO|FAZENDA|SITIO|DISTRITO|CIDADE|OUTRO|CONJUNTO)",
                linha, re.IGNORECASE
            )
            if match:
                codigo = match.group(1)
                nome = match.group(2).strip()
                tipo = match.group(3).title()

                # Tenta pegar município e status nas linhas próximas
                bloco = " ".join(linhas[i:i+5])
                status_match = re.search(r"(Ativa|Extinta)", bloco, re.IGNORECASE)
                status = status_match.group(1).title() if status_match else "Ativa"

                # Código IBGE geralmente é 6 dígitos
                ibge_match = re.search(r"\b(29\d{4})\b", bloco)
                cod_ibge = ibge_match.group(1) if ibge_match else None

                if cod_ibge and len(nome) > 2:
                    localidades.append({
                        "nome": nome,
                        "tipo": tipo,
                        "cod_ibge": cod_ibge,
                        "status": status
                    })

    doc.close()
    return localidades

def inserir(localidades):
    conn = conectar()
    cur = conn.cursor()
    inseridos = 0
    erros = 0

    for loc in localidades:
        try:
            cur.execute("SELECT id FROM municipios WHERE codigo_ibge = %s", (loc["cod_ibge"],))
            res = cur.fetchone()
            if not res:
                erros += 1
                continue

            cur.execute("""
                INSERT INTO localidades (municipio_id, nome, tipo, status)
                VALUES (%s, %s, %s, %s)
            """, (res[0], loc["nome"], loc["tipo"], loc["status"]))
            inseridos += 1
        except Exception as e:
            erros += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"Inseridos: {inseridos} | Erros: {erros}")

if __name__ == "__main__":
    print("Processando PDF...")
    locs = processar_pdf(PDF_PATH)
    print(f"Encontradas aproximadamente: {len(locs)}")
    inserir(locs)