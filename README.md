# Smart PO Requirements Hub: Intelligent Ingestion and Governance Ecosystem

Plataforma corporativa de governança ágil e engenharia de requisitos sob a arquitetura Human-in-the-Loop (HITL), projetada para centralização, tratamento e ingestão automatizada de fluxos de demandas em ecossistemas corporativos.

## Características de Arquitetura

* **Sanitização Contextual de Linguagem Natural**: Consumo de modelos de Large Language Models (LLMs) via schemas de validação rígidos (`Pydantic`) para converter descrições livres de negócios ou e-mails brutos em especificações técnicas formais (User Stories, Critérios de Aceite e BDD/Gherkin).
* **Conformidade de Payload Atlassian**: Abstração lógica e parser nativo estruturado para compilação e tradução das histórias em payloads complexos baseados em Atlassian Document Format (ADF), injetando dados via API v3 do Jira Cloud.
* **Mecanismo de Auditoria Gerencial**: Scripts utilitários acoplados para tracking analítico em tempo real via JQL (Jira Query Language), executando rotinas automáticas de encerramento de Sprints e limpeza semântica de Épicos órfãos.

## Configuração de Desenvolvimento Local

Para executar a aplicação localmente garantindo o isolamento absoluto de credenciais:

1. Crie o diretório `.streamlit/` na raiz do projeto.
2. Configure o arquivo `secrets.toml` seguindo o padrão de chaves mapeadas no módulo `config.py`.
3. Inicie o servidor local:

```bash
pip install -r requirements.txt
streamlit run app.py