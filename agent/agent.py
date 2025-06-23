# Agente ReAct con memoria e tool per interrogare PDF

from langchain.agents import Tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from langchain_together import ChatTogether
from dotenv import load_dotenv
import os

# TOOL: ricerca nei documenti indicizzati con FAISS
# configurato dall'esterno passando un retriever

def get_tools(retriever):
    def search_pdf_tool(query: str) -> str:
        docs = retriever.get_relevant_documents(query)
        if not docs:
            return "Nessun risultato trovato."
        return "\n---\n".join([doc.page_content for doc in docs])

    tool = Tool(
        name="SearchPDF",
        func=search_pdf_tool,
        description="Usa questo tool per cercare informazioni nel PDF caricato. Inserisci una domanda chiara."
    )
    return [tool]

# Funzione per costruire l'agente ReAct con memoria

load_dotenv()

def build_agent(retriever):
    tools = get_tools(retriever)
    memory = MemorySaver()

    llm = ChatTogether(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        temperature=0.3,
        together_api_key=os.getenv("TOGETHER_API_KEY")
    )

    agent = create_react_agent(
        model=llm,
        checkpointer=memory,
        tools=tools
    )
    return agent

# Funzione di invocazione

def invoke_agent(agent, message: str, session_id: str = "default") -> str:
    response = agent.invoke(
        {"messages": [HumanMessage(content=message)]},
        config={"configurable": {
            "session_id": session_id,
            "thread_id": session_id,
            "recursion_limit": 2,
        }}
    )
    return response["messages"][-1].content
