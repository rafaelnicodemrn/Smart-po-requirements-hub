# core/inbox_watcher.py
import sys
import os
import time
from datetime import datetime

import requests

# Adiciona o diretório raiz ao sys.path para imports absolutos funcionarem de forma independente
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from config import APPS_SCRIPT_WEB_APP_URL
from core.database import inicializar_banco, salvar_demandas

# Intervalo entre cada verificação, em segundos (5 minutos)
INTERVALO_SEGUNDOS = 300


def buscar_demandas_pendentes() -> list:
    """Faz GET no Web App do Apps Script e retorna a lista de demandas pendentes."""
    resposta = requests.get(APPS_SCRIPT_WEB_APP_URL, timeout=30)
    resposta.raise_for_status()
    return resposta.json()


def avisar_planilha_processada(linhas_processadas: list) -> None:
    """Faz POST no Web App avisando quais linhas foram processadas, para o
    Apps Script atualizar a Coluna C (status) na planilha."""
    requests.post(APPS_SCRIPT_WEB_APP_URL, json={"rows": linhas_processadas}, timeout=30)


def main():
    print(f"[{datetime.now()}] [INFO] Iniciando Inbox Watcher (Outbound Polling via Apps Script)...")
    try:
        inicializar_banco()
        print(f"[{datetime.now()}] [INFO] Banco de dados inicializado com sucesso.")
    except Exception as e:
        print(f"[{datetime.now()}] [ERRO] Erro ao inicializar o banco de dados: {e}")

    while True:
        try:
            print(f"[{datetime.now()}] [INFO] Buscando demandas pendentes no Apps Script...")
            demandas_pendentes = buscar_demandas_pendentes()

            if demandas_pendentes:
                print(f"[{datetime.now()}] [INFO] Encontradas {len(demandas_pendentes)} demandas pendentes. Salvando no banco de dados...")
                salvar_demandas(demandas_pendentes)

                linhas_processadas = [demanda.get("row") for demanda in demandas_pendentes if demanda.get("row")]
                avisar_planilha_processada(linhas_processadas)
                print(f"[{datetime.now()}] [INFO] {len(demandas_pendentes)} demandas salvas e planilha avisada com sucesso.")
            else:
                print(f"[{datetime.now()}] [INFO] Nenhuma demanda nova pendente no Apps Script.")

        except Exception as e:
            # Proteção contra falhas de rede ou indisponibilidade do Apps Script,
            # para não derrubar o worker em background.
            print(f"[{datetime.now()}] [ERRO] Erro no ciclo de processamento da inbox: {e}")
            print(f"[{datetime.now()}] [INFO] O monitor continuará ativo e tentará novamente no próximo ciclo.")

        print(f"[{datetime.now()}] Aguardando 5 minutos (300s) para nova verificação...")
        time.sleep(INTERVALO_SEGUNDOS)


if __name__ == "__main__":
    main()
