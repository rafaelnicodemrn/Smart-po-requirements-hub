# 📋 Smart PO Requirements Hub

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Gemini](https://img.shields.io/badge/Google-Gemini-4285F4?logo=googlegemini&logoColor=white)
![Jira](https://img.shields.io/badge/Jira%20Cloud-API%20v3-0052CC?logo=jira&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?logo=pydantic&logoColor=white)

Hub de governança ágil e engenharia de requisitos para Product Owners, com **Human-in-the-Loop**: transforma e-mails e descrições livres de negócio em histórias de usuário estruturadas e as cria no Jira, depois da revisão humana.

## ✨ Funcionalidades

- **IA para requisitos:** o Gemini converte texto livre ou e-mail bruto em User Story, critérios de aceite e cenários BDD/Gherkin, com saída validada por schema (`Pydantic`).
- **Resiliência de IA:** chave de backup e modelo de contingência quando a primeira tentativa falha.
- **Jira Cloud (API v3):** conversão para **ADF** (Atlassian Document Format), roteamento por tipo de ticket (Bug Produção, Bug Squad, Pequenas Manutenções, História), labels e campos customizados.
- **Caixa de entrada automática:** um *watcher* consulta uma planilha Google (via Apps Script) a cada 5 minutos, grava as demandas num SQLite local e marca a linha como processada.
- **Auditoria gerencial:** utilitários JQL para acompanhamento, encerramento de sprints e limpeza de épicos órfãos.

## 🧭 Fluxo

```
E-mail ─► Planilha Google ─► Apps Script ─► Inbox Watcher ─► SQLite ─┐
                                                                      ▼
                        Texto livre ─────────────────────────► Streamlit (PO revisa)
                                                                      │  Gemini
                                                                      ▼
                                                           Jira Cloud (ADF, API v3)
```

## 🛠️ Stack

Python 3.11+ · Streamlit · Google Gemini · Jira Cloud REST API v3 · Pydantic · SQLite · gspread · pandas · python-docx

## 📁 Estrutura

```
├── app.py                  # interface Streamlit
├── config.py               # segredos (variáveis de ambiente ou st.secrets)
├── core/
│   ├── models.py           # dataclass Demanda e roteamento Jira
│   ├── prompts.py          # prompts da IA
│   ├── gemini_client.py    # chamadas ao Gemini com fallback
│   ├── jira_client.py      # integração com o Jira
│   ├── jira_fields.py      # campos customizados
│   ├── adf.py              # conversor para Atlassian Document Format
│   ├── database.py         # persistência SQLite
│   ├── inbox_watcher.py    # polling da planilha/Apps Script
│   └── sheets_client.py    # acesso à planilha Google
├── scripts/gerar_mocks_inbox.py
├── start_all.bat           # sobe watcher e interface (Windows)
└── requirements.txt
```

## 🚀 Como executar

```bash
python -m venv venv
venv\Scripts\activate          # Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
```

Crie `.streamlit/secrets.toml` com as chaves mapeadas em [`config.py`](config.py) (Jira, Gemini, planilha Google e URL do Apps Script). Para a caixa de entrada, coloque também a credencial da conta de serviço em `.streamlit/google_credentials.json`.

```bash
streamlit run app.py           # só a interface
.\start_all.bat                # interface + inbox watcher (Windows)
```

> 🔒 `secrets.toml`, `google_credentials.json` e `hub_database.db*` ficam no `.gitignore`. Nunca os versione.
