import psycopg2
from datetime import date

print("=" * 70)
print("CARGA CONTROLADA DOS PREFEITOS CONFIRMADOS")
print("=" * 70)

senha = input("Senha do PostgreSQL: ")

conn = psycopg2.connect(
    host="localhost",
    dbname="endemiasbr",
    user="postgres",
    password=senha
)

cur = conn.cursor()

# ==========================================================
# SOMENTE OS CASOS CONFIRMADOS PELO DIAGNOSTICO
# ==========================================================
#
# 4 correspondencias exatas
# + 54 correspondencias aproximadas >= 90%
#
# Os 3 casos abaixo de 90% NÃO entram.
# Os 11 sem correspondencia segura NÃO entram.
# Brasilia e Fernando de Noronha NÃO entram.
# ==========================================================

prefeitos = {

    # ------------------------------------------------------
    # ALAGOAS
    # ------------------------------------------------------

    "2705705": "JOSÉ LUIZ VASCONCELLOS DOS ANJOS",
    "2705804": "CARLOS ALBERTO BEZERRA DA SILVA",
    "2705903": "MARIA SUZANICE HIGINO BAHÉ",
    "2709004": "JUVENIL LOPES DE OLIVEIRA",

    # ------------------------------------------------------
    # BAHIA
    # ------------------------------------------------------

    "2905602": "PAULO CESAR BOMFIM DE OLIVEIRA",
    "2910057": "ALBERTO PEREIRA CASTRO",
    "2922250": "AILSON DE SOUZA SELIS",
    "2928505": "AGNALDO FIGUEIREDO ANDRADE",

    # ------------------------------------------------------
    # GOIAS
    # ------------------------------------------------------

    "5220009": "GENIVAM GONÇALVES DOS SANTOS",
    "5220702": "ORLANDO JOSE DA SILVA NETO",

    # ------------------------------------------------------
    # MARANHAO
    # ------------------------------------------------------

    "2107407": "CLEDIVAL DE ALCANTARA SOUZA",

    # ------------------------------------------------------
    # MINAS GERAIS
    # ------------------------------------------------------

    "3145455": "RODRIGO VIEIRA DE MATOS",
    "3147808": "EDSON DO NASCIMENTO",
    "3150539": "ARTUR CARLOS DA SILVA",
    "3165560": "EDER ELÓI ALVES PENA",

    # ------------------------------------------------------
    # MATO GROSSO
    # ------------------------------------------------------

    "5103361": "ODAIR JOSE VARGAS",
    "5103809": "ADEMIR FELICIO GARCIA",
    "5103957": "GHEYSA MARIA BONFIM BORGATO",
    "5105234": "MARCELO VIEIRA VITORAZZI",
    "5105622": "HECTOR ALVARES BEZERRA",

    # ------------------------------------------------------
    # PARA
    # ------------------------------------------------------

    "1502954": "WAGNE COSTA MACHADO",
    "1505551": "DOMINGOS GUEDES NETO",

    # ------------------------------------------------------
    # PARAIBA
    # ------------------------------------------------------

    "2508703": "JUCELIO PEREIRA MOURA",
    "2510402": "JOANA SABINO DE ALMEIDA CARVALHO",

    # ------------------------------------------------------
    # PIAUI
    # ------------------------------------------------------

    "2201176": "MARDONIO SOARES LOPES",
    "2207108": "ANTONIO LEAL DA SILVA",
    "2207793": "ANTONIO MILTON DE ABREU PASSOS",

    # ------------------------------------------------------
    # PARANA
    # ------------------------------------------------------

    "4107157": "AMARILDO APARECIDO DA SILVA",
    "4111209": "VILMAR SCHMOLLER",
    "4116307": "ÁUREO GOMES",
    "4119004": "EDSOM LUIZ BAGETTI",
    "4121356": "EVERTON CÁSSIO ZANUTO",
    "4125209": "GELSON COELHO DO ROSÁRIO",

    # ------------------------------------------------------
    # RIO GRANDE DO NORTE
    # ------------------------------------------------------

    "2406205": "JOÃO PAULO GUEDES LOPES",
    "2408409": "ANTONIMAR AMORIM CARLOS",

    # ------------------------------------------------------
    # RONDONIA
    # ------------------------------------------------------

    "1100015": "GIOVAN DAMO",
    "1100346": "JAIR LUIZ",
    "1100098": "WELITON PEREIRA CAMPOS",
    "1100130": "PAULO HENRIQUE DOS SANTOS",
    "1100148": "CLODOALDO ALVES PEDROSO",
    "1100296": "JURANDIR DE OLIVEIRA ARAUJO",
    "1101484": "SIDNEY BORGES DE OLIVEIRA",

    # ------------------------------------------------------
    # RIO GRANDE DO SUL
    # ------------------------------------------------------

    "4317103": "ANA LUIZA MOURA TAROUCO",

    # ------------------------------------------------------
    # SANTA CATARINA
    # ------------------------------------------------------

    "4206108": "HELIO ALBERTON JUNIOR",
    "4206702": "RONALDO LORENÇO DA ROSA",

    # ------------------------------------------------------
    # SERGIPE
    # ------------------------------------------------------

    "2802601": "JOSÉ NICARCIO DE ARAGÃO",
    "2803203": "IVAN APOSTOLO SOBRAL",

    # ------------------------------------------------------
    # SAO PAULO
    # ------------------------------------------------------

    "3502606": "IZAIAS APARECIDO SANCHEZ",
    "3506607": "CARLOS ALBERTO TAINO JUNIOR",
    "3515202": "PEDRO DE SENZI NETO",
    "3518008": "EDMILSON PIRES DO CARMO",
    "3535200": "VALDIR SEMENSATI DE MORAES",
    "3545803": "RAFAEL PIOVEZAN",
    "3546108": "JOSÉ BASILIO DE FARIA",
    "3547403": "OSMAR SAMPAIO",
    "3549300": "LUCAS DE OLIVEIRA BARBOSA",
    "3550001": "ALEX EUZÉBIO TORRES",

    # ------------------------------------------------------
    # TOCANTINS
    # ------------------------------------------------------

    "1716307": "GILMAR OLIVEIRA SOUZA",
}


print()
print(
    "REGISTROS PREPARADOS PARA CARGA:",
    len(prefeitos)
)

print()
print("Conferindo municipios...")


# ==========================================================
# CONFERIR TODOS ANTES DE ALTERAR
# ==========================================================

problemas = []

for codigo_ibge, nome_prefeito in prefeitos.items():

    cur.execute("""
        SELECT
            m.id,
            m.nome
        FROM municipios m
        WHERE m.codigo_ibge = %s
    """, (
        codigo_ibge,
    ))

    resultado = cur.fetchone()

    if not resultado:

        problemas.append(
            (
                codigo_ibge,
                "MUNICIPIO NAO ENCONTRADO"
            )
        )


print(
    "PROBLEMAS ENCONTRADOS:",
    len(problemas)
)


# ==========================================================
# PROTECAO
# ==========================================================

if problemas:

    print()
    print("A CARGA FOI CANCELADA.")

    for problema in problemas:
        print(
            problema[0],
            "|",
            problema[1]
        )

    print()
    print("NENHUM DADO FOI ALTERADO.")

    conn.rollback()
    cur.close()
    conn.close()

    raise SystemExit


# ==========================================================
# ATUALIZAR
# ==========================================================

print()
print("Todos os municipios foram encontrados.")
print()
print("Gravando prefeitos...")


atualizados = 0


for codigo_ibge, nome_prefeito in prefeitos.items():

    cur.execute("""
        SELECT id
        FROM municipios
        WHERE codigo_ibge = %s
    """, (
        codigo_ibge,
    ))

    municipio_id = cur.fetchone()[0]


    cur.execute("""
        UPDATE autoridades
        SET
            nome = %s,
            ativo = TRUE,
            fonte =
                'Tribunal Superior Eleitoral - Eleicoes 2024',
            data_verificacao = %s,
            observacao =
                'Autoridade confirmada por cruzamento do codigo IBGE com a base oficial do TSE.'
        WHERE esfera = 'MUNICIPAL'
          AND municipio_id = %s
          AND cargo = 'Prefeito'
    """, (
        nome_prefeito,
        date.today(),
        municipio_id
    ))


    if cur.rowcount:
        atualizados += cur.rowcount


conn.commit()


# ==========================================================
# CONFERENCIA FINAL
# ==========================================================

cur.execute("""
    SELECT COUNT(*)
    FROM autoridades
    WHERE esfera = 'MUNICIPAL'
      AND cargo = 'Prefeito'
      AND nome <> 'A CADASTRAR'
""")

preenchidos = cur.fetchone()[0]


cur.execute("""
    SELECT COUNT(*)
    FROM autoridades
    WHERE esfera = 'MUNICIPAL'
      AND cargo = 'Prefeito'
      AND nome = 'A CADASTRAR'
""")

pendentes = cur.fetchone()[0]


print()
print("=" * 70)
print("CARGA CONCLUIDA")
print("=" * 70)

print(
    "REGISTROS PREPARADOS:",
    len(prefeitos)
)

print(
    "REGISTROS ATUALIZADOS:",
    atualizados
)

print(
    "PREFEITOS PREENCHIDOS NO BANCO:",
    preenchidos
)

print(
    "PREFEITOS AINDA PENDENTES:",
    pendentes
)

print("=" * 70)


cur.close()
conn.close()