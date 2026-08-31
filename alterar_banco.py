import mysql.connector
from mysql.connector import Error

# Conexão com o MySQL
try:
    conexao = mysql.connector.connect(
        host='localhost',
        user='root',
        password='root',
        database='sistema_pacientes'
    )

    if conexao.is_connected():
        cursor = conexao.cursor()

        script_sql = """
                          ALTER TABLE relatorios ADD COLUMN valor_sessao DECIMAL(10,2) NOT NULL DEFAULT 0;
                     """

        # Executando múltiplas queries
        for result in cursor.execute(script_sql, multi=True):
            pass

        print("Banco e tabelas criados com sucesso!")

except Error as e:
    print("Erro ao conectar ou executar:", e)

finally:
    if conexao.is_connected():
        cursor.close()
        conexao.close()
