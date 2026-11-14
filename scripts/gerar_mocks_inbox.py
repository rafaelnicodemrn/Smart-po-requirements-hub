# scripts/gerar_mocks_inbox.py
"""
Script utilitário para popular a tabela inbox_demandas do hub_database.db
com cenários de teste, simulando e-mails recebidos pela inbox do Hub do PO.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import _get_connection, inicializar_banco

MOCKS = [
    {
        "linha": 1001,
        "assunto": "URGENTE: PDV não emite NFCe na loja Centro",
        "corpo": (
            "Bom dia, o PDV 3 da loja Centro está travando toda vez que tentamos "
            "finalizar uma venda. O sistema fecha o cupom mas a NFCe não é emitida "
            "e o cliente fica sem o documento fiscal. Isso já aconteceu com pelo "
            "menos 5 clientes hoje pela manhã. Precisamos de uma correção urgente "
            "pois estamos parados para vendas fiscais."
        ),
    },
    {
        "linha": 1002,
        "assunto": "sugestao",
        "corpo": (
            "Oi, queria pedir um botão novo no sistema de RH, sei que parece "
            "bobeira mas ia ajudar muito a gente aqui. Tipo, quando a gente "
            "precisa lançar um afastamento, hoje tem que entrar em três telas "
            "diferentes. Será que dava pra ter um botão direto na tela inicial "
            "pra isso? Obrigado!"
        ),
    },
    {
        "linha": 1003,
        "assunto": "[GLPI #999999] Solicitação de liberação de acesso",
        "corpo": (
            "Chamado GLPI #999999\n\n"
            "Solicitante: Maria Souza - Departamento Financeiro\n"
            "Tipo de solicitação: Liberação de acesso\n\n"
            "Descrição: Solicito liberação de acesso ao módulo de Contas a Pagar "
            "no sistema ERP para o usuário maria.souza, com perfil de consulta e "
            "lançamento. Acesso necessário a partir de segunda-feira para início "
            "das atividades no setor."
        ),
    },
    {
        "linha": 1004,
        "assunto": "Erro na integração de cartões - mesmo problema de ontem",
        "corpo": (
            "Pessoal, está acontecendo de novo o mesmo erro de integração de "
            "cartões que reportamos ontem. As vendas com cartão de crédito não "
            "estão sendo conciliadas com a adquirente, e o status fica pendente "
            "indefinidamente no painel financeiro. Por favor verificar pois é o "
            "mesmo comportamento do chamado de ontem."
        ),
    },
]


def gerar_mocks() -> None:
    """Insere os 4 cenários de teste na tabela inbox_demandas com status 'Pendente'."""
    inicializar_banco()
    with _get_connection() as conn:
        cursor = conn.cursor()
        for mock in MOCKS:
            cursor.execute(
                "INSERT INTO inbox_demandas (linha, assunto, corpo, status) VALUES (?, ?, ?, 'Pendente')",
                (mock["linha"], mock["assunto"], mock["corpo"]),
            )
        conn.commit()


if __name__ == "__main__":
    gerar_mocks()
    print("Mocks inseridos com sucesso no banco de dados local!")
