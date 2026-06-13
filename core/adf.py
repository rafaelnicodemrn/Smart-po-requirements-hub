# core/adf.py
from core.models import Demanda, TipoTicket

def _criar_paragrafo(texto: str) -> dict:
    return {
        "type": "paragraph",
        "content": [{"type": "text", "text": texto}]
    }

def _criar_titulo(texto: str, nivel: int = 2) -> dict:
    return {
        "type": "heading",
        "attrs": {"level": nivel},
        "content": [{"type": "text", "text": texto}]
    }

def construir_descricao_adf(demanda: Demanda) -> dict:
    """
    Converte os dados da Dataclass Demanda para o Atlassian Document Format (ADF).
    """
    conteudo = []

    # 1. BUGS (Produção ou Squad) - Foco em texto livre estruturado
    if demanda.tipo in [TipoTicket.BUG_PRODUCAO, TipoTicket.BUG_SQUAD]:
        conteudo.append(_criar_titulo("Descrição do Problema", 2))
        if demanda.descricao_livre:
            conteudo.append(_criar_paragrafo(demanda.descricao_livre))
            
    # 2. HISTÓRIAS E MANUTENÇÕES - Foco em Requisitos
    else:
        if demanda.objetivo:
            conteudo.append(_criar_titulo("Objetivo", 2))
            conteudo.append(_criar_paragrafo(demanda.objetivo))
            
        if demanda.user_story:
            conteudo.append(_criar_titulo("User Story", 2))
            historia = f"EU COMO: {demanda.user_story.get('eu_como', '')}\n" \
                       f"QUERO: {demanda.user_story.get('quero', '')}\n" \
                       f"PARA: {demanda.user_story.get('para', '')}"
            conteudo.append(_criar_paragrafo(historia))
            
        if demanda.criterios_aceite:
            conteudo.append(_criar_titulo("Critérios de Aceite", 2))
            # Cria lista numerada em ADF
            itens_lista = []
            for criterio in demanda.criterios_aceite:
                itens_lista.append({
                    "type": "listItem",
                    "content": [_criar_paragrafo(criterio)]
                })
            conteudo.append({"type": "orderedList", "content": itens_lista})
            
        if demanda.cenarios_teste:
            conteudo.append(_criar_titulo("Cenários de Teste (BDD)", 2))
            for i, cenario in enumerate(demanda.cenarios_teste, 1):
                bdd_text = f"Cenário {i}:\nDADO QUE {cenario.get('dado', '')}\nQUANDO {cenario.get('quando', '')}\nENTÃO {cenario.get('entao', '')}"
                conteudo.append(_criar_paragrafo(bdd_text))

        if demanda.ambiente:
            conteudo.append(_criar_titulo("Ambiente (Valor Entregue)", 2))
            itens_ambiente = []
            for amb in demanda.ambiente:
                titulo = amb.get('titulo', '')
                desc = amb.get('descricao', '')
                itens_ambiente.append({
                    "type": "listItem",
                    "content": [_criar_paragrafo(f"**{titulo}**: {desc}")]
                })
            conteudo.append({"type": "bulletList", "content": itens_ambiente})

    # Link GLPI padronizado ao final
    if demanda.glpi_url:
        conteudo.append({"type": "rule"}) # Linha divisória
        conteudo.append(_criar_paragrafo(f"🔗 Origem GLPI: {demanda.glpi_url}"))

    return {
        "version": 1,
        "type": "doc",
        "content": conteudo
    }