import webbrowser

url = "https://siops.datasus.gov.br/conselho.php"

print("=" * 70)
print("CONSULTA CADASTRAL SIOPS")
print("=" * 70)
print()
print("Abrindo o SIOPS...")
print()
print("Esta consulta deve ser usada para:")
print("  - Prefeitos")
print("  - Secretarios Municipais de Saude")
print()
print("NAO usar a consulta de situacao de entrega/transmissao.")
print()

webbrowser.open(url)

print("SIOPS aberto no navegador.")
print()
print("Depois selecione a consulta cadastral de:")
print("Prefeitos, Contadores e Secretarios de Saude.")