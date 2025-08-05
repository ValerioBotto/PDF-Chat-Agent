import streamlit as st
from pdf_utils.loader import layout                             #funzione che estrae struttura del pdf
from pdf_utils.preprocessor import split_sections_with_layout   #funzione che segmenta il testo in sezioni
from pdf_utils.indexer import build_retriever                   #funzione che indicizza i testi e crea retriver semantico
from agent.agent import build_agent, invoke_agent               #funzioni per costruire e invocare l'agente
from pdf_utils.graph import GraphDB                             #classe per interagire con Neo4j
import traceback                                                #per gestire le eccezioni e mostrare il traceback       
import logging
import os
from pdf_utils.graph import handle_user_preferences             #importa la funzione per inferire le preferenze dell'utente
from pdf_utils.graph import extract_topics_from_pdf             #importa la funzione per estrarre argomenti dal PDF

#configurazione logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

#configurazione della pagina streamlit
st.set_page_config(
    page_title="Chat con PDF",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📄 Chatta con il tuo PDF")

#funzione che gestisce tutto il flusso di parsing e indicizzazione del pdf
def process_pdf(uploaded_file):
    """Handle PDF processing pipeline"""
    try:
        with st.spinner("Estrazione e indicizzazione..."):
            #debug info - API Keys
            logger.debug(f"TOGETHER_API_KEY present: {bool(os.getenv('TOGETHER_API_KEY'))}")
            if os.getenv('TOGETHER_API_KEY'):
                logger.debug(f"TOGETHER_API_KEY length: {len(os.getenv('TOGETHER_API_KEY'))}")

            #converte il file caricato in bytes perché il layout richiede un file in bytes
            file_bytes = uploaded_file.getvalue()
            logger.debug(f"PDF file size: {len(file_bytes)} bytes")
            
            #estrazione struttura con spacy-layout
            doc = layout(file_bytes)
            if doc is None:
                raise ValueError("Errore nell'estrazione del documento")
            logger.debug("Document layout extraction completed")

            #segmentazione del documento in sezioni
            sections = split_sections_with_layout(doc)

            #estraggo il nome del documento
            filename = uploaded_file.name

            #Creo un nodo documento e collego l'utente
            graph = GraphDB(password="logogramma")
            graph.create_user("user")
            graph.create_document(filename)
            graph.link_user_to_document("user", filename)

            # Estrazione e collegamento topic
            full_text = "\n".join(sections.values())
            topics = extract_topics_from_pdf(full_text)

            if topics:
                graph.link_document_to_topics(filename, topics)
                logger.info(f"🔗 Collegati i seguenti topic al documento: {topics}")

            graph.close()


            logger.debug(f"Split completed: {len(sections)} sections found")
            
            if not sections:
                st.warning("⚠️ Non sono state trovate sezioni nel documento")
                sections = {"DOCUMENTO": str(doc)}
                logger.warning("No sections found, using full document")

            #possibilità di visualizzare le sezioni estratte
            with st.expander("📑 Sezioni individuate"):
                st.write(f"Numero sezioni: {len(sections)}")
                for title, content in sections.items():
                    st.write(f"🟦 {title} — {len(content.strip())} caratteri")
                    logger.debug(f"Section '{title}': {len(content.strip())} characters")

            #costruzione del retriever e dell'agente
            try:
                logger.debug("Building retriever...")
                retriever = build_retriever(sections)
                logger.debug("Retriever built successfully")
                
                logger.debug("Building agent...")
                agent = build_agent(retriever)
                logger.debug("Agent built successfully")
                
                return agent    #ritorna l'agente pronto per essere usato in chat
            except Exception as e:
                logger.error(f"Error in build phase: {str(e)}")
                raise

    except Exception as e:
        logger.error(f"Error during PDF processing: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        st.error(f"❌ Errore durante la preparazione del PDF: {str(e)}")
        st.info("📝 Dettagli tecnici per il debug:", icon="ℹ️")
        st.code(traceback.format_exc())
        return None

#inizializza lo stato della sessione per la cronologia della chat
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

#sidebar con upload PDF
with st.sidebar:
    st.header("📁 Carica documento")
    uploaded_file = st.file_uploader("Seleziona un PDF", type=["pdf"])
    
    if uploaded_file:
        print(f"[DEBUG] uploaded_file.getvalue() => {type(uploaded_file.getvalue())}")
        agent = process_pdf(uploaded_file)
        if agent:
            st.session_state.agent = agent
            st.success("✅ Documento caricato e indicizzato con successo!")
            
            #pulsante per pulire/resettare la chat
            if st.button("🗑️ Pulisci chat"):
                st.session_state.chat_history = []
                st.rerun()

#area centrale della pagina streamlit per la chat
if "agent" in st.session_state:
    #container per la chat
    chat_container = st.container()
    #possibilità di inviare messaggi
    user_message = st.chat_input("Fai una domanda sul documento...")
    if user_message:
        handle_user_preferences("user", user_message)
        try:
            #visualizzazione/append del messaggio dell'utente nella cronologia chat
            st.session_state.chat_history.append(("user", user_message))
            #mostra spinner durante l'elaborazione
            with st.spinner("🤔 Sto elaborando la risposta..."):
                try:
                    response = invoke_agent(st.session_state.agent, user_message)
                    #puliamo la risposta da eventuali URL di debug
                    if "https://" in response:
                        response = response.split("https://")[0].strip()
                    #appendiamo la risposta alla chat
                    st.session_state.chat_history.append(("assistant", response))
                    
                except Exception as e:
                    error_msg = str(e)
                    if "OUTPUT_PARSING" in error_msg:
                        #estrazione manuale risposta da errori di parsing se tutto fallisce
                        try:
                            actual_response = error_msg.split("Risposta Finale:")[1].strip()
                            st.session_state.chat_history.append(("assistant", actual_response))
                        except:
                            st.error("❌ Errore nel processare la risposta")
                    else:
                        st.error(f"❌ Errore: {str(e)}")
            
            #refresh della pagina per mostrare aggiornamento chat
            st.rerun()
                    
        except Exception as e:
            st.error(f"❌ Errore generale: {str(e)}")
    
    #stampa della cronologia della chat
    with chat_container:
        for role, message in reversed(st.session_state.chat_history):
            with st.chat_message(role):
                st.write(message)

else:
    #messaggio iniziale di default
    st.info("👈 Carica un PDF dalla sidebar per iniziare la conversazione")




