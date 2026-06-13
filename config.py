# config.py
import os
import streamlit as st

def _get_secret(section: str, key: str) -> str:
    """
    Busca o segredo nas variáveis de ambiente (Prod) ou no st.secrets (Dev Local).
    Garante o princípio do menor privilégio, centralizando o acesso.
    """
    env_key = f"{section.upper()}_{key.upper()}"
    
    # 1. Tenta buscar da variável de ambiente do Sistema Operacional/Nuvem
    if env_key in os.environ:
        return os.environ[env_key]
    
    # 2. Fallback para o arquivo local .streamlit/secrets.toml
    try:
        return st.secrets[section][key]
    except KeyError:
        raise ValueError(f"⚠️ Segredo crítico ausente: [{section}] {key}. Verifique seu secrets.toml ou variáveis de ambiente.")

# Exportação das Constantes Imutáveis
JIRA_URL = _get_secret("jira", "url")
JIRA_EMAIL = _get_secret("jira", "email")
JIRA_TOKEN = _get_secret("jira", "api_token")
RELATOR_ACCOUNT_ID = _get_secret("jira", "relator_account_id")

GEMINI_API_KEY = _get_secret("gemini", "api_key")

PROJETO_KEY = _get_secret("projeto", "key")