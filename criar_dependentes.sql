-- Tabela de dependentes: vincula nomes do extrato a pacientes cadastrados
CREATE TABLE IF NOT EXISTS dependentes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    paciente_id INT NOT NULL,
    nome_extrato VARCHAR(255) NOT NULL,
    nome_extrato_norm VARCHAR(255) NOT NULL,
    UNIQUE KEY uq_nome_norm (nome_extrato_norm),
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
);
