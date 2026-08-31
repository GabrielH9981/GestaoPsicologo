from flask import Blueprint, render_template, request, redirect, url_for
from db import get_db_connection

bp = Blueprint('gastos', __name__)

CATEGORIAS = ['Impostos', 'Contabilidade', 'Aluguel', 'Assinaturas', 'Marketing', 'Equipamentos', 'Outros']


@bp.route('/gastos')
def lista():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM gastos ORDER BY categoria, nome')
    gastos = cursor.fetchall()
    cursor.close(); conn.close()
    return render_template('gastos/lista.html', gastos=gastos, categorias=CATEGORIAS)


@bp.route('/gastos/novo', methods=['POST'])
def novo():
    nome = request.form.get('nome', '').strip()
    categoria = request.form.get('categoria', '').strip() or 'Outros'
    valor = request.form.get('valor_padrao', '').strip() or None
    fixo = 1 if request.form.get('fixo') else 0
    if nome:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO gastos (nome, categoria, valor_padrao, fixo) VALUES (%s,%s,%s,%s)',
            (nome, categoria, valor, fixo)
        )
        conn.commit(); cursor.close(); conn.close()
    return redirect(url_for('gastos.lista'))


@bp.route('/gastos/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        categoria = request.form.get('categoria', '').strip() or 'Outros'
        valor = request.form.get('valor_padrao', '').strip() or None
        fixo = 1 if request.form.get('fixo') else 0
        cursor.execute(
            'UPDATE gastos SET nome=%s, categoria=%s, valor_padrao=%s, fixo=%s WHERE id=%s',
            (nome, categoria, valor, fixo, id)
        )
        conn.commit(); cursor.close(); conn.close()
        return redirect(url_for('gastos.lista'))
    cursor.execute('SELECT * FROM gastos WHERE id=%s', (id,))
    gasto = cursor.fetchone()
    cursor.close(); conn.close()
    return render_template('gastos/editar.html', gasto=gasto, categorias=CATEGORIAS)


@bp.route('/gastos/<int:id>/excluir', methods=['POST'])
def excluir(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM gastos WHERE id=%s', (id,))
    conn.commit(); cursor.close(); conn.close()
    return redirect(url_for('gastos.lista'))


@bp.route('/painel/gastos/vincular', methods=['POST'])
def vincular():
    mes = request.form.get('mes', type=int)
    ano = request.form.get('ano', type=int)
    gasto_id = request.form.get('gasto_id', type=int)
    valor = request.form.get('valor', '').strip()
    # cadastro rapido inline
    nome_novo = request.form.get('nome_novo', '').strip()
    if nome_novo and not gasto_id:
        categoria = request.form.get('categoria_nova', 'Outros').strip() or 'Outros'
        fixo = 1 if request.form.get('fixo_novo') else 0
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO gastos (nome, categoria, valor_padrao, fixo) VALUES (%s,%s,%s,%s)',
            (nome_novo, categoria, valor or None, fixo)
        )
        gasto_id = cursor.lastrowid
        conn.commit(); cursor.close(); conn.close()
    if gasto_id and valor:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO gasto_mes (gasto_id, mes, ano, valor) VALUES (%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE valor=%s
        ''', (gasto_id, mes, ano, valor, valor))
        conn.commit(); cursor.close(); conn.close()
    return redirect(url_for('painel.index', mes=mes, ano=ano))


@bp.route('/painel/gastos/<int:id>/remover', methods=['POST'])
def remover_mes(id):
    mes = request.form.get('mes', type=int)
    ano = request.form.get('ano', type=int)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM gasto_mes WHERE id=%s', (id,))
    conn.commit(); cursor.close(); conn.close()
    return redirect(url_for('painel.index', mes=mes, ano=ano))
