# app.py
import streamlit as st
import json
import re
import base64
import docx
import pandas as pd
from config import JIRA_URL, PROJETO_KEY
# Otimização via Facade do pacote core
from core import (
    Demanda,
    TipoTicket,
    AreaNegocios,
    Prioridade,
    analisar_demanda,
    montar_payload,
    criar_issue,
    buscar_issues_similares,
    buscar_usuarios_responsaveis,
    buscar_opcoes_terceiros,
    inicializar_banco,
    listar_pendentes,
    marcar_como_processado
)

# Texto padrão exibido no topo das listas de Responsável e Terceiros quando nada é selecionado
_OPCAO_EM_BRANCO = "Não Atribuir / Em Branco"

st.set_page_config(page_title="Hub do PO", page_icon="🎯", layout="wide")

# Inicializa o banco de dados embutido SQLite
inicializar_banco()

# Regex que captura o número do chamado na tag padrão usada nos assuntos vindos do GLPI, ex: "[GLPI #0527513]"
_REGEX_TAG_GLPI = re.compile(r"\[GLPI\s*#?\s*0*(\d+)\]", re.IGNORECASE)

def extrair_id_glpi(texto: str) -> str:
    """Extrai apenas os números da tag do GLPI (sem zeros à esquerda). Retorna string vazia se não encontrar."""
    if not texto:
        return ""
    match = _REGEX_TAG_GLPI.search(texto)
    return match.group(1) if match else ""

def extrair_link_glpi(texto: str) -> str:
    """
    Identifica a tag do GLPI (ex: "[GLPI #0527513]") no texto e monta a URL exata
    do chamado. Retorna string vazia se a tag não for encontrada.
    """
    id_extraido = extrair_id_glpi(texto)
    if not id_extraido:
        return ""
    return f"https://glpi.lar.ind.br/index.php?redirect=ticket_{id_extraido}"

def extrair_texto_docx(arquivo) -> str:
    """Extrai texto de um arquivo .docx usando a biblioteca python-docx."""
    try:
        arquivo.seek(0)
        doc = docx.Document(arquivo)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        return f"[Erro ao extrair texto do DOCX: {e}]"

def extrair_texto_xlsx(arquivo) -> str:
    """Extrai dados de uma planilha .xlsx usando pandas.to_string()."""
    try:
        arquivo.seek(0)
        df = pd.read_excel(arquivo)
        return df.to_string()
    except Exception as e:
        return f"[Erro ao extrair texto do XLSX: {e}]"

def extrair_texto_csv(arquivo) -> str:
    """Extrai dados de um arquivo .csv usando pandas.to_string()."""
    try:
        arquivo.seek(0)
        try:
            df = pd.read_csv(arquivo)
        except UnicodeDecodeError:
            arquivo.seek(0)
            df = pd.read_csv(arquivo, encoding="latin-1")
        return df.to_string()
    except Exception as e:
        return f"[Erro ao extrair texto do CSV: {e}]"

def extrair_texto_txt_md(arquivo) -> str:
    """Extrai texto de arquivos .txt e .md com fallback de codificação (utf-8 → latin-1)."""
    try:
        arquivo.seek(0)
        try:
            return arquivo.read().decode("utf-8")
        except UnicodeDecodeError:
            arquivo.seek(0)
            return arquivo.read().decode("latin-1")
    except Exception as e:
        return f"[Erro ao extrair texto do arquivo: {e}]"

def extrair_texto_html(arquivo) -> str:
    """Extrai texto puro de arquivo .html usando BeautifulSoup, removendo tags, CSS e scripts."""
    try:
        from bs4 import BeautifulSoup
        arquivo.seek(0)
        try:
            conteudo = arquivo.read().decode("utf-8")
        except UnicodeDecodeError:
            arquivo.seek(0)
            conteudo = arquivo.read().decode("latin-1")
        soup = BeautifulSoup(conteudo, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        return f"[Erro ao extrair texto do HTML: {e}]"

@st.cache_data(ttl=300, show_spinner=False)
def _buscar_usuarios_cache(project_key: str):
    """Cacheia por 5 minutos a lista de usuários atribuíveis do projeto."""
    return buscar_usuarios_responsaveis(project_key)

@st.cache_data(ttl=300, show_spinner=False)
def _buscar_terceiros_cache():
    """Cacheia por 5 minutos as opções do campo customizado Terceiros."""
    return buscar_opcoes_terceiros()

if "demanda_atual" not in st.session_state:
    st.session_state.demanda_atual = None
if "issues_similares" not in st.session_state:
    st.session_state.issues_similares = []
if "texto_entrada_inicial" not in st.session_state:
    st.session_state.texto_entrada_inicial = ""
if "disparar_analise_automatica" not in st.session_state:
    st.session_state.disparar_analise_automatica = False
if "ticket_sucesso" not in st.session_state:
    st.session_state.ticket_sucesso = None

# Processa análise automática se a flag estiver ativa
if st.session_state.disparar_analise_automatica:
    st.session_state.disparar_analise_automatica = False
    texto_a_analisar = st.session_state.texto_entrada_inicial
    if texto_a_analisar.strip():
        with st.spinner("Analisando demanda da inbox com IA..."):
            demanda_gerada = analisar_demanda(texto_a_analisar)
            if demanda_gerada:
                id_glpi = extrair_id_glpi(texto_a_analisar)
                demanda_gerada.glpi_url = extrair_link_glpi(texto_a_analisar)
                st.session_state.demanda_atual = demanda_gerada
                st.session_state.issues_similares = buscar_issues_similares(demanda_gerada.resumo, PROJETO_KEY, glpi_id=id_glpi)
                st.rerun()

with st.sidebar:
    st.title("⚙️ Hub do PO")
    st.markdown("Criação de tickets estruturados.")

st.header("✨ Criação Inteligente de Demandas")

# Feedback visual persistente após a criação de um ticket (sobrevive ao rerun do Streamlit)
if st.session_state.ticket_sucesso:
    info = st.session_state.ticket_sucesso
    st.success(info["mensagem"])
    st.markdown(f"**🔗 [Abrir {info['jira_key']} no Jira]({info['link']})**")
    if st.button("🔄 Limpar e Voltar para a Inbox"):
        st.session_state.ticket_sucesso = None
        st.session_state.demanda_atual = None
        st.session_state.issues_similares = []
        st.session_state.texto_entrada_inicial = ""
        st.rerun()
    st.divider()

# Expander para Inbox de E-mails vindos da Planilha (SQLite)
with st.expander("📥 Inbox de E-mails (Sincronização a cada 5 min)", expanded=False):
    emails_pendentes = listar_pendentes()
    if not emails_pendentes:
        st.info("Nenhum e-mail pendente na caixa de entrada.")
    else:
        st.markdown(f"Você tem **{len(emails_pendentes)}** demanda(s) pendente(s) na inbox:")
        for email in emails_pendentes:
            c_info, c_btn = st.columns([8, 2])
            with c_info:
                st.markdown(f"**Assunto:** {email['assunto']}")
                previa = email['corpo'][:150] + "..." if len(email['corpo']) > 150 else email['corpo']
                st.caption(f"Prévia: {previa}")
            with c_btn:
                if st.button("Analisar 🧠", key=f"btn_analisar_{email['id']}"):
                    texto_completo = f"Assunto: {email['assunto']}\n\nCorpo:\n{email['corpo']}"
                    st.session_state.texto_entrada_inicial = texto_completo
                    marcar_como_processado(email['id'])
                    st.session_state.disparar_analise_automatica = True
                    st.rerun()

texto_entrada = st.text_area(
    "Contexto da Demanda:",
    value=st.session_state.texto_entrada_inicial,
    height=150,
    placeholder="Ex: O PDV 3 da loja Centro travou ao emitir NFCe..."
)

# Upload multimodal: aceita screenshots, documentos, planilhas e arquivos de texto/web para a demanda
arquivos_anexados = st.file_uploader(
    "📁 Anexar Arquivos (opcional)",
    type=['png', 'jpg', 'jpeg', 'pdf', 'docx', 'xlsx', 'csv', 'txt', 'md', 'html'],
    accept_multiple_files=True,
    help="Anexe imagens (PNG/JPG), PDFs, documentos Word (.docx), planilhas (XLSX/CSV) ou arquivos de texto (.txt, .md, .html) para enriquecer a análise."
)

if st.button("Analisar com IA 🧠", type="primary"):
    if not texto_entrada.strip():
        st.warning("Por favor, insira algum texto para análise.")
    else:
        with st.spinner("A IA está classificando e estruturando a sua demanda..."):
            partes_imagens = []
            texto_final = texto_entrada
            
            for arquivo in (arquivos_anexados or []):
                nome = arquivo.name.lower()
                if nome.endswith(('.png', '.jpg', '.jpeg', '.pdf')):
                    arquivo.seek(0)
                    dados_base64 = base64.b64encode(arquivo.read()).decode("utf-8")
                    partes_imagens.append({
                        "inline_data": {
                            "mime_type": arquivo.type,
                            "data": dados_base64
                        }
                    })
                elif nome.endswith('.docx'):
                    texto_extraido = extrair_texto_docx(arquivo)
                    texto_final += f"\n\n--- Conteúdo extraído do arquivo {arquivo.name} ---\n{texto_extraido}"
                elif nome.endswith(('.xlsx', '.xls')):
                    texto_extraido = extrair_texto_xlsx(arquivo)
                    texto_final += f"\n\n--- Conteúdo extraído do arquivo {arquivo.name} ---\n{texto_extraido}"
                elif nome.endswith('.csv'):
                    texto_extraido = extrair_texto_csv(arquivo)
                    texto_final += f"\n\n--- Conteúdo extraído do arquivo {arquivo.name} ---\n{texto_extraido}"
                elif nome.endswith(('.txt', '.md')):
                    texto_extraido = extrair_texto_txt_md(arquivo)
                    texto_final += f"\n\n--- Conteúdo extraído do arquivo {arquivo.name} ---\n{texto_extraido}"
                elif nome.endswith('.html'):
                    texto_extraido = extrair_texto_html(arquivo)
                    texto_final += f"\n\n--- Conteúdo extraído do arquivo {arquivo.name} ---\n{texto_extraido}"

            demanda_gerada = analisar_demanda(texto_final, imagens=partes_imagens or None)
            if demanda_gerada:
                id_glpi = extrair_id_glpi(texto_final)
                demanda_gerada.glpi_url = extrair_link_glpi(texto_final)
                st.session_state.demanda_atual = demanda_gerada
                st.session_state.issues_similares = buscar_issues_similares(demanda_gerada.resumo, PROJETO_KEY, glpi_id=id_glpi)
                st.rerun()

st.divider()

if st.session_state.demanda_atual:
    st.subheader("📝 Revisão do Ticket")
    d: Demanda = st.session_state.demanda_atual

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        novo_tipo = st.selectbox("Tipo", [t.value for t in TipoTicket], index=[t.value for t in TipoTicket].index(d.tipo))
    with col2:
        nova_area = st.selectbox("Área", ["Varejo", "Compras"], index=["Varejo", "Compras"].index(d.area_negocios))
    with col3:
        n_prioridades = ["Muito Baixa", "Baixa", "Média", "Alta", "Muito Alta", "Crítica"]
        nova_prioridade = st.selectbox("Prioridade", n_prioridades, index=n_prioridades.index(d.prioridade))
    with col4:
        novo_glpi = st.text_input("GLPI ID / Link", value=d.glpi_url or "")

    novo_resumo = st.text_input("Resumo (Título do Card)", value=d.resumo, max_chars=70)
    novo_pai = st.text_input("Ticket Pai (Ex: CEV-1024)", value=d.pai_key or "")

    # Busca dinâmica de Responsável e Terceiros junto à API do Jira (com cache de 5 min)
    usuarios_disponiveis = _buscar_usuarios_cache(PROJETO_KEY)
    dados_terceiros = _buscar_terceiros_cache()
    opcoes_terceiros = dados_terceiros.get("opcoes", [])

    col_resp, col_terc = st.columns(2)
    with col_resp:
        nomes_usuarios = [_OPCAO_EM_BRANCO] + [u["displayName"] for u in usuarios_disponiveis]
        novo_responsavel = st.selectbox("Responsável", nomes_usuarios)
    with col_terc:
        nomes_terceiros = [_OPCAO_EM_BRANCO] + [o["value"] for o in opcoes_terceiros]
        novo_terceiro = st.selectbox("Terceiros", nomes_terceiros)

    st.markdown("### Corpo do Ticket")
    
    if novo_tipo in [TipoTicket.BUG_PRODUCAO.value, TipoTicket.BUG_SQUAD.value]:
        nova_descricao_livre = st.text_area("Descrição / Comportamento / Ação", value=d.descricao_livre or "", height=200)
    else:
        novo_objetivo = st.text_area("Objetivo / Contexto", value=d.objetivo or "")
        
        # Divisão Granular da User Story para não quebrar o dicionário do ADF
        st.markdown("**Estrutura da User Story**")
        c_as, c_q, c_p = st.columns(3)
        with c_as:
            as_eu_como = st.text_input("EU COMO:", value=d.user_story.get('eu_como', '') if d.user_story else "")
        with c_q:
            as_quero = st.text_input("QUERO:", value=d.user_story.get('quero', '') if d.user_story else "")
        with c_p:
            as_para = st.text_input("PARA:", value=d.user_story.get('para', '') if d.user_story else "")
        
        ca_txt = "\n".join(d.criterios_aceite)
        novos_criterios_txt = st.text_area("Critérios de Aceite (1 por linha)", value=ca_txt, height=150)
        
        bdd_txt = "\n\n".join([f"DADO QUE {c.get('dado', '')}\nQUANDO {c.get('quando', '')}\nENTÃO {c.get('entao', '')}" for c in d.cenarios_teste])
        novos_cenarios_txt = st.text_area("Cenários BDD", value=bdd_txt, height=150)

    # Motor Anti-Duplicidade do Jira
    issues_duplicadas = st.session_state.get("issues_similares", [])
    if issues_duplicadas:
        st.warning(
            "⚠️ **Atenção! Possíveis duplicatas encontradas no Jira:**\n\n"
            + "\n".join([f"- **[{issue['key']}]({issue['link']})**: {issue['resumo']}" for issue in issues_duplicadas])
        )

    if st.button("🚀 Aprovar e Criar no Jira", use_container_width=True):
        with st.spinner("Criando ticket no Jira com a formatação oficial ADF..."):
            d.tipo = TipoTicket(novo_tipo)
            d.area_negocios = nova_area
            d.prioridade = nova_prioridade
            d.glpi_url = novo_glpi
            d.resumo = novo_resumo
            d.pai_key = novo_pai

            # Responsável: só envia accountId se um usuário real foi selecionado
            if novo_responsavel != _OPCAO_EM_BRANCO:
                usuario_selecionado = next((u for u in usuarios_disponiveis if u["displayName"] == novo_responsavel), None)
                d.responsavel_account_id = usuario_selecionado["accountId"] if usuario_selecionado else None
            else:
                d.responsavel_account_id = None

            # Terceiros: só envia a opção se um valor real foi selecionado
            if novo_terceiro != _OPCAO_EM_BRANCO:
                opcao_selecionada = next((o for o in opcoes_terceiros if o["value"] == novo_terceiro), None)
                d.terceiros_field_id = dados_terceiros.get("field_id")
                d.terceiros_opcao = opcao_selecionada
            else:
                d.terceiros_field_id = None
                d.terceiros_opcao = None

            if d.tipo in [TipoTicket.BUG_PRODUCAO, TipoTicket.BUG_SQUAD]:
                d.descricao_livre = nova_descricao_livre
            else:
                d.objetivo = novo_objetivo
                # Preservação correta do Schema do models.py
                d.user_story = {"eu_como": as_eu_como, "quero": as_quero, "para": as_para}
                d.criterios_aceite = [linha.strip() for linha in novos_criterios_txt.split('\n') if linha.strip()]
                d.cenarios_teste = [{"dado": novos_cenarios_txt, "quando": "", "entao": ""}]

            try:
                payload = montar_payload(d)
                jira_key = criar_issue(payload)
                st.session_state.ticket_sucesso = {
                    "mensagem": f"Ticket {jira_key} criado com sucesso!",
                    "jira_key": jira_key,
                    "link": f"{JIRA_URL}/browse/{jira_key}"
                }
                st.session_state.demanda_atual = None
                st.session_state.issues_similares = []
                st.session_state.texto_entrada_inicial = ""
                st.rerun()
            except Exception as e:
                st.error(f"Erro durante a criação: {e}")