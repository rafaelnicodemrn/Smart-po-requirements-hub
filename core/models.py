# core/models.py
from dataclasses import dataclass, field
from typing import Optional, Literal, List, Dict
from enum import Enum

class TipoTicket(str, Enum):
    BUG_PRODUCAO = "Bug - Produção"
    BUG_SQUAD    = "Bug - Squad"
    MANUTENCAO   = "Pequenas Manutenções"
    HISTORIA     = "História"

ROTEAMENTO_JIRA = {
    TipoTicket.BUG_PRODUCAO: {"issuetype": "Bug",   "labels": ["bug-producao"]},
    TipoTicket.BUG_SQUAD:    {"issuetype": "Bug",   "labels": ["squad-interno"]},
    TipoTicket.MANUTENCAO:   {"issuetype": "Task",  "labels": ["pequena-manutencao"]},
    TipoTicket.HISTORIA:     {"issuetype": "Story", "labels": []},
}

Prioridade    = Literal["Muito Baixa", "Baixa", "Média", "Alta", "Muito Alta", "Crítica"]
AreaNegocios  = Literal["Varejo", "Compras"]

@dataclass
class Demanda:
    tipo:           TipoTicket
    resumo:         str
    area_negocios:  AreaNegocios
    prioridade:     Prioridade
    
    descricao_livre:  Optional[str]  = None
    objetivo:         Optional[str]  = None
    user_story:       Optional[dict] = None
    # Alterado para List e Dict maiúsculos para suportar Python 3.8
    criterios_aceite: List[str]      = field(default_factory=list)
    cenarios_teste:   List[Dict]     = field(default_factory=list)
    ambiente:         List[Dict]     = field(default_factory=list)
    
    origem:             Literal["inbox_glpi", "criacao_manual"] = "criacao_manual"
    glpi_url:           Optional[str]  = None
    pai_key:            Optional[str]  = None
    anexos_capturados:  List[Dict]     = field(default_factory=list)

    # Responsável (assignee) selecionado dinamicamente a partir da API do Jira
    responsavel_account_id:  Optional[str]  = None
    # Opção do campo customizado "Terceiros", buscada dinamicamente via createmeta
    terceiros_field_id:      Optional[str]  = None
    terceiros_opcao:         Optional[Dict] = None