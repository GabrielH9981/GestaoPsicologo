CREATE DATABASE IF NOT EXISTS sistema_pacientes;
USE sistema_pacientes;

-- Tabela de pacientes
CREATE TABLE IF NOT EXISTS pacientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    data_nascimento DATE NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    valor_sessao VARCHAR(20) NOT NULL,
    pacote_mensal BOOLEAN NOT NULL,
    valor_pacote VARCHAR(20)
);

-- Tabela de relatórios
CREATE TABLE IF NOT EXISTS relatorios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    paciente_id INT NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    data DATE NOT NULL,
    conteudo TEXT NOT NULL,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
);
