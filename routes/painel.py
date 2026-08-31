from datetime import datetime
from flask import Blueprint, render_template, request
from db import get_db_connection

bp = Blueprint('painel', __name__)


def _fmt(v):
    return f"{v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


@bp.route('/painel')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM pacientes")
    total_pacientes = cursor.fetchone()['total']

    hoje = datetime.today()
    mes = request.args.get('mes', default=hoje.month, type=int)
    ano = request.args.get('ano', default=hoje.year, type=int)

    primeiro_dia = datetime(ano, mes, 1).strftime('%Y-%m-%d')
    ultimo_dia = datetime(ano + 1, 1, 1).strftime('%Y-%m-%d') if mes == 12 else datetime(ano, mes + 1, 1).strftime('%Y-%m-%d')

    cursor.execute('''
        SELECT p.id, p.nome, COUNT(*) AS qtd_sessoes
        FROM relatorios r JOIN pacientes p ON r.paciente_id = p.id
        WHERE r.data >= %s AND r.data < %s AND r.tipo = 'Relatório'
        GROUP BY p.id, p.nome ORDER BY p.nome ASC
    ''', (primeiro_dia, ultimo_dia))
    sessoes_map = {r['id']: r for r in cursor.fetchall()}
    total_sessoes = sum(r['qtd_sessoes'] for r in sessoes_map.values())

    cursor.execute('''
        SELECT i.paciente_id, SUM(i.total_valor) AS recebido
        FROM extrato_itens i JOIN extratos e ON e.id = i.extrato_id
        WHERE e.mes=%s AND e.ano=%s AND i.ignorado=0 AND i.paciente_id IS NOT NULL
        GROUP BY i.paciente_id
    ''', (mes, ano))
    extrato_map = {r['paciente_id']: float(r['recebido']) for r in cursor.fetchall()}

    cursor.execute('''
        SELECT SUM(i.total_valor) AS total FROM extrato_itens i
        JOIN extratos e ON e.id = i.extrato_id
        WHERE e.mes=%s AND e.ano=%s AND i.ignorado=0
    ''', (mes, ano))
    total_financeiro = float((cursor.fetchone()['total']) or 0)

    todos_ids = set(sessoes_map) | set(extrato_map)
    nomes_map = {}
    if todos_ids:
        cursor.execute('SELECT id, nome FROM pacientes WHERE id IN (%s)' % ','.join(['%s'] * len(todos_ids)), list(todos_ids))
        nomes_map = {r['id']: r['nome'] for r in cursor.fetchall()}

    detalhamento = []
    for pac_id in sorted(todos_ids, key=lambda i: nomes_map.get(i, '')):
        recebido = extrato_map.get(pac_id, 0)
        detalhamento.append({
            'nome': nomes_map.get(pac_id, '—'),
            'qtd_sessoes': sessoes_map.get(pac_id, {}).get('qtd_sessoes', 0),
            'recebido': _fmt(recebido),
        })

    # gastos do mes
    cursor.execute('''
        SELECT gm.id, gm.valor, g.nome, g.categoria, g.fixo
        FROM gasto_mes gm JOIN gastos g ON g.id = gm.gasto_id
        WHERE gm.mes=%s AND gm.ano=%s
        ORDER BY g.categoria, g.nome
    ''', (mes, ano))
    gastos_mes = cursor.fetchall()
    total_gastos = sum(float(g['valor']) for g in gastos_mes)

    # gastos cadastrados para o select (excluindo os já vinculados no mês)
    cursor.execute('''
        SELECT g.* FROM gastos g
        WHERE g.id NOT IN (
            SELECT gasto_id FROM gasto_mes WHERE mes=%s AND ano=%s
        )
        ORDER BY g.categoria, g.nome
    ''', (mes, ano))
    gastos_disponiveis = cursor.fetchall()

    from routes.gastos import CATEGORIAS

    cursor.close(); conn.close()
    return render_template('painel/index.html',
                           total_pacientes=total_pacientes,
                           total_sessoes=total_sessoes,
                           total_financeiro=_fmt(total_financeiro),
                           total_gastos=_fmt(total_gastos),
                           liquido=_fmt(total_financeiro - total_gastos),
                           liquido_val=total_financeiro - total_gastos,
                           detalhamento=detalhamento,
                           gastos_mes=gastos_mes,
                           gastos_disponiveis=gastos_disponiveis,
                           categorias=CATEGORIAS,
                           mes=mes, ano=ano, ano_atual=hoje.year)
