import os
from dotenv import load_dotenv
from langchain.agents import Tool
from langchain_community.tools.brave_search import BraveSearchWrapper
from prompt_template import WEB_SUMMARY_PROMPT

load_dotenv()

# Tool Brave Search: accesso alla ricerca web tramite Brave API
def get_brave_tool(llm):
    brave_search = BraveSearchWrapper.from_api_key(
        api_key=os.getenv("BRAVE_API_KEY"),
        k=5,
        search_kwargs={"count": 5}
    )

    def brave_search_and_summarize(query: str) -> str:
        results = brave_search.run(query)
        prompt = WEB_SUMMARY_PROMPT
        return llm.invoke(prompt)

    return Tool(
        name="BraveSearch",
        func=brave_search_and_summarize,
        description="Usa questo tool quando l'utente chiede maggiori informazioni per cercare online un concetto tecnico non ben spiegato nel PDF, con contesto mancante o non sufficiente nel PDF e ottieni un riassunto."
    )


# Tool per interrogare un PDF indicizzato via retriever
def get_pdf_tool(retriever):
    def search_pdf_tool(query: str) -> str:
        docs = retriever.get_relevant_documents(query)
        if not docs:
            return "Nessun risultato trovato."
        return "\n---\n".join([doc.page_content for doc in docs])

    return Tool(
        name="SearchPDF",
        func=search_pdf_tool,
        description="Usa questo tool per cercare informazioni nel PDF caricato. Inserisci una domanda chiara."
    )


# Funzione per aggregare tutti i tools
def get_all_tools(retriever, llm):
    return [
        get_pdf_tool(retriever),
        get_brave_tool(llm)
    ]
