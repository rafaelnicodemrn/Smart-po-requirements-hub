# core/gemini_client.py
import requests
import json
from config import GEMINI_API_KEY, GEMINI_API_KEY_BACKUP, GEMINI_MODEL_BACKUP
from core.prompts import PROMPT_DE_OURO, SCHEMA_GEMINI
from core.models import Demanda, TipoTicket

_MODELO_PRINCIPAL = "gemini-2.5-flash"


def _demanda_fallback_segura() -> Demanda:
    """
    Retorna uma instância de Demanda com avisos textuais fixos quando todas as
    tentativas da esteira de redundância falham. Garante que a tela do Streamlit
    nunca quebre e os campos fiquem livres para edição manual.
    """
    aviso = "Serviço temporariamente indisponível. Por favor, revise e ajuste os detalhes manualmente."
    return Demanda(
        tipo=TipoTicket.HISTORIA,
        resumo="VAREJO - Serviço Temporariamente Indisponível",
        area_negocios="Varejo",
        prioridade="Média",
        descricao_livre=aviso,
        objetivo=aviso,
        user_story={"eu_como": "usuário", "quero": "preencher manualmente", "para": "criar o ticket corretamente"},
        criterios_aceite=[aviso],
        cenarios_teste=[{
            "dado": "Serviço de IA indisponível",
            "quando": "todas as tentativas da esteira de redundância falham",
            "entao": "preencha os campos manualmente antes de criar o ticket"
        }],
        ambiente=[{"titulo": "Aviso de Sistema", "descricao": aviso}]
    )


def _chamar_api_gemini(api_key: str, modelo: str, payload: dict) -> dict:
    """
    Executa uma única chamada HTTP à API do Gemini e retorna o dicionário de resultado.
    Lança HTTPError para qualquer status de erro (4xx/5xx) ou exceção de conexão.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
    response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=60)
    response.raise_for_status()
    return json.loads(response.json()['candidates'][0]['content']['parts'][0]['text'])


def analisar_demanda(texto_entrada: str, regras_adicionais: str = "", imagens: list = None) -> Demanda:
    """
    Envia a demanda para o Gemini atuando sob a Persona do PO e retorna o objeto Demanda tipado.
    Implementa esteira de redundância em cascata com três tentativas antes de acionar o fallback seguro:

      Tentativa 1 → Chave primária  + modelo padrão  (gemini-2.5-flash)
      Tentativa 2 → Chave backup    + modelo padrão  (gemini-2.5-flash)
      Tentativa 3 → Chave disponível + modelo backup (gemini-1.5-pro)
      Fallback    → Objeto Demanda com avisos, sem quebrar a interface.

    Parâmetros:
        texto_entrada:     Descrição textual da demanda em linguagem natural.
        regras_adicionais: Contexto dinâmico injetado ao final do system_instruction.
        imagens:           Lista opcional de objetos multimodais no formato Gemini:
                           [{"inline_data": {"mime_type": "image/png", "data": "<base64>"}}]
    """
    system_instruction = PROMPT_DE_OURO
    if regras_adicionais:
        system_instruction += f"\n\nRegras Dinâmicas de Contexto:\n{regras_adicionais}"

    parts_usuario = [{"text": f"Analise esta demanda e estruture-a rigorosamente:\n\n{texto_entrada}"}]
    if imagens:
        parts_usuario.extend(imagens)

    payload = {
        "system_instruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"role": "user", "parts": parts_usuario}],
        "generationConfig": {
            "temperature": 0.2,  # Temperatura baixa para garantir que siga regras de negócio sem alucinar
            "responseMimeType": "application/json",
            "responseSchema": SCHEMA_GEMINI
        }
    }

    # Chave de contingência: usa a backup se configurada; caso contrário reutiliza a primária
    chave_contingencia = GEMINI_API_KEY_BACKUP if GEMINI_API_KEY_BACKUP else GEMINI_API_KEY

    tentativas = [
        (GEMINI_API_KEY,        _MODELO_PRINCIPAL,  "Tentativa 1: chave primária + modelo padrão"),
        (GEMINI_API_KEY_BACKUP, _MODELO_PRINCIPAL,  "Tentativa 2: chave backup + modelo padrão"),
        (chave_contingencia,    GEMINI_MODEL_BACKUP, "Tentativa 3: modelo de contingência"),
    ]

    ultimo_erro = None
    for api_key, modelo, descricao in tentativas:
        if not api_key:
            print(f"[GEMINI FAILOVER] {descricao} ignorada — chave de API não configurada.")
            continue
        try:
            print(f"[GEMINI FAILOVER] Executando {descricao}...")
            resultado_json = _chamar_api_gemini(api_key, modelo, payload)
            return Demanda(
                tipo=TipoTicket(resultado_json.get("tipo", "História")),
                resumo=resultado_json.get("resumo", "SEM RESUMO"),
                area_negocios=resultado_json.get("area_negocios", "Varejo"),
                prioridade=resultado_json.get("prioridade", "Média"),
                descricao_livre=resultado_json.get("descricao_livre"),
                objetivo=resultado_json.get("objetivo"),
                user_story=resultado_json.get("user_story"),
                criterios_aceite=resultado_json.get("criterios_aceite", []),
                cenarios_teste=resultado_json.get("cenarios_teste", []),
                ambiente=resultado_json.get("ambiente", [])
            )
        except Exception as e:
            print(f"[GEMINI FAILOVER] {descricao} falhou: {e}")
            ultimo_erro = e

    # Nenhuma das tentativas foi bem-sucedida — aciona o fallback seguro
    print(f"[GEMINI FAILOVER] Todas as tentativas de API falharam. Último erro: {ultimo_erro}. Acionando fallback seguro.")
    return _demanda_fallback_segura()
