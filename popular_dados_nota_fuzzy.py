# -*- coding: utf-8 -*-
"""
Complementa dados_nota para pacientes que foram vinculados via fuzzy/dependente
mas cujo nome no MySQL não bateu com o SQLite na importação anterior.
Cruza pelo nome_extrato_norm do extrato_itens com o nome_norm do SQLite.
"""
import sqlite3
import mysql.connector
from extrato import normalize

SQ_PATH = 'seleniumAline/pacientes.db'

sq = sqlite3.connect(SQ_PATH)
sq_cur = sq.cursor()
sq_cur.execute('SELECT nome_norm, CPF, CEP, Logradouro, Numero, Bairro, Cidade FROM pacientes')
sqlite_index = {row[0]: row[1:] for row in sq_cur.fetchall()}
sq.close()
print(f'SQLite: {len(sqlite_index)} registros')

my = mysql.connector.connect(host='localhost', user='root', password='root', database='sistema_pacientes')
cur = my.cursor(dictionary=True)

# Pega todos os itens com paciente vinculado mas sem dados_nota ainda
cur.execute('''
    SELECT DISTINCT i.paciente_id, i.nome_extrato, i.nome_extrato_norm
    FROM extrato_itens i
    LEFT JOIN dados_nota dn ON dn.paciente_id = i.paciente_id
    WHERE i.paciente_id IS NOT NULL AND dn.id IS NULL
''')
pendentes = cur.fetchall()
print(f'Pacientes sem dados_nota: {len(pendentes)}')

inseridos = 0
nao_encontrados = []

for row in pendentes:
    pac_id = row['paciente_id']
    nome_norm = row['nome_extrato_norm']

    dados = sqlite_index.get(nome_norm)
    if not dados:
        # tenta normalizar o nome_extrato diretamente
        dados = sqlite_index.get(normalize(row['nome_extrato']))

    if dados:
        cpf, cep, logradouro, numero, bairro, cidade = dados
        cep_limpo = cep if cep and '.' not in cep else None
        cur.execute('''
            INSERT INTO dados_nota (paciente_id, cpf, cep, logradouro, numero, bairro, cidade)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                cpf=VALUES(cpf), cep=VALUES(cep), logradouro=VALUES(logradouro),
                numero=VALUES(numero), bairro=VALUES(bairro), cidade=VALUES(cidade)
        ''', (pac_id, cpf, cep_limpo, logradouro, numero, bairro, cidade))
        inseridos += 1
    else:
        nao_encontrados.append(f"{row['nome_extrato']} (pac_id={pac_id})")

my.commit()
cur.close()
my.close()

print(f'Inseridos: {inseridos}')
print(f'Nao encontrados no SQLite ({len(nao_encontrados)}):')
for n in nao_encontrados:
    print(f'  - {n}')
