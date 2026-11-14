# core/jira_client.py
import re
import requests
from difflib import SequenceMatcher
from requests.auth import HTTPBasicAuth
from config import JIRA_URL, JIRA_EMAIL, JIRA_TOKEN, PROJETO_KEY

# Limiar mínimo de similaridade textual para considerar duas issues como possíveis duplicatas
_LIMIAR_SIMILARIDADE = 0.75

# Stopwords em português a ignorar na extração da palavra-chave para o JQL
_STOPWORDS = {
    "o", "a", "os", "as", "um", "uma", "de", "do", "da", "dos", "das",
    "em", "no", "na", "nos", "nas", "ao", "à", "e", "é", "ou", "que",
    "se", "por", "para", "com", "não", "mais", "foi", "ser", "ter",
    "varejo", "compras",  # prefixos de área — não são palavras-chave úteis
}

def _extrair_palavra_chave(resumo: str) -> str:
    """
    Extrai a primeira palavra relevante do resumo (ignorando stopwords e prefixos de área)
    para usar como termo de busca no JQL.
    """
    # Remove o prefixo de área padronizado (ex: "VAREJO - ", "COMPRAS - ")
    resumo_limpo = re.sub(r"^[A-Z]+\s*-\s*", "", resumo).strip()
    palavras = resumo_limpo.split()
    for palavra in palavras:
        token = re.sub(r"[^\w]", "", palavra).lower()
        if token and token not in _STOPWORDS and len(token) > 3:
            return token
    # Fallback: retorna a primeira palavra do resumo limpo, sem filtros
    return palavras[0] if palavras else resumo[:20]


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


def buscar_issues_similares(resumo: str, projeto_key: str, glpi_id: str = None) -> list:
    """
    Busca issues parecidas no Jira via JQL para evitar duplicidade.
    Usa método GET seguro com URL Encoding.

    Filtra os resultados brutos da JQL pela similaridade textual entre o resumo
    atual e o resumo de cada issue retornada (SequenceMatcher >= 0.75). Quando a
    demanda possui um ID do GLPI, a JQL também busca por esse ID nos campos de
    texto do Jira; uma correspondência exata pelo ID é considerada duplicata
    confirmada, ignorando o filtro de similaridade.
    """
    try:
        if not resumo:
            return []

        # Pega a primeira palavra útil do resumo gerado pela IA (maior que 4 letras)
        palavras = resumo.split()
        if not palavras:
            return []
        palavras_uteis = [p for p in palavras if len(p) > 4]
        palavra_chave = palavras_uteis[0] if palavras_uteis else palavras[0]

        url = f"{JIRA_URL}/rest/api/3/search/jql"
        jql_query = f'project = "{projeto_key}" AND summary ~ "{palavra_chave}"'
        if glpi_id:
            jql_query = f'project = "{projeto_key}" AND (summary ~ "{palavra_chave}" OR text ~ "{glpi_id}")'

        auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_TOKEN)
        headers = {"Accept": "application/json"}
        params = {
            "jql": jql_query,
            "maxResults": 3,
            "fields": "summary"
        }

        response = requests.get(url, headers=headers, params=params, auth=auth, timeout=10)
        if response.status_code == 200:
            issues = response.json().get("issues", [])
            resultados = []
            for issue in issues:
                resumo_jira = issue["fields"].get("summary", "")
                # Correspondência exata pelo ID do GLPI é duplicata confirmada, sem precisar do filtro de similaridade
                eh_correspondencia_glpi = bool(glpi_id) and glpi_id in resumo_jira
                similaridade = SequenceMatcher(None, resumo.lower(), resumo_jira.lower()).ratio()
                if eh_correspondencia_glpi or similaridade >= _LIMIAR_SIMILARIDADE:
                    resultados.append({
                        "key": issue["key"],
                        "resumo": resumo_jira,
                        "link": f"{JIRA_URL}/browse/{issue['key']}"
                    })
            return resultados
        else:
            # Erro HTTP da API do Jira — log silencioso, fluxo principal não é interrompido
            print(f"[ANTI-DUPLICIDADE] Erro HTTP {response.status_code} retornado pelo Jira.")
            return []
    except requests.exceptions.Timeout:
        print("[ANTI-DUPLICIDADE] Timeout na conexão com o Jira. Checagem de duplicidade ignorada.")
        return []
    except requests.exceptions.ConnectionError:
        print("[ANTI-DUPLICIDADE] Falha de conexão com o Jira. Checagem de duplicidade ignorada.")
        return []
    except Exception as e:
        print(f"[ANTI-DUPLICIDADE] Erro inesperado ao consultar o Jira: {e}")
        return []


def buscar_usuarios_responsaveis(project_key: str) -> list:
    """
    Busca, via /rest/api/3/user/assignable/search, os usuários ativos que podem
    ser atribuídos como responsáveis no projeto informado. Retorna uma lista de
    dicionários com 'displayName' e 'accountId'.
    """
    try:
        url = f"{JIRA_URL}/rest/api/3/user/assignable/search"
        auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_TOKEN)
        headers = {"Accept": "application/json"}
        params = {"project": project_key, "maxResults": 50}

        response = requests.get(url, headers=headers, params=params, auth=auth, timeout=10)
        if response.status_code == 200:
            usuarios = response.json()
            return [
                {"displayName": usuario.get("displayName"), "accountId": usuario.get("accountId")}
                for usuario in usuarios
                if usuario.get("active", True)
            ]
        print(f"[RESPONSAVEL] Erro HTTP {response.status_code} ao buscar usuários atribuíveis.")
        return []
    except requests.exceptions.Timeout:
        print("[RESPONSAVEL] Timeout na conexão com o Jira. Busca de responsáveis ignorada.")
        return []
    except requests.exceptions.ConnectionError:
        print("[RESPONSAVEL] Falha de conexão com o Jira. Busca de responsáveis ignorada.")
        return []
    except Exception as e:
        print(f"[RESPONSAVEL] Erro inesperado ao buscar usuários atribuíveis: {e}")
        return []


def buscar_opcoes_terceiros(project_key: str = None) -> dict:
    """
    Busca as opções válidas (allowedValues) do campo customizado "Terceiros" via
    createmeta. Como o ID exato do campo pode variar entre instâncias do Jira,
    a busca é genérica: percorre todos os campos do tipo de issue retornados
    para o projeto e seleciona aquele cujo nome contenha "terceiro".

    Retorna um dicionário no formato {"field_id": str|None, "opcoes": list},
    onde cada opção possui 'id' e 'value'.
    """
    try:
        project_key = project_key or PROJETO_KEY
        url = f"{JIRA_URL}/rest/api/3/issue/createmeta"
        auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_TOKEN)
        headers = {"Accept": "application/json"}
        params = {"projectKeys": project_key, "expand": "projects.issuetypes.fields"}

        response = requests.get(url, headers=headers, params=params, auth=auth, timeout=10)
        if response.status_code != 200:
            print(f"[TERCEIROS] Erro HTTP {response.status_code} ao buscar createmeta.")
            return {"field_id": None, "opcoes": []}

        dados = response.json()
        for projeto in dados.get("projects", []):
            for issuetype in projeto.get("issuetypes", []):
                campos = issuetype.get("fields", {})
                for field_id, field_info in campos.items():
                    nome_campo = (field_info.get("name") or "").lower()
                    if "terceiro" in nome_campo:
                        opcoes = [
                            {"id": valor.get("id"), "value": valor.get("value") or valor.get("name")}
                            for valor in field_info.get("allowedValues", [])
                        ]
                        return {"field_id": field_id, "opcoes": opcoes}
        return {"field_id": None, "opcoes": []}
    except requests.exceptions.Timeout:
        print("[TERCEIROS] Timeout na conexão com o Jira. Busca de opções ignorada.")
        return {"field_id": None, "opcoes": []}
    except requests.exceptions.ConnectionError:
        print("[TERCEIROS] Falha de conexão com o Jira. Busca de opções ignorada.")
        return {"field_id": None, "opcoes": []}
    except Exception as e:
        print(f"[TERCEIROS] Erro inesperado ao buscar opções: {e}")
        return {"field_id": None, "opcoes": []}