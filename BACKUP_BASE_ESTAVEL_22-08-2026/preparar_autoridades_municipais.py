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
print("PREPARACAO DAS AUTORIDADES MUNICIPAIS")
print("=" * 70)

x.execute("""
    SELECT id, nome, estado_id
    FROM municipios
    ORDER BY estado_id, nome
""")

municipios = x.fetchall()

print("MUNICIPIOS ENCONTRADOS:", len(municipios))

inseridos = 0
existentes = 0

for municipio_id, municipio_nome, estado_id in municipios:

    # PREFEITO
    x.execute("""
        SELECT id
        FROM autoridades
        WHERE esfera = 'MUNICIPAL'
          AND municipio_id = %s
          AND cargo = 'Prefeito'
        LIMIT 1
    """, (municipio_id,))

    if x.fetchone():
        existentes += 1
    else:
        x.execute("""
            INSERT INTO autoridades (
                nome,
                cargo,
                esfera,
                estado_id,
                municipio_id,
                ativo,
                fonte,
                data_verificacao,
                observacao
            )
            VALUES (
                'A CADASTRAR',
                'Prefeito',
                'MUNICIPAL',
                %s,
                %s,
                FALSE,
                'Aguardando confirmação em fonte oficial',
                %s,
                'Autoridade municipal preparada para receber o nome oficial do Prefeito.'
            )
        """, (
            estado_id,
            municipio_id,
            date.today()
        ))

        inseridos += 1

    # SECRETÁRIO MUNICIPAL DE SAÚDE
    x.execute("""
        SELECT id
        FROM autoridades
        WHERE esfera = 'MUNICIPAL'
          AND municipio_id = %s
          AND cargo = 'Secretário Municipal de Saúde'
        LIMIT 1
    """, (municipio_id,))

    if x.fetchone():
        existentes += 1
    else:
        x.execute("""
            INSERT INTO autoridades (
                nome,
                cargo,
                esfera,
                estado_id,
                municipio_id,
                ativo,
                fonte,
                data_verificacao,
                observacao
            )
            VALUES (
                'A CADASTRAR',
                'Secretário Municipal de Saúde',
                'MUNICIPAL',
                %s,
                %s,
                FALSE,
                'Aguardando confirmação em fonte oficial',
                %s,
                'Autoridade municipal preparada para receber o nome oficial do Secretário Municipal de Saúde.'
            )
        """, (
            estado_id,
            municipio_id,
            date.today()
        ))

        inseridos += 1

c.commit()

x.execute("""
    SELECT COUNT(*)
    FROM autoridades
    WHERE esfera = 'MUNICIPAL'
""")

total_municipal = x.fetchone()[0]

x.execute("""
    SELECT COUNT(*)
    FROM autoridades
""")

total_geral = x.fetchone()[0]

print()
print("=" * 70)
print("PREPARACAO MUNICIPAL CONCLUIDA")
print("=" * 70)
print("MUNICIPIOS:", len(municipios))
print("REGISTROS CRIADOS:", inseridos)
print("REGISTROS JA EXISTENTES:", existentes)
print("AUTORIDADES MUNICIPAIS:", total_municipal)
print("TOTAL DE AUTORIDADES:", total_geral)
print("=" * 70)

x.close()
c.close()