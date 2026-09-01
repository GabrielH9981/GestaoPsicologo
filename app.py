from flask import Flask, render_template
from routes import pacientes, relatorios, extratos, painel, gastos, configuracoes
from routes.configuracoes import get_config, PALETAS
from db import get_db_connection
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = 'gestao-psi-secret'

app.register_blueprint(pacientes.bp)
app.register_blueprint(relatorios.bp)
app.register_blueprint(extratos.bp)
app.register_blueprint(painel.bp)
app.register_blueprint(gastos.bp)
app.register_blueprint(configuracoes.bp)

@app.context_processor
def inject_config():
    cfg = get_config()
    paleta = PALETAS.get(cfg['paleta'], PALETAS['indigo'])
    return dict(cfg=cfg, paleta=paleta)


@app.route('/')
def home():
    cfg = get_config()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    hoje = date.today()
    mes, ano = hoje.month, hoje.year

    cursor.execute("SELECT COUNT(*) AS total FROM pacientes")
    total_pacientes = cursor.fetchone()['total']

    cursor.execute('''
        SELECT COUNT(*) AS total FROM relatorios
        WHERE MONTH(data)=%s AND YEAR(data)=%s AND tipo='Relatório'
    ''', (mes, ano))
    total_sessoes = cursor.fetchone()['total']

    cursor.execute('''
        SELECT COALESCE(SUM(i.total_valor),0) AS total
        FROM extrato_itens i JOIN extratos e ON e.id=i.extrato_id
        WHERE e.mes=%s AND e.ano=%s AND i.ignorado=0
    ''', (mes, ano))
    total_recebido = float(cursor.fetchone()['total'])

    cursor.execute('''
        SELECT COALESCE(SUM(gm.valor),0) AS total
        FROM gasto_mes gm WHERE gm.mes=%s AND gm.ano=%s
    ''', (mes, ano))
    total_gastos = float(cursor.fetchone()['total'])
    liquido = total_recebido - total_gastos

    dias = int(cfg.get('aniversario_dias', 30))
    aniversarios = []
    if cfg.get('home_aniversarios') == '1':
        cursor.execute("SELECT id, nome, data_nascimento FROM pacientes WHERE data_nascimento IS NOT NULL")
        for p in cursor.fetchall():
            try:
                dn = p['data_nascimento']
                proximo = dn.replace(year=hoje.year)
                if proximo < hoje:
                    proximo = dn.replace(year=hoje.year + 1)
                delta = (proximo - hoje).days
                if 0 <= delta <= dias:
                    aniversarios.append({**p, 'delta': delta, 'proximo': proximo})
            except Exception:
                pass
        aniversarios.sort(key=lambda x: x['delta'])

    extratos_pendentes = []
    if cfg.get('home_extratos') == '1':
        cursor.execute('''
            SELECT e.id, e.mes, e.ano,
                   SUM(CASE WHEN i.ignorado=0 AND i.paciente_id IS NULL THEN 1 ELSE 0 END) AS pendentes
            FROM extratos e JOIN extrato_itens i ON i.extrato_id=e.id
            WHERE e.finalizado=0
            GROUP BY e.id HAVING pendentes > 0
            ORDER BY e.ano DESC, e.mes DESC
        ''')
        extratos_pendentes = cursor.fetchall()

    cursor.close(); conn.close()

    def fmt(v):
        return f"{v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    return render_template('home.html',
        total_pacientes=total_pacientes,
        total_sessoes=total_sessoes,
        total_recebido=fmt(total_recebido),
        total_gastos=fmt(total_gastos),
        liquido=fmt(liquido),
        liquido_val=liquido,
        aniversarios=aniversarios,
        extratos_pendentes=extratos_pendentes,
        mes_nome=hoje.strftime('%B/%Y').capitalize(),
        show_stats=cfg.get('home_stats') == '1',
    )


if __name__ == '__main__':
    app.run(debug=True, extra_files=[], exclude_patterns=['seleniumAline/*'])
