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
    except Exception:
        try:
            import tomllib
            # config.py está na raiz, então o caminho relativo para .streamlit/secrets.toml é correto
            base_dir = os.path.dirname(os.path.abspath(__file__))
            secrets_path = os.path.join(base_dir, ".streamlit", "secrets.toml")
            if os.path.exists(secrets_path):
                with open(secrets_path, "rb") as f:
                    data = tomllib.load(f)
                    return data[section][key]
            raise KeyError()
        except KeyError:
            raise ValueError(f"⚠️ Segredo crítico ausente: [{section}] {key}. Verifique seu secrets.toml ou variáveis de ambiente.")
        except Exception as e:
            raise ValueError(f"⚠️ Segredo crítico ausente: [{section}] {key}. Erro ao ler secrets.toml de forma independente: {e}")

# Exportação das Constantes Imutáveis
JIRA_URL = _get_secret("jira", "url")
JIRA_EMAIL = _get_secret("jira", "email")
JIRA_TOKEN = _get_secret("jira", "api_token")
RELATOR_ACCOUNT_ID = _get_secret("jira", "relator_account_id")

GEMINI_API_KEY = _get_secret("gemini", "api_key")

# Esteira de redundância: chave e modelo de contingência para o cliente da IA.
# A chave backup é opcional — se ausente, as tentativas que a usam são puladas.
try:
    GEMINI_API_KEY_BACKUP = _get_secret("gemini", "api_key_backup")
except ValueError:
    GEMINI_API_KEY_BACKUP = os.environ.get("GEMINI_API_KEY_BACKUP", "")
GEMINI_MODEL_BACKUP = "gemini-1.5-pro"

PROJETO_KEY = _get_secret("projeto", "key")

GOOGLE_SHEET_KEY = _get_secret("google", "sheet_key")

# URL do Web App publicado no Google Apps Script (modelo de Outbound Polling).
# O antivírus corporativo bloqueia túneis (Ngrok/FastAPI), então o Hub passa a
# buscar/atualizar a planilha via requisições HTTP nativas para este endpoint.
# Preenchido manualmente pelo PO após publicar o Apps Script como Web App.
APPS_SCRIPT_WEB_APP_URL = "https://script.google.com/macros/s/AKfycbw2ZOsz_nkKDPgFHZR_5lyrcDf1QYQ4x2o4530yik8_51EyukqxS0InJpljZHAORb-w/exec"