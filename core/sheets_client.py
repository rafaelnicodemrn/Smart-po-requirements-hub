# core/sheets_client.py
import os
import gspread
from google.oauth2 import service_account
from typing import List, Dict

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_PATH = os.path.join(ROOT_DIR, ".streamlit", "google_credentials.json")

def buscar_novos_emails_planilha(sheet_key: str) -> List[Dict[str, str]]:
    """
    Lê a aba ativa de uma planilha Google buscando linhas onde Coluna A (Assunto)
    e Coluna B (Corpo) tenham texto, mas Coluna C (Status) esteja vazia.
    Escreve 'Importado para o Hub' na Coluna C destas linhas e as retorna.
    """
    if not os.path.exists(CREDENTIALS_PATH):
        raise FileNotFoundError(
            f"⚠️ Arquivo de credenciais do Google ausente em: {CREDENTIALS_PATH}. "
            "Por favor, configure o arquivo de credenciais da conta de serviço do Google."
        )

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=scopes
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_key)
    worksheet = sheet.sheet1  # Obtém a aba primária/ativa

    rows = worksheet.get_all_values()
    novas_demandas = []

    for i, row in enumerate(rows):
        row_num = i + 1  # 1-indexed para gspread

        # Pula cabeçalho típico se for o caso
        if row_num == 1 and len(row) >= 2:
            val_a = row[0].strip().lower()
            val_b = row[1].strip().lower()
            if val_a in ["assunto", "subject", "title", "titulo"] or val_b in ["corpo", "body", "mensagem", "descrição", "descricao"]:
                continue

        # Garante que tenha ao menos coluna A e B
        if len(row) < 2:
            continue

        assunto = row[0].strip()
        corpo = row[1].strip()
        status = row[2].strip() if len(row) >= 3 else ""

        # Deve ter Assunto e Corpo, mas Status deve ser VAZIO
        if assunto and corpo and not status:
            novas_demandas.append({
                "row_num": row_num,
                "assunto": assunto,
                "corpo": corpo
            })

    result = []
    # Atualiza as linhas identificadas
    for d in novas_demandas:
        worksheet.update_cell(d["row_num"], 3, "Importado para o Hub")
        result.append({
            "assunto": d["assunto"],
            "corpo": d["corpo"]
        })

    return result
