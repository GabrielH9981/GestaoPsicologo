from flask import Blueprint, render_template, request, redirect, url_for
from db import get_db_connection

bp = Blueprint('relatorios', __name__)


@bp.route('/relatorios/novo', methods=['GET', 'POST'])
def novo():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        paciente_id = request.form['paciente_id']
        cursor.execute('SELECT valor_sessao FROM pacientes WHERE id = %s', (paciente_id,))
        res = cursor.fetchone()
        valor = float(str(res['valor_sessao']).replace(',', '.')) if res else 0
        cursor.execute(
            'INSERT INTO relatorios (paciente_id, titulo, data, conteudo, tipo, valor_sessao) VALUES (%s,%s,%s,%s,%s,%s)',
            (paciente_id, request.form['titulo'], request.form['data'],
             request.form['conteudo'], request.form['tipo'], valor)
        )
        conn.commit(); cursor.close(); conn.close()
        return redirect(url_for('pacientes.perfil', id=paciente_id))
    cursor.execute('SELECT id, nome FROM pacientes ORDER BY nome ASC')
    pacientes = cursor.fetchall()
    cursor.close(); conn.close()
    return render_template('relatorios/novo.html', pacientes=pacientes)


@bp.route('/relatorios/<int:id>')
def visualizar(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM relatorios WHERE id = %s', (id,))
    relatorio = cursor.fetchone()
    cursor.close(); conn.close()
    if not relatorio:
        return 'Relatório não encontrado', 404
    return render_template('relatorios/visualizar.html', relatorio=relatorio)


@bp.route('/relatorios/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        cursor.execute(
            'UPDATE relatorios SET titulo=%s, data=%s, conteudo=%s, tipo=%s WHERE id=%s',
            (request.form['titulo'], request.form['data'],
             request.form['conteudo'], request.form['tipo'], id)
        )
        conn.commit(); cursor.close(); conn.close()
        return redirect(url_for('relatorios.visualizar', id=id))
    cursor.execute('SELECT * FROM relatorios WHERE id = %s', (id,))
    relatorio = cursor.fetchone()
    cursor.close(); conn.close()
    if not relatorio:
        return 'Relatório não encontrado', 404
    return render_template('relatorios/editar.html', relatorio=relatorio)


@bp.route('/relatorios/<int:id>/excluir', methods=['POST'])
def excluir(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT paciente_id FROM relatorios WHERE id = %s', (id,))
    res = cursor.fetchone()
    if not res:
        cursor.close(); conn.close()
        return 'Relatório não encontrado', 404
    cursor.execute('DELETE FROM relatorios WHERE id = %s', (id,))
    conn.commit(); cursor.close(); conn.close()
    return redirect(url_for('pacientes.perfil', id=res['paciente_id']))
