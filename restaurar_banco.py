import subprocess

# Caminho dos arquivos
mysql_path = r'C:\Program Files\MySQL\MySQL Server 8.2\bin\mysql.exe'
backup_file = r'C:\Users\Gabriel\Desktop\Projetos\Aline\GestaoPsicologo\backups\sistema_pacientes_backup_2026-08-31_12-32-03.sql'

# Comando para restaurar
comando = [
    mysql_path,
    '-u', 'root',
    '-proot',  # sem espaço após o -p
    'sistema_pacientes'
]

try:
    with open(backup_file, 'r', encoding='utf-8') as f:
        subprocess.run(comando, stdin=f, check=True)
    print('Backup restaurado com sucesso.')

except subprocess.CalledProcessError as e:
    print(f'Erro ao restaurar o backup: {e}')

except Exception as ex:
    print(f'Erro inesperado: {ex}')
