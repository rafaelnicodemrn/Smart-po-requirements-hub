# core/jira_client.py
import requests
from requests.auth import HTTPBasicAuth
from config import JIRA_URL, JIRA_EMAIL, JIRA_TOKEN

def criar_issue(payload: dict) -> str:
    """
    Envia o payload para a API v3 do Jira e retorna a chave do ticket criado.
    """
    url = f"{JIRA_URL}/rest/api/3/issue"
    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_TOKEN)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers, auth=auth, timeout=30)
        if response.status_code == 201:
            return response.json().get('key')
        else:
            raise Exception(f"Erro {response.status_code}: {response.text}")
    except Exception as e:
        raise Exception(f"Falha ao conectar com o Jira: {e}")