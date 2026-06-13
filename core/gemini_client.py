# core/gemini_client.py
import requests
import json
from config import GEMINI_API_KEY
from core.prompts import PROMPT_DE_OURO, SCHEMA_GEMINI
from core.models import Demanda, TipoTicket

def analisar_demanda(texto_entrada: str, regras_adicionais: str = "") -> Demanda:
    """
    Envia a demanda para o Gemini atuando sob a Persona do PO e retorna o objeto Demanda tipado.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # Injeta a instrução de sistema (O Prompt de Ouro) separada do texto do usuário
    system_instruction = PROMPT_DE_OURO
    if regras_adicionais:
        system_instruction += f"\n\nRegras Dinâmicas de Contexto:\n{regras_adicionais}"

    payload = {
        "system_instruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"role": "user", "parts": [{"text": f"Analise esta demanda e estruture-a rigorosamente:\n\n{texto_entrada}"}]}],
        "generationConfig": {
            "temperature": 0.2, # Temperatura baixa para garantir que siga regras de negócio sem alucinar
            "responseMimeType": "application/json",
            "responseSchema": SCHEMA_GEMINI
        }
    }

    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=60)
        if response.status_code == 200:
            resultado_json = json.loads(response.json()['candidates'][0]['content']['parts'][0]['text'])
            
            # Converte o dicionário retornado no objeto Demanda canônico
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
        else:
            print(f"[ERRO GEMINI] Status: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"[FALHA DE CONEXÃO GEMINI]: {e}")
        return None