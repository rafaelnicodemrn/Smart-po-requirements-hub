# app.py
import streamlit as st
import json
from config import JIRA_URL
from core.models import Demanda, TipoTicket, AreaNegocios, Prioridade
from core.gemini_client import analisar_demanda
from core.jira_fields import montar_payload
from core.jira_client import criar_issue

st.set_page_config(page_title="Hub do PO", page_icon="🎯", layout="wide")

# --- GERENCIAMENTO DE ESTADO ---
if "demanda_atual" not in st.session_state:
    st.session_state.demanda_atual = None

# --- BARRA LATERAL (MENU) ---
with st.sidebar:
    st.title("⚙️ Hub do PO")
    st.markdown("Criação de tickets estruturados.")
    st.info("A captura automática de arquivos (Imagens/PDFs) será habilitada no próximo bloco da nossa sprint.")

# --- TELA PRINCIPAL ---
st.header("✨ Criação Inteligente de Demandas")
st.markdown("Cole o e-mail do GLPI ou digite sua demanda livre abaixo:")

texto_entrada = st.text_area("Contexto da Demanda:", height=150, placeholder="Ex: O PDV 3 da loja Centro travou ao emitir NFCe...")

if st.button("Analisar com IA 🧠", type="primary"):
    if not texto_entrada.strip():
        st.warning("Por favor, insira algum texto para análise.")
    else:
        with st.spinner("A IA está classificando e estruturando a sua demanda..."):
            demanda_gerada = analisar_demanda(texto_entrada)
            if demanda_gerada:
                st.session_state.demanda_atual = demanda_gerada
                st.rerun()

st.divider()

# --- TELA DE REVISÃO E EDIÇÃO (HITL) ---
if st.session_state.demanda_atual:
    st.subheader("📝 Revisão do Ticket")
    d: Demanda = st.session_state.demanda_atual

    # Colunas Superiores (Campos de Sistema)
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
    novo_pai = st.text_input("Ticket Pai (Ex: CEV-1024)", value=d.pai_key or "", help="Vincule a um Épico ou História Pai existente")

    # --- CAMPOS DINÂMICOS BASEADOS NO TIPO ---
    st.markdown("### Corpo do Ticket")
    
    if novo_tipo in [TipoTicket.BUG_PRODUCAO.value, TipoTicket.BUG_SQUAD.value]:
        nova_descricao_livre = st.text_area("Descrição / Comportamento / Ação", value=d.descricao_livre or "", height=200)
    
    else:
        # Se for História ou Manutenção, abre os campos de engenharia
        novo_objetivo = st.text_area("Objetivo / Contexto", value=d.objetivo or "")
        
        # User Story (Convertida para string editável)
        st_txt = f"EU COMO: {d.user_story.get('eu_como', '')}\nQUERO: {d.user_story.get('quero', '')}\nPARA: {d.user_story.get('para', '')}" if d.user_story else ""
        nova_historia_txt = st.text_area("User Story", value=st_txt, height=100)
        
        # Critérios de Aceite (Lista para String)
        ca_txt = "\n".join(d.criterios_aceite)
        novos_criterios_txt = st.text_area("Critérios de Aceite (1 por linha)", value=ca_txt, height=150)
        
        # BDD (Lista para String)
        bdd_txt = "\n\n".join([f"DADO QUE {c.get('dado', '')}\nQUANDO {c.get('quando', '')}\nENTÃO {c.get('entao', '')}" for c in d.cenarios_teste])
        novos_cenarios_txt = st.text_area("Cenários BDD", value=bdd_txt, height=200)

    # Botão de Ação Final
    if st.button("🚀 Aprovar e Criar no Jira", use_container_width=True):
        with st.spinner("Criando ticket no Jira com a formatação oficial ADF..."):
            
            # 1. Atualizamos o objeto Demanda com as edições feitas na tela
            d.tipo = TipoTicket(novo_tipo)
            d.area_negocios = nova_area
            d.prioridade = nova_prioridade
            d.glpi_url = novo_glpi
            d.resumo = novo_resumo
            d.pai_key = novo_pai

            if d.tipo in [TipoTicket.BUG_PRODUCAO, TipoTicket.BUG_SQUAD]:
                d.descricao_livre = nova_descricao_livre
            else:
                d.objetivo = novo_objetivo
                # O ADF Builder que fizemos no passo anterior já entende esses textos
                # Só precisamos devolver no formato que ele espera
                d.user_story = {"eu_como": "", "quero": nova_historia_txt, "para": ""} 
                d.criterios_aceite = novos_criterios_txt.split('\n') if novos_criterios_txt else []
                d.cenarios_teste = [{"dado": novos_cenarios_txt, "quando": "", "entao": ""}] # O ADF renderiza como texto contínuo

            # 2. Monta o payload seguro e despacha
            try:
                payload = montar_payload(d)
                jira_key = criar_issue(payload)
                st.success(f"Ticket criado com sucesso: {jira_key}")
                st.markdown(f"**🔗 [Abrir {jira_key} no Jira]({JIRA_URL}/browse/{jira_key})**")
                st.session_state.demanda_atual = None # Limpa a tela para a próxima demanda
            except Exception as e:
                st.error(f"Erro durante a criação: {e}")