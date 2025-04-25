from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from config import MYSQL_CONFIG
from datetime import datetime


app = Flask(__name__)

# Conexão com o banco de dados MySQL
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='aline',  # Usuário que você criou
        password='1234',  # Senha do usuário
        database='meu_banco'
    )

@app.route('/')
def home():
    return render_template('home.html')


# Rota para cadastrar paciente
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro_paciente():
    if request.method == 'POST':
        nome = request.form['nome']
        data_nascimento = request.form['data_nascimento']
        telefone = request.form['telefone']
        valor_sessao = request.form['valor_sessao']
        pacote_mensal = 'pacote_mensal' in request.form
        valor_pacote = request.form['valor_pacote'] if pacote_mensal else None

        # Conexão com o banco de dados
        conn = get_db_connection()
        cursor = conn.cursor()

        # Inserir os dados do paciente no banco
        cursor.execute('''INSERT INTO pacientes (nome, data_nascimento, telefone, valor_sessao, pacote_mensal, valor_pacote) 
                          VALUES (%s, %s, %s, %s, %s, %s)''',
                       (nome, data_nascimento, telefone, valor_sessao, pacote_mensal, valor_pacote))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('lista_pacientes'))

    return render_template('cadastro_paciente.html')


# Rota para listar pacientes
@app.route('/pacientes')
def lista_pacientes():
    busca = request.args.get('busca', '')

    conn = get_db_connection()
    cursor = conn.cursor()

    if busca:
        cursor.execute("SELECT * FROM pacientes WHERE nome LIKE %s", ('%' + busca + '%',))
    else:
        cursor.execute("SELECT * FROM pacientes")

    pacientes = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('lista_pacientes.html', pacientes=pacientes, busca=busca)


# Rota para visualizar o perfil do paciente
@app.route('/paciente/<int:id>')
def perfil_paciente(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM pacientes WHERE id = %s', (id,))
    paciente = cursor.fetchone()

    data_filtro = request.args.get('data')
    if data_filtro:
        cursor.execute('''
            SELECT id, titulo, data FROM relatorios
            WHERE paciente_id = %s AND data = %s
            ORDER BY data DESC
        ''', (id, data_filtro))
    else:
        cursor.execute('''
            SELECT id, titulo, data FROM relatorios
            WHERE paciente_id = %s
            ORDER BY data DESC
        ''', (id,))

    relatorios = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('perfil_paciente.html', paciente=paciente, relatorios=relatorios, data_filtro=data_filtro)


@app.route('/paciente/<int:id>/editar', methods=['GET', 'POST'])
def editar_paciente(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        data_nascimento = request.form['data_nascimento']
        telefone = request.form['telefone']
        valor_sessao = request.form['valor_sessao']
        pacote_mensal = True if request.form.get('pacote_mensal') == 'on' else False
        valor_pacote = request.form.get('valor_pacote', '')

        cursor.execute('''
            UPDATE pacientes
            SET nome = %s, data_nascimento = %s, telefone = %s,
                valor_sessao = %s, pacote_mensal = %s, valor_pacote = %s
            WHERE id = %s
        ''', (nome, data_nascimento, telefone, valor_sessao, pacote_mensal, valor_pacote, id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('perfil_paciente', id=id))

    cursor.execute('SELECT * FROM pacientes WHERE id = %s', (id,))
    paciente = cursor.fetchone()
    cursor.close()
    conn.close()

    if not paciente:
        return "Paciente não encontrado", 404

    return render_template('editar_paciente.html', paciente=paciente)


@app.route('/paciente/<int:id>/excluir')
def excluir_paciente(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Excluir relatórios do paciente primeiro para manter integridade referencial
    cursor.execute('DELETE FROM relatorios WHERE paciente_id = %s', (id,))
    cursor.execute('DELETE FROM pacientes WHERE id = %s', (id,))
    conn.commit()

    cursor.close()
    conn.close()
    return redirect(url_for('lista_pacientes'))


@app.route('/relatorio/novo', methods=['GET', 'POST'])
def novo_relatorio():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        paciente_id = request.form['paciente_id']
        titulo = request.form['titulo']
        data = request.form['data']
        conteudo = request.form['conteudo']

        cursor.execute('''
            INSERT INTO relatorios (paciente_id, titulo, data, conteudo)
            VALUES (%s, %s, %s, %s)
        ''', (paciente_id, titulo, data, conteudo))

        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('lista_pacientes'))

    # Se GET, buscar todos os pacientes para preencher o select
    cursor.execute('SELECT id, nome FROM pacientes')
    pacientes = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('cadastro_relatorio.html', pacientes=pacientes)


@app.route('/relatorio/<int:id>')
def visualizar_relatorio(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT titulo, data, conteudo FROM relatorios WHERE id = %s', (id,))
    relatorio = cursor.fetchone()

    cursor.close()
    conn.close()

    if not relatorio:
        return "Relatório não encontrado", 404

    return render_template('visualizar_relatorio.html', relatorio=relatorio, id=id)


@app.route('/relatorio/<int:id>/editar', methods=['GET', 'POST'])
def editar_relatorio(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        titulo = request.form['titulo']
        data = request.form['data']
        conteudo = request.form['conteudo']

        cursor.execute('''
            UPDATE relatorios
            SET titulo = %s, data = %s, conteudo = %s
            WHERE id = %s
        ''', (titulo, data, conteudo, id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('visualizar_relatorio', id=id))

    cursor.execute('SELECT titulo, data, conteudo FROM relatorios WHERE id = %s', (id,))
    relatorio = cursor.fetchone()
    cursor.close()
    conn.close()

    if not relatorio:
        return "Relatório não encontrado", 404

    return render_template('editar_relatorio.html', relatorio=relatorio, id=id)


@app.route('/relatorio/<int:id>/excluir')
def excluir_relatorio(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Primeiro, buscar paciente_id antes de excluir, se quiser redirecionar para o perfil do paciente depois
    cursor.execute('SELECT paciente_id FROM relatorios WHERE id = %s', (id,))
    resultado = cursor.fetchone()

    if not resultado:
        cursor.close()
        conn.close()
        return "Relatório não encontrado", 404

    paciente_id = resultado[0]

    cursor.execute('DELETE FROM relatorios WHERE id = %s', (id,))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('perfil_paciente', id=paciente_id))


@app.route('/painel')
def painel():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Total de pacientes
    cursor.execute("SELECT COUNT(*) AS total FROM pacientes")
    total_pacientes = cursor.fetchone()['total']

    # Mês e ano selecionados (ou padrão para o mês atual)
    hoje = datetime.today()
    mes = request.args.get('mes', default=hoje.month, type=int)
    ano = request.args.get('ano', default=hoje.year, type=int)

    # Primeiro e último dia do mês selecionado
    primeiro_dia = datetime(ano, mes, 1).strftime('%Y-%m-%d')
    if mes == 12:
        ultimo_dia = datetime(ano + 1, 1, 1).strftime('%Y-%m-%d')
    else:
        ultimo_dia = datetime(ano, mes + 1, 1).strftime('%Y-%m-%d')

    # Relatórios no período
    cursor.execute("""
        SELECT r.paciente_id, COUNT(*) AS qtd_sessoes, p.nome, p.valor_sessao
        FROM relatorios r
        JOIN pacientes p ON r.paciente_id = p.id
        WHERE r.data >= %s AND r.data < %s
        GROUP BY r.paciente_id
    """, (primeiro_dia, ultimo_dia))

    resultados = cursor.fetchall()

    total_sessoes = 0
    total_financeiro = 0.0
    detalhamento = []

    for row in resultados:
        qtd = row['qtd_sessoes']
        valor = float(row['valor_sessao'].replace(',', '.'))
        total = round(qtd * valor, 2)

        detalhamento.append({
            'nome': row['nome'],
            'qtd_sessoes': qtd,
            'valor_sessao': row['valor_sessao'],
            'total_gerado': f"{total:.2f}".replace('.', ',')
        })

        total_sessoes += qtd
        total_financeiro += total

    conn.close()

    return render_template('painel.html',
                           total_pacientes=total_pacientes,
                           total_sessoes=total_sessoes,
                           total_financeiro=f"{total_financeiro:.2f}".replace('.', ','),
                           detalhamento=detalhamento,
                           mes=mes,
                           ano=ano,
                           ano_atual=hoje.year)


if __name__ == '__main__':
    app.run(debug=True)
