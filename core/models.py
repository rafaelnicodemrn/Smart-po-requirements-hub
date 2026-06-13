# core/models.py
from dataclasses import dataclass, field
from typing import Optional, Literal
from enum import Enum

class TipoTicket(str, Enum):
    BUG_PRODUCAO = "Bug - Produção"
    BUG_SQUAD    = "Bug - Squad"
    MANUTENCAO   = "Pequenas Manutenções"
    HISTORIA     = "História"

# Mapeamento técnico para tradução das regras de negócio exigidas pelo PRD
# Define qual IssueType exato da API do Jira e quais labels injetar silenciosamente
ROTEAMENTO_JIRA = {
    TipoTicket.BUG_PRODUCAO: {"issuetype": "Bug", "labels": ["bug-producao"]},
    TipoTicket.BUG_SQUAD:    {"issuetype": "Bug", "labels": ["squad-interno"]},
    TipoTicket.MANUTENCAO:   {"issuetype": "Task", "labels": ["pequena-manutencao"]},
    TipoTicket.HISTORIA:     {"issuetype": "Story", "labels": []},
}

Prioridade = Literal["Muito Baixa", "Baixa", "Média", "Alta", "Muito Alta", "Crítica"]
AreaNegocios = Literal["Varejo", "Compras"]

@dataclass
class Demanda:
    """
    Contrato de dados unificado do Hub do PO. 
    Reflete as regras granulares exigidas para o projeto CEV da Lar Cooperativa.
    """
    # Campos Base Obrigatórios
    tipo: TipoTicket
    resumo: str  # Limite de 50-70 chars, iniciando com módulo/área (Ex: 'VAREJO - ')
    area_negocios: AreaNegocios
    prioridade: Prioridade
    
    # Campos de Estruturação Dinâmica (Preenchidos conforme o Tipo do Ticket)
    descricao_livre: Optional[str] = None      # Usado primariamente para Bugs
    objetivo: Optional[str] = None             # Usado em História / Manutenção
    user_story: Optional[dict] = None          # Formato: {"eu_como": "", "quero": "", "para": ""}
    criterios_aceite: list[str] = field(default_factory=list)
    cenarios_teste: list[dict] = field(default_factory=list) # Gherkin: {"dado": "", "quando": "", "entao": ""}
    ambiente: list[dict] = field(default_factory=list)       # Valor entregue: {"titulo": "", "descricao": ""}
    
    # Campos de Rastreabilidade e Governança
    origem: Literal["inbox_glpi", "criacao_manual"] = "criacao_manual"
    glpi_url: Optional[str] = None
    pai_key: Optional[str] = None              # Chave do Épico Pai (ex: CEV-1024). Substitui o 'Epic Link' deprecado.
    anexos_capturados: list[dict] = field(default_factory=list) # Payload multimodal para o Gemini