import psycopg2

senha = input("Senha do PostgreSQL: ")

c = psycopg2.connect(
    host="localhost",
    dbname="endemiasbr",
    user="postgres",
    password=senha
)

x = c.cursor()

x.execute("""
CREATE TABLE IF NOT EXISTS autoridades (
    id SERIAL PRIMARY KEY,

    nome VARCHAR(150) NOT NULL,

    cargo VARCHAR(100) NOT NULL,

    esfera VARCHAR(20) NOT NULL
        CHECK (esfera IN ('FEDERAL','ESTADUAL','REGIONAL','MUNICIPAL')),

    estado_id INTEGER REFERENCES estados(id),

    regional_id INTEGER REFERENCES regionais_saude(id),

    municipio_id INTEGER REFERENCES municipios(id),

    data_inicio DATE,

    data_fim DATE,

    ativo BOOLEAN DEFAULT TRUE,

    fonte VARCHAR(500),

    data_verificacao DATE DEFAULT CURRENT_DATE,

    observacao TEXT,

    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

x.execute("""
CREATE INDEX IF NOT EXISTS idx_autoridades_esfera
ON autoridades(esfera);
""")

x.execute("""
CREATE INDEX IF NOT EXISTS idx_autoridades_estado
ON autoridades(estado_id);
""")

x.execute("""
CREATE INDEX IF NOT EXISTS idx_autoridades_regional
ON autoridades(regional_id);
""")

x.execute("""
CREATE INDEX IF NOT EXISTS idx_autoridades_municipio
ON autoridades(municipio_id);
""")

c.commit()

x.execute("""
SELECT COUNT(*)
FROM autoridades
""")

print()
print("===== AUTORIDADES =====")
print("TABELA CRIADA/VERIFICADA")
print("REGISTROS ATUAIS:", x.fetchone()[0])

x.close()
c.close()