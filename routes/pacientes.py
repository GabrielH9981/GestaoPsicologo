from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import get_db_connection
import unicodedata, re

def _normalize(s):
    s = unicodedata.normalize('NFD', s.upper())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^A-Z0-9 ]', '', s).strip()

bp = Blueprint('pacientes', __name__)


@bp.route('/pacientes')
def lista():
    busca = request.args.get('busca', '')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if busca:
        cursor.execute("SELECT * FROM pacientes WHERE nome LIKE %s ORDER BY nome", ('%' + busca + '%',))
    else:
        cursor.execute("SELECT * FROM pacientes ORDER BY nome")
    pacientes = cursor.fetchall()
    cursor.close(); conn.close()
    return render_template('pacientes/lista.html', pacientes=pacientes, busca=busca)


@bp.route('/pacientes/novo', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO pacientes (nome, data_nascimento, telefone, valor_sessao, pacote_mensal, valor_pacote) VALUES (%s,%s,%s,%s,%s,%s)',
            (request.form['nome'], request.form['data_nascimento'], request.form['telefone'],
             request.form['valor_sessao'], 'pacote_mensal' in request.form,
             request.form.get('valor_pacote') or None)
        )
        pac_id = cursor.lastrowid
        _salvar_dados_nota(cursor, pac_id=pac_id)
        conn.commit(); cursor.close(); conn.close()
        return redirect(url_for('pacientes.lista'))
    return render_template('pacientes/cadastro.html')


@bp.route('/pacientes/<int:id>')
def perfil(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM pacientes WHERE id = %s', (id,))
    paciente = cursor.fetchone()
    if not paciente:
        cursor.close(); conn.close()
        return 'Paciente não encontrado', 404
    data_filtro = request.args.get('data')
    q = 'SELECT id, titulo, data FROM relatorios WHERE paciente_id = %s'
    params = [id]
    if data_filtro:
        q += ' AND data = %s'
        params.append(data_filtro)
    q += ' ORDER BY data DESC'
    cursor.execute(q, params)
    relatorios = cursor.fetchall()
    cursor.close(); conn.close()
    return render_template('pacientes/perfil.html', paciente=paciente, relatorios=relatorios, data_filtro=data_filtro)


@bp.route('/pacientes/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        cursor.execute('''
            UPDATE pacientes SET nome=%s, data_nascimento=%s, telefone=%s,
            valor_sessao=%s, pacote_mensal=%s, valor_pacote=%s WHERE id=%s
        ''', (request.form['nome'], request.form['data_nascimento'], request.form['telefone'],
              request.form['valor_sessao'], request.form.get('pacote_mensal') == 'on',
              request.form.get('valor_pacote') or None, id))
        _salvar_dados_nota(cursor, pac_id=id, update=True)
        conn.commit(); cursor.close(); conn.close()
        return redirect(url_for('pacientes.perfil', id=id))
    cursor.execute('SELECT * FROM pacientes WHERE id = %s', (id,))
    paciente = cursor.fetchone()
    cursor.execute('SELECT * FROM dados_nota WHERE paciente_id = %s', (id,))
    nota = cursor.fetchone()
    cursor.close(); conn.close()
    if not paciente:
        return 'Paciente não encontrado', 404
    return render_template('pacientes/editar.html', paciente=paciente, nota=nota)


@bp.route('/pacientes/<int:id>/excluir', methods=['POST'])
def excluir(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM pacientes WHERE id = %s', (id,))
    conn.commit(); cursor.close(); conn.close()
    return redirect(url_for('pacientes.lista'))


@bp.route('/pacientes/<int:id>/nota', methods=['GET', 'POST'])
def dados_nota(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT id, nome FROM pacientes WHERE id = %s', (id,))
    paciente = cursor.fetchone()
    if not paciente:
        cursor.close(); conn.close()
        return 'Paciente não encontrado', 404
    if request.method == 'POST':
        _salvar_dados_nota(cursor, pac_id=id, update=True)
        conn.commit(); cursor.close(); conn.close()
        next_url = request.args.get('next') or request.form.get('next')
        return redirect(next_url or url_for('pacientes.dados_nota', id=id))
    cursor.execute('SELECT * FROM dados_nota WHERE paciente_id = %s', (id,))
    nota = cursor.fetchone()
    cursor.execute('''
        SELECT d.id, d.nome_extrato, dn.cpf, dn.cep, dn.logradouro, dn.numero, dn.bairro, dn.cidade
        FROM dependentes d LEFT JOIN dados_nota dn ON dn.dependente_id = d.id
        WHERE d.paciente_id = %s
    ''', (id,))
    dependentes = cursor.fetchall()
    cursor.close(); conn.close()
    return render_template('pacientes/dados_nota.html', paciente=paciente, nota=nota, dependentes=dependentes)


@bp.route('/dependentes/<int:id>/nota', methods=['POST'])
def dados_nota_dependente(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT paciente_id FROM dependentes WHERE id = %s', (id,))
    dep = cursor.fetchone()
    if not dep:
        cursor.close(); conn.close()
        return 'Dependente não encontrado', 404
    _salvar_dados_nota(cursor, dep_id=id, update=True)
    conn.commit(); cursor.close(); conn.close()
    return redirect(url_for('pacientes.dados_nota', id=dep['paciente_id']))


@bp.route('/pacientes/<int:id>/dependentes', methods=['GET', 'POST'])
def dependentes(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT id, nome FROM pacientes WHERE id = %s', (id,))
    paciente = cursor.fetchone()
    if not paciente:
        cursor.close(); conn.close()
        return 'Paciente não encontrado', 404
    if request.method == 'POST':
        nome = request.form.get('nome_extrato', '').strip()
        if nome:
            norm = _normalize(nome)
            try:
                cursor.execute(
                    'INSERT INTO dependentes (paciente_id, nome_extrato, nome_extrato_norm) VALUES (%s,%s,%s)',
                    (id, nome, norm)
                )
                conn.commit()
            except Exception:
                conn.rollback()
        cursor.close(); conn.close()
        return redirect(url_for('pacientes.dependentes', id=id))
    cursor.execute('SELECT * FROM dependentes WHERE paciente_id = %s ORDER BY nome_extrato', (id,))
    deps = cursor.fetchall()
    cursor.close(); conn.close()
    return render_template('pacientes/dependentes.html', paciente=paciente, dependentes=deps)


@bp.route('/dependentes/<int:id>/excluir', methods=['POST'])
def excluir_dependente(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT paciente_id FROM dependentes WHERE id = %s', (id,))
    dep = cursor.fetchone()
    if dep:
        cursor.execute('DELETE FROM dependentes WHERE id = %s', (id,))
        conn.commit()
    cursor.close(); conn.close()
    return redirect(url_for('pacientes.dependentes', id=dep['paciente_id']) if dep else url_for('pacientes.lista'))


def _salvar_dados_nota(cursor, pac_id=None, dep_id=None, update=False):
    campos = ('cpf', 'cep', 'logradouro', 'numero', 'bairro', 'cidade')
    v = {c: request.form.get(c, '').strip() or None for c in campos}
    if not any(v.values()):
        return
    if pac_id:
        cursor.execute('''
            INSERT INTO dados_nota (paciente_id, cpf, cep, logradouro, numero, bairro, cidade)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE cpf=%s,cep=%s,logradouro=%s,numero=%s,bairro=%s,cidade=%s
        ''', (pac_id, *v.values(), *v.values()))
    elif dep_id:
        cursor.execute('''
            INSERT INTO dados_nota (dependente_id, cpf, cep, logradouro, numero, bairro, cidade)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE cpf=%s,cep=%s,logradouro=%s,numero=%s,bairro=%s,cidade=%s
        ''', (dep_id, *v.values(), *v.values()))
