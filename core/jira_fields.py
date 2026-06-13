# core/jira_fields.py
from core.models import Demanda, ROTEAMENTO_JIRA
from core.adf import construir_descricao_adf
from config import PROJETO_KEY, RELATOR_ACCOUNT_ID

# IDs Reais Descobertos no seu Jira
CAMPOS = {
    "area_negocios": "customfield_10118",
    "glpi_id": "customfield_10047"
    # 'Ambiente' será injetado diretamente na Descrição (ADF).
    # 'Epic Link' (10014) está deprecado pela Atlassian, usaremos o campo nativo 'parent'.
}

def montar_payload(demanda: Demanda) -> dict:
    """
    Transforma a Dataclass Demanda no Payload JSON exato que a API v3 do Jira exige.
    """
    rota = ROTEAMENTO_JIRA[demanda.tipo]
    
    fields = {
        "project": {"key": PROJETO_KEY},
        "summary": demanda.resumo[:70],  # Garante o limite de 70 caracteres
        "issuetype": {"name": rota["issuetype"]},
        "description": construir_descricao_adf(demanda),
        "reporter": {"id": RELATOR_ACCOUNT_ID}, # Exigência GDPR da Atlassian (accountId)
        "priority": {"name": demanda.prioridade},
        "labels": rota["labels"]
    }

    # 1. Tratamento de Área de Negócios (Campo do tipo Select/Lista)
    if demanda.area_negocios:
        fields[CAMPOS["area_negocios"]] = {"value": demanda.area_negocios}

    # 2. Tratamento de GLPI ID (Campo do tipo texto ou URL)
    if demanda.glpi_url:
        fields[CAMPOS["glpi_id"]] = demanda.glpi_url

    # 3. Tratamento de Vínculo com Épico Pai (Usando 'parent')
    if demanda.pai_key:
        fields["parent"] = {"key": demanda.pai_key}

    return {"fields": fields}