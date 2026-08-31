CREATE TABLE IF NOT EXISTS dados_nota (
    id INT AUTO_INCREMENT PRIMARY KEY,
    paciente_id INT DEFAULT NULL,
    dependente_id INT DEFAULT NULL,
    cpf VARCHAR(20),
    cep VARCHAR(10),
    logradouro VARCHAR(255),
    numero VARCHAR(20),
    bairro VARCHAR(100),
    cidade VARCHAR(100),
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE,
    FOREIGN KEY (dependente_id) REFERENCES dependentes(id) ON DELETE CASCADE
);
