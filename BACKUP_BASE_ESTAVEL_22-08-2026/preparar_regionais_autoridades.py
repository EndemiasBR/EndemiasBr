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
print("PREPARACAO DAS AUTORIDADES REGIONAIS")
print("=" * 70)

# Verificar Regionais existentes
x.execute("""
    SELECT
        r.id,
        r.nome,
        e.id,
        e.nome
    FROM regionais_saude r
    LEFT JOIN estados e
        ON e.id = r.estado_id
    ORDER BY e.nome, r.nome
""")

regionais = x.fetchall()

print("REGIONAIS ENCONTRADAS:", len(regionais))

if not regionais:
    print("ERRO: nenhuma Regional encontrada.")
    x.close()
    c.close()
    raise SystemExit

inseridos = 0
existentes = 0

for regional_id, regional_nome, estado_id, estado_nome in regionais:

    # ------------------------------------------------------
    # MARCADOR PARA DIREÇÃO REGIONAL DE SAÚDE
    # ------------------------------------------------------

    x.execute("""
        SELECT id
        FROM autoridades
        WHERE esfera = 'REGIONAL'
          AND regional_id = %s
          AND cargo = 'DIREÇÃO REGIONAL DE SAÚDE'
        LIMIT 1
    """, (regional_id,))

    if x.fetchone():
        existentes += 1
    else:
        x.execute("""
            INSERT INTO autoridades (
                nome,
                cargo,
                esfera,
                estado_id,
                regional_id,
                ativo,
                fonte,
                data_verificacao,
                observacao
            )
            VALUES (
                'A CADASTRAR',
                'DIREÇÃO REGIONAL DE SAÚDE',
                'REGIONAL',
                %s,
                %s,
                FALSE,
                'Aguardando confirmação em fonte oficial',
                %s,
                'Registro preparado para receber a autoridade responsável pela direção da Regional.'
            )
        """, (
            estado_id,
            regional_id,
            date.today()
        ))

        inseridos += 1

    # ------------------------------------------------------
    # MARCADOR PARA DIREÇÃO ADMINISTRATIVA
    # ------------------------------------------------------

    x.execute("""
        SELECT id
        FROM autoridades
        WHERE esfera = 'REGIONAL'
          AND regional_id = %s
          AND cargo = 'DIREÇÃO ADMINISTRATIVA'
        LIMIT 1
    """, (regional_id,))

    if x.fetchone():
        existentes += 1
    else:
        x.execute("""
            INSERT INTO autoridades (
                nome,
                cargo,
                esfera,
                estado_id,
                regional_id,
                ativo,
                fonte,
                data_verificacao,
                observacao
            )
            VALUES (
                'A CADASTRAR',
                'DIREÇÃO ADMINISTRATIVA',
                'REGIONAL',
                %s,
                %s,
                FALSE,
                'Aguardando confirmação em fonte oficial',
                %s,
                'Registro preparado para receber a autoridade administrativa da Regional.'
            )
        """, (
            estado_id,
            regional_id,
            date.today()
        ))

        inseridos += 1

c.commit()

# Conferência
x.execute("""
    SELECT COUNT(*)
    FROM autoridades
    WHERE esfera = 'REGIONAL'
""")

total_regionais = x.fetchone()[0]

x.execute("""
    SELECT COUNT(*)
    FROM autoridades
""")

total_geral = x.fetchone()[0]

print()
print("=" * 70)
print("PREPARACAO CONCLUIDA")
print("=" * 70)
print("REGIONAIS NO BANCO:", len(regionais))
print("REGISTROS CRIADOS:", inseridos)
print("REGISTROS JA EXISTENTES:", existentes)
print("AUTORIDADES REGIONAIS:", total_regionais)
print("TOTAL DE AUTORIDADES:", total_geral)
print("=" * 70)

x.close()
c.close()