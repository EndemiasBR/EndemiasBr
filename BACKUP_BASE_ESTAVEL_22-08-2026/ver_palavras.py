import fitz
doc = fitz.open("localidades-BA01082026.pdf")
pagina = doc[2]
texto = pagina.get_text("text")
palavras = [p.strip() for p in texto.split("\n") if p.strip()]
print(palavras[:80])
doc.close()