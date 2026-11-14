# core/jira_fields.py
from core.models import Demanda, ROTEAMENTO_JIRA
from core.adf import construir_descricao_adf
from config import PROJETO_KEY

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
        # Campo 'reporter' omitido propositalmente: a API do Jira Cloud usa
        # automaticamente o accountId do usuário autenticado, evitando o erro
        # "Especifique algum valor válido para reporter".
        "priority": {"name": demanda.prioridade}
        # Campo de Categoria/Labels omitido propositalmente: não deve ser
        # preenchido automaticamente, ficando vazio/padrão no Jira Cloud.
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

    # 4. Tratamento de Responsável (assignee), apenas se selecionado
    if demanda.responsavel_account_id:
        fields["assignee"] = {"accountId": demanda.responsavel_account_id}

    # 5. Tratamento de Terceiros (campo customizado), apenas se selecionado
    if demanda.terceiros_field_id and demanda.terceiros_opcao:
        opcao_id = demanda.terceiros_opcao.get("id")
        if opcao_id:
            fields[demanda.terceiros_field_id] = {"id": opcao_id}
        else:
            fields[demanda.terceiros_field_id] = {"value": demanda.terceiros_opcao.get("value")}

    return {"fields": fields}