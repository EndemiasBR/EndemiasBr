import psycopg2
from datetime import date

senha = input("Senha do PostgreSQL: ")

c = psycopg2.connect(
    host="localhost",
    dbname="endemiasbr",
    user="postgres",
    password=senha
)

x = c.cursor()

print()
print("=" * 70)
print("CARGA INICIAL DE AUTORIDADES")
print("=" * 70)

# ---------------------------------------------------------
# FUNÇÃO DE INSERÇÃO
# ---------------------------------------------------------

def inserir(nome, cargo, esfera, estado_id=None,
            regional_id=None, municipio_id=None,
            fonte=None):

    x.execute("""
        INSERT INTO autoridades (
            nome,
            cargo,
            esfera,
            estado_id,
            regional_id,
            municipio_id,
            data_inicio,
            ativo,
            fonte,
            data_verificacao
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,TRUE,%s,%s)
    """, (
        nome,
        cargo,
        esfera,
        estado_id,
        regional_id,
        municipio_id,
        date.today(),
        fonte,
        date.today()
    ))


# ---------------------------------------------------------
# FEDERAL
# ---------------------------------------------------------

print()
print("Cadastrando autoridades federais...")

inserir(
    "Luiz Inácio Lula da Silva",
    "Presidente da República",
    "FEDERAL",
    fonte="Presidência da República"
)

inserir(
    "Alexandre Rocha Santos Padilha",
    "Ministro da Saúde",
    "FEDERAL",
    fonte="Ministério da Saúde"
)

print("FEDERAL: 2 autoridades")


# ---------------------------------------------------------
# RESULTADO
# ---------------------------------------------------------

c.commit()

x.execute("SELECT COUNT(*) FROM autoridades")

total = x.fetchone()[0]

print()
print("=" * 70)
print("CARGA CONCLUIDA")
print("=" * 70)
print("TOTAL DE AUTORIDADES:", total)
print()
print("ATENCAO:")
print("Neste primeiro passo foram inseridas somente as autoridades")
print("federais oficialmente confirmadas.")
print()
print("Os demais níveis serão carregados em lote depois da")
print("consolidação das respectivas fontes.")
print("=" * 70)

x.close()
c.close()