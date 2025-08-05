import os
from dotenv import load_dotenv
from langchain.agents import Tool                       #classe per definire tools
import requests                                         #per effettuare richieste HTTP      
from agent.prompt_template import WEB_SUMMARY_PROMPT    #prompt per il riassunto dei risultati web
import logging

#Configurazione logging
logger = logging.getLogger(__name__)

load_dotenv()

#tool per cercare all'interno di un pdf indicizzato
def get_pdf_tool(retriever):
    #funzione interna usata come entrypoint per il tool
    def search_pdf_tool(query: str) -> str:
        try:
            docs = retriever.get_relevant_documents(query) #esegue ricerca semantica
            if not docs:
                return "Nessuna informazione trovata nel PDF su questo argomento."
            
            #formatto i risultati in modo più chiaro
            results = []
            for doc in docs:
                section = doc.metadata.get("sezione", "Sezione non specificata")
                content = doc.page_content.strip()
                results.append(f"[{section}]: {content}")
            
            return "\n\n".join(results) #ritorna i risultati concatenati
        except Exception as e:
            logger.error(f"Errore durante la ricerca nel PDF: {str(e)}")
            return f"Errore durante la ricerca nel PDF: {str(e)}"

    #creo un oggetto tool per l'agente
    return Tool(
        name="SearchPDF",
        func=search_pdf_tool,
        description="Usa questo tool per cercare informazioni specifiche nel PDF. Fornisci una query precisa e pertinente."
    )


#tool per cercare informazioni online usando Brave Search e riassumere i risultati con llm
def get_brave_tool(llm):
    """Create Brave Search tool with proper initialization"""
    try:
        brave_api_key = os.getenv("BRAVE_API_KEY")
        if not brave_api_key:
            logger.warning("BRAVE_API_KEY not found in environment variables")
            return None
        
        #funzione che interroga l'api di brave e riassume i risultati
        def brave_search_and_summarize(query: str) -> str:
            try:
                headers = {"X-Subscription-Token": brave_api_key}
                response = requests.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    headers=headers,
                    params={"q": query, "count": 5}
                )
                
                if not response.ok:
                    raise Exception(f"Brave API error: {response.status_code}")
                
                results = response.json().get("web", {}).get("results", [])
                if not results:
                    return "Nessun risultato trovato nella ricerca web."
                
                #formatta i risultati per il prompt
                formatted_results = "\n\n".join([
                    f"Titolo: {r['title']}\nDescrizione: {r['description']}"
                    for r in results
                ])
                
                 #usa il prompt per chiedere riassunto all'llm
                prompt = WEB_SUMMARY_PROMPT.format(content=formatted_results)
                return llm.invoke(prompt) #invia prompt all'llm
                
            except Exception as e:
                logger.error(f"Errore durante la ricerca web: {str(e)}")
                return f"Errore durante la ricerca web: {str(e)}"

        #crea e ritorna il tool
        return Tool(
            name="BraveSearch",
            func=brave_search_and_summarize,
            description="Usa questo tool quando l'utente chiede maggiori informazioni per cercare online un concetto tecnico non ben spiegato nel PDF."
        )
        
    except Exception as e:
        logger.error(f"Error creating Brave Search tool: {str(e)}")
        return None

#funzione per aggregare tutti i tool disponibili
def get_all_tools(retriever, llm):
    tools = [] #lista che conterrà i tool

    pdf_tool = get_pdf_tool(retriever)
    if pdf_tool:
        tools.append(pdf_tool)
    
    brave_tool = get_brave_tool(llm)
    if brave_tool:
        tools.append(brave_tool)
    
    logger.info(f"Initialized {len(tools)} tools successfully")
    return tools