import mysql.connector
from mysql.connector import Error

# Conexão com o MySQL
try:
    conexao = mysql.connector.connect(
        host='localhost',
        user='root',
        password='root'
    )

    if conexao.is_connected():
        cursor = conexao.cursor()

        script_sql = """
        CREATE DATABASE IF NOT EXISTS sistema_pacientes;
        USE sistema_pacientes;

        CREATE TABLE IF NOT EXISTS pacientes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            data_nascimento DATE NOT NULL,
            telefone VARCHAR(20) NOT NULL,
            valor_sessao VARCHAR(20) NOT NULL,
            pacote_mensal BOOLEAN NOT NULL,
            valor_pacote VARCHAR(20)
        );

        CREATE TABLE IF NOT EXISTS relatorios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            paciente_id INT NOT NULL,
            titulo VARCHAR(255) NOT NULL,
            data DATE NOT NULL,
            conteudo TEXT NOT NULL,
            FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
        );
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
