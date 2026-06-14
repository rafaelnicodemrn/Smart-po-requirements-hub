# app.py
import streamlit as st
import json
from config import JIRA_URL
# Otimização via Facade do pacote core
from core import Demanda, TipoTicket, AreaNegocios, Prioridade, analisar_demanda, montar_payload, criar_issue

st.set_page_config(page_title="Hub do PO", page_icon="🎯", layout="wide")

if "demanda_atual" not in st.session_state:
    st.session_state.demanda_atual = None

with st.sidebar:
    st.title("⚙️ Hub do PO")
    st.markdown("Criação de tickets estruturados.")

st.header("✨ Criação Inteligente de Demandas")
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

    if st.button("🚀 Aprovar e Criar no Jira", use_container_width=True):
        with st.spinner("Criando ticket no Jira com a formatação oficial ADF..."):
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
                # Preservação correta do Schema do models.py
                d.user_story = {"eu_como": as_eu_como, "quero": as_quero, "para": as_para}
                d.criterios_aceite = [linha.strip() for linha in novos_criterios_txt.split('\n') if linha.strip()]
                d.cenarios_teste = [{"dado": novos_cenarios_txt, "quando": "", "entao": ""}]

            try:
                payload = montar_payload(d)
                jira_key = criar_issue(payload)
                st.success(f"Ticket criado com sucesso: {jira_key}")
                st.markdown(f"**🔗 [Abrir {jira_key} no Jira]({JIRA_URL}/browse/{jira_key})**")
                st.session_state.demanda_atual = None
                st.rerun()
            except Exception as e:
                st.error(f"Erro durante a criação: {e}")