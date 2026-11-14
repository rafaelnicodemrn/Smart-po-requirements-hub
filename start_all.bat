@echo off
title Smart PO Requirements Hub
echo Iniciando o Ecossistema do PO...

:: Inicia o Watcher de E-mails silenciosamente em uma nova janela minimizada
start /min "Inbox Watcher" cmd /c ".\venv\Scripts\activate && python core\inbox_watcher.py"

:: Inicia a interface do Streamlit na janela atual
call .\venv\Scripts\activate
streamlit run app.py