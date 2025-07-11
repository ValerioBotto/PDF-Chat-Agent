import streamlit as st
from pdf_utils.loader import load_text_from_pdf
from pdf_utils.preprocessor import split_sections
from pdf_utils.indexer import build_retriever
from agent.agent import build_agent, invoke_agent

st.set_page_config(page_title="Chat con PDF", layout="wide")
st.title("📄 Chatta con il tuo PDF")

# Caricamento PDF
uploaded_file = st.file_uploader("Carica un PDF", type=["pdf"])
if uploaded_file:
    try:
        with st.spinner("Estrazione e indicizzazione..."):
            # Estrazione testo
            text = load_text_from_pdf(uploaded_file)

            # Split in sezioni
            sections = split_sections(text)

            #DEBUG: mostra sezioni trovate 
            st.write(f"Numero sezioni individuate: {len(sections)}")
            for title, content in sections.items():
                st.write(f"🟦 {title} — {len(content.strip())} caratteri")

            # Costruzione retriever e agente
            retriever = build_retriever(sections)
            agent = build_agent(retriever)

            st.session_state.agent = agent
            st.success("✅ Documento caricato e indicizzato con successo!")

    except Exception as e:
        st.error(f"❌ Errore durante la preparazione del PDF: {e}")

# Interazione utente
if "agent" in st.session_state:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_message = st.chat_input("Fai una domanda al tuo PDF...")
    if user_message:
        with st.spinner("Sto ragionando..."):
            response = invoke_agent(st.session_state.agent, user_message)

        # Salvataggio conversazione
        st.session_state.chat_history.append(("user", user_message))
        st.session_state.chat_history.append(("agent", response))

    # Mostra cronologia
    for role, message in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(message)

