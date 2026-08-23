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
print("CARGA DAS AUTORIDADES ESTADUAIS")
print("=" * 70)

# ==========================================================
# GOVERNADORES ATUAIS
# ==========================================================

governadores = {
    "AC": "Mailza Assis",
    "AL": "Paulo Dantas",
    "AP": "Clécio Luís",
    "AM": "Roberto Cidade",
    "BA": "Jerônimo Rodrigues",
    "CE": "Elmano de Freitas",
    "DF": "Celina Leão",
    "ES": "Ricardo Ferraço",
    "GO": "Daniel Vilela",
    "MA": "Carlos Brandão",
    "MT": "Otaviano Pivetta",
    "MS": "Eduardo Riedel",
    "MG": "Mateus Simões",
    "PA": "Hana Ghassan",
    "PB": "Lucas Ribeiro",
    "PR": "Ratinho Junior",
    "PE": "Raquel Lyra",
    "PI": "Rafael Fonteles",
    "RJ": "Ricardo Couto de Castro",
    "RN": "Fátima Bezerra",
    "RS": "Eduardo Leite",
    "RO": "Marcos Rocha",
    "RR": "Edilson Damião",
    "SC": "Jorginho Mello",
    "SP": "Tarcísio de Freitas",
    "SE": "Fábio Mitidieri",
    "TO": "Wanderlei Barbosa"
}

# ==========================================================
# SECRETÁRIOS ESTADUAIS DE SAÚDE
# ==========================================================

secretarios = {
    "AC": "Pedro Pascoal Duarte Pinheiro Zambon",
    "AL": "Gustavo Pontes de Miranda",
    "AP": "Carlos Rinaldo Nogueira Martins",
    "AM": "Nayara de Oliveira Maksoud Moraes",
    "BA": "Roberta Silva de Carvalho Santana",
    "CE": "Tânia Mara Coelho",
    "DF": "Juracy Cavalcante Lacerda Júnior",
    "ES": "Tyago Hoffmann",
    "GO": "Rasível dos Reis Santos Junior",
    "MA": "Tiago José Mendes Fernandes",
    "MT": "Gilberto Figueiredo",
    "MS": "Maurício Simões Correia",
    "MG": "Fábio Baccheretti Vitor",
    "PA": "Ualame Fialho Machado",
    "PB": "Arimatheus Silva Reis",
    "PR": "César Augusto Neves Luiz",
    "PE": "Zilda do Rego Cavalcante",
    "PI": "Dirceu Hamilton Cordeiro Campêlo",
    "RJ": "Ronaldo Damião",
    "RN": "Alexandre Motta Câmara",
    "RS": "Arita Gilda Hübner Bergmann",
    "RO": "Edilton Oliveira dos Santos",
    "RR": "Adilma Rosa de Castro Lucena",
    "SC": "Diogo Demarchi Silva",
    "SP": "Eleuses Paiva",
    "SE": "Jardel Mitermayer",
    "TO": "Carlos Felinto Júnior"
}

# ==========================================================
# DESCOBRIR A COLUNA DA SIGLA NA TABELA ESTADOS
# ==========================================================

x.execute("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'estados'
""")

colunas = [r[0] for r in x.fetchall()]

coluna_sigla = None

for coluna in ["sigla", "uf", "sg_uf", "sigla_uf"]:
    if coluna in colunas:
        coluna_sigla = coluna
        break

if not coluna_sigla:
    print()
    print("ERRO: não encontrei a coluna da UF na tabela estados.")
    print("COLUNAS ENCONTRADAS:", colunas)
    x.close()
    c.close()
    raise SystemExit

# ==========================================================
# CARREGAR ESTADOS
# ==========================================================

x.execute(
    f"""
    SELECT id, {coluna_sigla}
    FROM estados
    """
)

estados = {}

for estado_id, sigla in x.fetchall():
    if sigla:
        estados[str(sigla).strip().upper()] = estado_id

print()
print("ESTADOS ENCONTRADOS NO BANCO:", len(estados))

# ==========================================================
# INSERÇÃO
# ==========================================================

inseridos = 0
ja_existiam = 0
erros = 0

fonte_governadores = (
    "Fontes oficiais dos Governos Estaduais / "
    "verificacao nacional em 17/08/2026"
)

fonte_secretarios = (
    "CONASS - composicao dos Secretarios Estaduais de Saude 2026; "
    "verificacao complementar em fontes oficiais estaduais"
)

for uf in governadores:

    if uf not in estados:
        print("ERRO - UF não encontrada:", uf)
        erros += 1
        continue

    estado_id = estados[uf]

    # ------------------------------------------------------
    # GOVERNADOR
    # ------------------------------------------------------

    nome_governador = governadores[uf]

    x.execute("""
        SELECT id
        FROM autoridades
        WHERE esfera = 'ESTADUAL'
          AND estado_id = %s
          AND cargo = 'Governador'
          AND ativo = TRUE
        LIMIT 1
    """, (estado_id,))

    if x.fetchone():
        ja_existiam += 1
    else:
        x.execute("""
            INSERT INTO autoridades (
                nome,
                cargo,
                esfera,
                estado_id,
                data_inicio,
                ativo,
                fonte,
                data_verificacao
            )
            VALUES (
                %s,
                'Governador',
                'ESTADUAL',
                %s,
                %s,
                TRUE,
                %s,
                %s
            )
        """, (
            nome_governador,
            estado_id,
            date.today(),
            fonte_governadores,
            date.today()
        ))

        inseridos += 1

    # ------------------------------------------------------
    # SECRETÁRIO DE SAÚDE
    # ------------------------------------------------------

    nome_secretario = secretarios[uf]

    x.execute("""
        SELECT id
        FROM autoridades
        WHERE esfera = 'ESTADUAL'
          AND estado_id = %s
          AND cargo = 'Secretário Estadual de Saúde'
          AND ativo = TRUE
        LIMIT 1
    """, (estado_id,))

    if x.fetchone():
        ja_existiam += 1
    else:
        x.execute("""
            INSERT INTO autoridades (
                nome,
                cargo,
                esfera,
                estado_id,
                data_inicio,
                ativo,
                fonte,
                data_verificacao
            )
            VALUES (
                %s,
                'Secretário Estadual de Saúde',
                'ESTADUAL',
                %s,
                %s,
                TRUE,
                %s,
                %s
            )
        """, (
            nome_secretario,
            estado_id,
            date.today(),
            fonte_secretarios,
            date.today()
        ))

        inseridos += 1

# ==========================================================
# GRAVAR
# ==========================================================

c.commit()

# ==========================================================
# CONFERÊNCIA
# ==========================================================

x.execute("""
    SELECT COUNT(*)
    FROM autoridades
    WHERE esfera = 'ESTADUAL'
""")

total_estadual = x.fetchone()[0]

x.execute("""
    SELECT COUNT(*)
    FROM autoridades
    WHERE esfera = 'FEDERAL'
""")

total_federal = x.fetchone()[0]

print()
print("=" * 70)
print("CARGA ESTADUAL CONCLUIDA")
print("=" * 70)
print("INSERIDOS:", inseridos)
print("JA EXISTIAM:", ja_existiam)
print("ERROS:", erros)
print()
print("AUTORIDADES ESTADUAIS NO BANCO:", total_estadual)
print("AUTORIDADES FEDERAIS NO BANCO:", total_federal)
print("TOTAL DE AUTORIDADES:", total_estadual + total_federal)
print("=" * 70)

x.close()
c.close()