import subprocess
import datetime
import os

# Configurações do banco de dados
host = 'localhost'
user = 'root'
password = 'root'
database = 'sistema_pacientes'

# Caminho do mysqldump
mysqldump_path = r'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe'

# Pasta onde o backup será salvo
backup_dir = r'C:\Users\Aline\Desktop\GestaoPsicologo\GestaoPsicologo\backups'  # Altere para o local desejado
os.makedirs(backup_dir, exist_ok=True)

# Nome do arquivo com data/hora
data_hora = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
arquivo_backup = f'{database}_backup_{data_hora}.sql'
caminho_completo = os.path.join(backup_dir, arquivo_backup)

# Comando mysqldump com o caminho completo
comando = [
    mysqldump_path,
    f'-h{host}',
    f'-u{user}',
    f'-p{password}',
    database
]

try:
    with open(caminho_completo, 'w', encoding='utf-8') as f:
        subprocess.run(comando, stdout=f, check=True)
    print(f'✅ Backup criado com sucesso: {caminho_completo}')

except subprocess.CalledProcessError as e:
    print(f'❌ Erro ao executar mysqldump: {e}')

except Exception as ex:
    print(f'❌ Erro inesperado: {ex}')
