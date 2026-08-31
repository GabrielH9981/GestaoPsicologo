@echo off

:: Executa o app.py em segundo plano
start "" /B python app.py

:: Aguarda 3 segundos para garantir que o servidor suba
timeout /t 3 > nul

:: Abre o navegador no localhost
start http://localhost:5000

exit
