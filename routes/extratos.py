import io
from collections import defaultdict
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, Response, json as fjson
from db import get_db_connection
from extrato import processar_csv, normalize

bp = Blueprint('extratos', __name__)


@bp.route('/extratos')
def lista():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT e.id, e.mes, e.ano, e.nome_arquivo, e.criado_em, e.finalizado,
               COUNT(i.id) AS total_itens,
               SUM(CASE WHEN i.ignorado=0 AND i.paciente_id IS NOT NULL THEN i.total_valor ELSE 0 END) AS total_vinculado,
               SUM(CASE WHEN i.ignorado=0 AND i.paciente_id IS NULL THEN 1 ELSE 0 END) AS pendentes
        FROM extratos e LEFT JOIN extrato_itens i ON i.extrato_id = e.id
        GROUP BY e.id ORDER BY e.ano DESC, e.mes DESC
    ''')
    extratos = cursor.fetchall()
    cursor.close(); conn.close()
    return render_template('extratos/lista.html', extratos=extratos)


@bp.route('/extratos/novo', methods=['GET', 'POST'])
def novo():
    erro = None
    if request.method == 'POST':
        arquivo = request.files.get('csv_file')
        if not arquivo or not arquivo.filename.endswith('.csv'):
            erro = 'Envie um arquivo .csv válido.'
        else:
            try:
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute('SELECT id, nome FROM pacientes ORDER BY nome ASC')
                pacientes = cursor.fetchall()
                cursor.execute('''
                    SELECT d.nome_extrato_norm, d.paciente_id, p.nome AS paciente_nome
                    FROM dependentes d JOIN pacientes p ON d.paciente_id = p.id
                ''')
                dependentes = cursor.fetchall()
                cursor.close(); conn.close()

                stream = io.StringIO(arquivo.stream.read().decode('utf-8', errors='replace'))
                resultados = processar_csv(stream, pacientes, dependentes)

                datas = [r['ultima_data'] for r in resultados if r['ultima_data']]
                if datas:
                    ultima = max(datas, key=lambda d: datetime.strptime(d, '%d/%m/%Y'))
                    mes, ano = int(ultima.split('/')[1]), int(ultima.split('/')[2])
                else:
                    mes, ano = datetime.today().month, datetime.today().year

                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO extratos (mes, ano, nome_arquivo) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE nome_arquivo=VALUES(nome_arquivo), criado_em=CURRENT_TIMESTAMP',
                    (mes, ano, arquivo.filename)
                )
                extrato_id = cursor.lastrowid
                if not extrato_id:
                    cursor.execute('SELECT id FROM extratos WHERE mes=%s AND ano=%s', (mes, ano))
                    extrato_id = cursor.fetchone()[0]
                    cursor.execute('DELETE FROM extrato_itens WHERE extrato_id=%s', (extrato_id,))

                for r in resultados:
                    cursor.execute('''
                        INSERT INTO extrato_itens
                            (extrato_id, nome_extrato, nome_extrato_norm, total_valor, sessoes, ultima_data, paciente_id, match_tipo)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    ''', (extrato_id, r['nome_extrato'], r['nome_extrato_norm'],
                          r['total_valor'], r['sessoes'], r['ultima_data'] or None,
                          r['paciente_id'], r['match_tipo']))
                conn.commit(); cursor.close(); conn.close()
                return redirect(url_for('extratos.editar', id=extrato_id))
            except Exception as e:
                erro = str(e)
    return render_template('extratos/novo.html', erro=erro)


@bp.route('/extratos/<int:id>')
def editar(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM extratos WHERE id = %s', (id,))
    extrato = cursor.fetchone()
    if not extrato:
        cursor.close(); conn.close()
        return 'Extrato não encontrado', 404
    cursor.execute('''
        SELECT i.*, p.nome AS paciente_nome FROM extrato_itens i
        LEFT JOIN pacientes p ON p.id = i.paciente_id
        WHERE i.extrato_id = %s ORDER BY i.ignorado ASC, i.nome_extrato ASC
    ''', (id,))
    itens = cursor.fetchall()
    cursor.execute('SELECT id, nome FROM pacientes ORDER BY nome ASC')
    pacientes = cursor.fetchall()
    cursor.close(); conn.close()
    for item in itens:
        v = float(item['total_valor'])
        item['total_fmt'] = f"{v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    return render_template('extratos/editar.html', extrato=extrato, itens=itens, pacientes=pacientes)


@bp.route('/extratos/<int:id>/salvar', methods=['POST'])
def salvar(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT id FROM extrato_itens WHERE extrato_id = %s', (id,))
    item_ids = [r['id'] for r in cursor.fetchall()]
    for item_id in item_ids:
        paciente_id = request.form.get(f'paciente_{item_id}') or None
        ignorado = 1 if request.form.get(f'ignorado_{item_id}') else 0
        cursor.execute('UPDATE extrato_itens SET paciente_id=%s, ignorado=%s WHERE id=%s',
                       (paciente_id, ignorado, item_id))
        if paciente_id:
            cursor.execute('SELECT nome_extrato, nome_extrato_norm, match_tipo FROM extrato_itens WHERE id=%s', (item_id,))
            item = cursor.fetchone()
            if item['match_tipo'] not in ('exato', 'fuzzy'):
                cursor.execute('''
                    INSERT INTO dependentes (paciente_id, nome_extrato, nome_extrato_norm)
                    VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE paciente_id=VALUES(paciente_id), nome_extrato=VALUES(nome_extrato)
                ''', (paciente_id, item['nome_extrato'], item['nome_extrato_norm']))
    conn.commit(); cursor.close(); conn.close()
    return redirect(url_for('extratos.editar', id=id))


@bp.route('/extratos/<int:id>/visualizar')
def visualizar(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM extratos WHERE id = %s', (id,))
    extrato = cursor.fetchone()
    if not extrato:
        cursor.close(); conn.close()
        return 'Extrato não encontrado', 404
    cursor.execute('''
        SELECT MIN(i.nome_extrato) AS nome_extrato, i.nome_extrato_norm,
               SUM(i.total_valor) AS total_valor, SUM(i.sessoes) AS sessoes,
               MAX(i.ultima_data) AS ultima_data, i.paciente_id,
               MAX(COALESCE(p.nome, i.nome_extrato)) AS nome_completo,
               MAX(dn.cpf) AS cpf, MAX(dn.cep) AS cep, MAX(dn.logradouro) AS logradouro,
               MAX(dn.numero) AS numero, MAX(dn.bairro) AS bairro, MAX(dn.cidade) AS cidade,
               MAX(p.id) AS pac_id
        FROM extrato_itens i
        LEFT JOIN pacientes p ON p.id = i.paciente_id
        LEFT JOIN dependentes d ON d.nome_extrato_norm = i.nome_extrato_norm
        LEFT JOIN dados_nota dn_dep ON (dn_dep.dependente_id = d.id)
        LEFT JOIN dados_nota dn_pac ON (dn_pac.paciente_id = i.paciente_id)
        LEFT JOIN dados_nota dn ON (dn.id = COALESCE(dn_dep.id, dn_pac.id))
        WHERE i.extrato_id = %s AND i.ignorado = 0
        GROUP BY i.paciente_id, i.nome_extrato_norm
        ORDER BY nome_completo ASC
    ''', (id,))
    itens_raw = cursor.fetchall()
    cursor.close(); conn.close()

    itens, vistos = [], {}
    for item in itens_raw:
        chave = item['paciente_id'] if item['paciente_id'] else item['nome_extrato_norm']
        if chave in vistos:
            idx = vistos[chave]
            itens[idx]['total_valor'] += float(item['total_valor'])
            itens[idx]['sessoes'] += item['sessoes']
            if item['ultima_data'] and item['ultima_data'] > (itens[idx]['ultima_data'] or ''):
                itens[idx]['ultima_data'] = item['ultima_data']
        else:
            vistos[chave] = len(itens)
            entry = dict(item)
            entry['total_valor'] = float(item['total_valor'])
            itens.append(entry)

    for item in itens:
        v = item['total_valor']
        item['total_fmt'] = f"{v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    if request.args.get('fmt') == 'json':
        resultado = [{
            'DataCompetencia': i['ultima_data'] or '',
            'CPF': i['cpf'] or '',
            'Nome': i['nome_completo'] or i['nome_extrato'],
            'CEP': i['cep'] or '', 'Logradouro': i['logradouro'] or '',
            'Numero': i['numero'] or '', 'Bairro': i['bairro'] or '',
            'Cidade': i['cidade'] or '', 'UnMed': 'UN',
            'Descricao': 'Sessões de Psicoterapia',
            'VlrUnit': i['total_fmt'], '_sessoes': i['sessoes'],
            '_total_recebido': i['total_fmt'],
        } for i in itens]
        return Response(fjson.dumps(resultado, ensure_ascii=False, indent=2),
                        mimetype='application/json',
                        headers={'Content-Disposition': f'attachment; filename=extrato_{extrato["mes"]:02d}_{extrato["ano"]}.json'})

    return render_template('extratos/visualizar.html', extrato=extrato, itens=itens)


@bp.route('/extratos/<int:id>/finalizar', methods=['POST'])
def finalizar(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT finalizado FROM extratos WHERE id=%s', (id,))
    e = cursor.fetchone()
    if e:
        cursor.execute('UPDATE extratos SET finalizado=%s WHERE id=%s', (0 if e['finalizado'] else 1, id))
        conn.commit()
    cursor.close(); conn.close()
    return redirect(url_for('extratos.lista'))


@bp.route('/extratos/<int:id>/excluir', methods=['POST'])
def excluir(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM extratos WHERE id = %s', (id,))
    conn.commit(); cursor.close(); conn.close()
    return redirect(url_for('extratos.lista'))
