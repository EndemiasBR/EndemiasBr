import fitz

doc = fitz.open("localidades-BA01082026.pdf")
pagina = doc[0]  # primeira página
texto = pagina.get_text("text")
print(texto[:2000])  # mostra os primeiros 2000 caracteres
doc.close()