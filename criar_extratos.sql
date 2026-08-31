CREATE TABLE IF NOT EXISTS extratos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mes INT NOT NULL,
    ano INT NOT NULL,
    nome_arquivo VARCHAR(255) NOT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_mes_ano (mes, ano)
);

CREATE TABLE IF NOT EXISTS extrato_itens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    extrato_id INT NOT NULL,
    nome_extrato VARCHAR(255) NOT NULL,
    nome_extrato_norm VARCHAR(255) NOT NULL,
    total_valor DECIMAL(10,2) NOT NULL,
    sessoes INT NOT NULL,
    ultima_data VARCHAR(10),
    paciente_id INT DEFAULT NULL,
    match_tipo VARCHAR(20) DEFAULT NULL,
    ignorado TINYINT(1) DEFAULT 0,
    FOREIGN KEY (extrato_id) REFERENCES extratos(id) ON DELETE CASCADE,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE SET NULL
);
