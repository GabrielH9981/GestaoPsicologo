# -*- coding: utf-8 -*-
"""
Popula dados_nota a partir do pacientes.db (SQLite),
cruzando pelo nome normalizado com os pacientes cadastrados no MySQL.
Execute uma única vez (ou re-execute — usa INSERT IGNORE).
"""
import sqlite3
import mysql.connector
from extrato import normalize

SQ_PATH = 'seleniumAline/pacientes.db'

sq = sqlite3.connect(SQ_PATH)
sq_cur = sq.cursor()
sq_cur.execute('SELECT Nome, CPF, CEP, Logradouro, Numero, Bairro, Cidade FROM pacientes')
sqlite_rows = sq_cur.fetchall()
sq.close()
print(f'SQLite: {len(sqlite_rows)} registros')

my = mysql.connector.connect(host='localhost', user='root', password='root', database='sistema_pacientes')
my_cur = my.cursor(dictionary=True)
my_cur.execute('SELECT id, nome FROM pacientes')
mysql_pacs = {normalize(p['nome']): p['id'] for p in my_cur.fetchall()}
print(f'MySQL pacientes: {len(mysql_pacs)}')

inseridos = 0
nao_encontrados = []

for nome, cpf, cep, logradouro, numero, bairro, cidade in sqlite_rows:
    pac_id = mysql_pacs.get(normalize(nome))
    # CEP sujo (ex: CPF no lugar) — ignora se tiver ponto e traço (formato CPF)
    cep_limpo = cep if cep and '.' not in cep else None
    if pac_id:
        my_cur.execute('''
            INSERT INTO dados_nota (paciente_id, cpf, cep, logradouro, numero, bairro, cidade)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                cpf = VALUES(cpf), cep = VALUES(cep), logradouro = VALUES(logradouro),
                numero = VALUES(numero), bairro = VALUES(bairro), cidade = VALUES(cidade)
        ''', (pac_id, cpf, cep_limpo, logradouro, numero, bairro, cidade))
        inseridos += 1
    else:
        nao_encontrados.append(nome)

my.commit()
my_cur.close()
my.close()

print(f'Inseridos/atualizados: {inseridos}')
print(f'Nao encontrados no MySQL ({len(nao_encontrados)}):')
for n in nao_encontrados:
    print(f'  - {n}')
