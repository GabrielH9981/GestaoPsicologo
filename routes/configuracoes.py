import os, subprocess, tempfile, shutil, glob
from flask import Blueprint, render_template, request, redirect, url_for, send_file, flash
from db import get_db_connection
from werkzeug.utils import secure_filename

bp = Blueprint('configuracoes', __name__)

LOGO_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads')
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'svg', 'webp'}

DEFAULTS = {
    'tema':              'claro',
    'paleta':            'indigo',
    'fonte':             'Inter',
    'home_stats':        '1',
    'home_aniversarios': '1',
    'home_extratos':     '1',
    'aniversario_dias':  '30',
    'app_nome':          'Gestão Psi',
    'app_subtitulo':     'Sistema de Pacientes',
    'app_logo':          '',
}

PALETAS = {
    'indigo': {'primary': '#4f46e5', 'primary_dark': '#3730a3', 'primary_light': '#ede9fe'},
    'violet': {'primary': '#7c3aed', 'primary_dark': '#5b21b6', 'primary_light': '#ede9fe'},
    'rose':   {'primary': '#e11d48', 'primary_dark': '#9f1239', 'primary_light': '#ffe4e6'},
    'teal':   {'primary': '#0d9488', 'primary_dark': '#0f766e', 'primary_light': '#ccfbf1'},
    'amber':  {'primary': '#d97706', 'primary_dark': '#92400e', 'primary_light': '#fef3c7'},
    'slate':  {'primary': '#475569', 'primary_dark': '#1e293b', 'primary_light': '#f1f5f9'},
}

FONTES = ['Inter', 'Poppins', 'DM Sans', 'Nunito', 'Roboto']


def get_config():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT chave, valor FROM configuracoes')
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    cfg = dict(DEFAULTS)
    for r in rows:
        cfg[r['chave']] = r['valor']
    return cfg


DB_USER = 'root'
DB_PASS = 'root'
DB_NAME = 'sistema_pacientes'


def _find_mysql_bin(exe):
    """Encontra mysqldump.exe / mysql.exe no PATH ou nas pastas padrão do MySQL no Windows."""
    found = shutil.which(exe)
    if found:
        return found
    for folder in glob.glob(r'C:\Program Files\MySQL\MySQL Server *\bin'):
        path = os.path.join(folder, exe)
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f'{exe} não encontrado. Adicione o MySQL ao PATH do sistema.')


@bp.route('/configuracoes/exportar')
def exportar():
    dump = os.path.join(tempfile.gettempdir(), 'sistema_pacientes_backup.sql')
    try:
        resultado = subprocess.run([
            _find_mysql_bin('mysqldump.exe'),
            f'-u{DB_USER}', f'-p{DB_PASS}',
            '--databases', DB_NAME,
            '--routines', '--triggers', '--single-transaction',
            '--add-drop-database', '--add-drop-table'
        ], stdout=open(dump, 'w', encoding='utf-8'), stderr=subprocess.PIPE, text=True)
        if resultado.returncode != 0:
            return f'<pre>Erro na exportação:\n{resultado.stderr}</pre>', 500
    except Exception as e:
        return f'<pre>Exceção: {e}</pre>', 500
    from datetime import date
    nome = f'backup_{date.today().isoformat()}.sql'
    return send_file(dump, as_attachment=True, download_name=nome, mimetype='text/plain')


@bp.route('/configuracoes/importar', methods=['POST'])
def importar():
    arquivo = request.files.get('sql_file')
    print(f'[IMPORT] arquivo={arquivo}, filename={getattr(arquivo, "filename", None)}')
    if not arquivo or not arquivo.filename.endswith('.sql'):
        print('[IMPORT] Arquivo invalido ou sem .sql, redirecionando')
        return redirect(url_for('configuracoes.index'))
    tmp = os.path.join(tempfile.gettempdir(), 'import_upload.sql')
    arquivo.save(tmp)
    print(f'[IMPORT] Salvo em {tmp}, tamanho={os.path.getsize(tmp)} bytes')
    try:
        with open(tmp, 'rb') as f:
            conteudo_bytes = f.read()
        conteudo_str = conteudo_bytes.decode('utf-8', errors='replace')
        tem_create_db = 'CREATE DATABASE' in conteudo_str.upper()
        print(f'[IMPORT] tem_create_db={tem_create_db}')
        cmd = [_find_mysql_bin('mysql.exe'), f'-u{DB_USER}', f'-p{DB_PASS}',
               '--default-character-set=utf8mb4']
        if not tem_create_db:
            cmd.append(DB_NAME)
        print(f'[IMPORT] cmd={cmd}')
        resultado = subprocess.run(cmd, input=conteudo_bytes, capture_output=True)
        print(f'[IMPORT] returncode={resultado.returncode}')
        print(f'[IMPORT] stderr={resultado.stderr.decode("utf-8", errors="replace")}')
    except Exception as e:
        print(f'[IMPORT] EXCECAO: {e}')
        os.remove(tmp)
        return f'<pre>Excecao: {e}</pre>', 500
    os.remove(tmp)
    if resultado.returncode != 0:
        stderr = resultado.stderr.decode('utf-8', errors='replace') if isinstance(resultado.stderr, bytes) else resultado.stderr
        return f'<pre>Erro na importacao:\n{stderr}</pre>', 500
    print('[IMPORT] Sucesso!')
    return redirect(url_for('configuracoes.index'))


@bp.route('/configuracoes/excluir-logo')
def excluir_logo():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT valor FROM configuracoes WHERE chave=%s', ('app_logo',))
    row = cursor.fetchone()
    if row:
        filepath = os.path.join(LOGO_FOLDER, row['valor'])
        if os.path.exists(filepath):
            os.remove(filepath)
        cursor.execute('DELETE FROM configuracoes WHERE chave=%s', ('app_logo',))
        conn.commit()
    cursor.close(); conn.close()
    return redirect(url_for('configuracoes.index'))


@bp.route('/configuracoes', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        os.makedirs(LOGO_FOLDER, exist_ok=True)
        conn = get_db_connection()
        cursor = conn.cursor()
        for chave in DEFAULTS:
            if chave == 'app_logo':
                continue
            if chave.startswith('home_'):
                valor = '1' if request.form.get(chave) else '0'
            else:
                valor = request.form.get(chave, DEFAULTS[chave])
            cursor.execute(
                'INSERT INTO configuracoes (chave, valor) VALUES (%s,%s) ON DUPLICATE KEY UPDATE valor=%s',
                (chave, valor, valor)
            )
        # logo upload
        logo = request.files.get('app_logo')
        if logo and logo.filename:
            ext = logo.filename.rsplit('.', 1)[-1].lower()
            if ext in ALLOWED_EXT:
                fname = f'logo.{ext}'
                logo.save(os.path.join(LOGO_FOLDER, fname))
                cursor.execute(
                    'INSERT INTO configuracoes (chave, valor) VALUES (%s,%s) ON DUPLICATE KEY UPDATE valor=%s',
                    ('app_logo', fname, fname)
                )
        conn.commit(); cursor.close(); conn.close()
        return redirect(url_for('configuracoes.index'))
    cfg = get_config()
    return render_template('configuracoes/index.html', cfg=cfg,
                           paletas=PALETAS, fontes=FONTES)
