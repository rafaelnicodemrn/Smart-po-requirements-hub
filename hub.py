import os
import sys
import time
import json
import requests
from requests.auth import HTTPBasicAuth

# === CONFIGURAÇÕES GERAIS (HIGIENIZADAS VIA ENV) ===
JIRA_URL = os.getenv("JIRA_URL", "https://seu-dominio.atlassian.net")
USER_EMAIL = os.getenv("JIRA_EMAIL", "seu_email@dominio.com")
API_TOKEN = os.getenv("JIRA_API_TOKEN", "SEU_TOKEN_AQUI")
SIGLA_DO_SEU_PROJETO = os.getenv("JIRA_PROJETO_KEY", "PRJ")

auth = HTTPBasicAuth(USER_EMAIL, API_TOKEN)
headers = {"Accept": "application/json", "Content-Type": "application/json"}

def executar_busca_jql(jql_query, max_results=50, campos="summary,status,priority,issuetype"):
    url = f"{JIRA_URL}/rest/api/3/search/jql"
    query = {'jql': jql_query, 'maxResults': max_results, 'fields': campos}
    try:
        response = requests.request("GET", url, headers=headers, params=query, auth=auth)
        if response.status_code == 200:
            return response.json().get("issues", [])
        return []
    except Exception:
        return []

def resumo_diario():
    print("\n[JIRA] Buscando cards ATRIBUÍDOS a você...")
    jql = 'assignee = currentUser() ORDER BY updated DESC'
    issues = executar_busca_jql(jql, max_results=10)
    print(f"[Sucesso] Encontrados {len(issues)} cards.\n")
    for issue in issues:
        fields = issue.get("fields", {})
        print(f" ➔ [{issue.get('key')}] {fields.get('summary')} | Status: {fields.get('status', {}).get('name')}")

def rotina_mensal():
    print(f"\n==================================================")
    print(f"  INICIANDO ROTINA MENSAL DE PRODUTO - SQUAD CEV  ")
    print(f"==================================================")
    
    jql_entregas = f'project = {SIGLA_DO_SEU_PROJETO} AND statusCategory = Done AND resolved >= startOfMonth()'
    entregas = executar_busca_jql(jql_entregas, max_results=30)
    print(f"\n[1/3 ENTREGA DO MÊS] Total de itens concluídos: {len(entregas)}")
    for item in entregas:
        print(f" ✔ [{item.get('key')}] {item.get('fields', {}).get('summary')}")
        
    jql_futuro = f'project = {SIGLA_DO_SEU_PROJETO} AND statusCategory != Done ORDER BY priority DESC'
    futuros = executar_busca_jql(jql_futuro, max_results=5)
    print(f"\n[2/3 PLANEJAMENTO PRÓXIMO MÊS] Principais itens abertos por prioridade:")
    for item in futuros:
        print(f" ➔ [{item.get('key')}] {item.get('fields', {}).get('summary')}")

    jql_epicos = f'project = {SIGLA_DO_SEU_PROJETO} AND issuetype = "Epic" AND statusCategory != Done'
    epicos = executar_busca_jql(jql_epicos, max_results=20)
    print(f"\n[3/3 AUDITORIA DE ÉPICOS] Verificando Épicos abertos:")
    for epic in epicos:
        epic_key = epic.get("key")
        epic_summary = epic.get('fields', {}).get('summary')
        filhos_pendentes = executar_busca_jql(f'parent = {epic_key} AND statusCategory != Done', max_results=1)
        if not filhos_pendentes:
            print(f" ⚠ ALERTA: O Épico [{epic_key}] '{epic_summary}' não possui pendências. Pode ser fechado!")
            
    print(f"\n==================================================\n")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "mensal":
        rotina_mensal()
    else:
        resumo_diario()