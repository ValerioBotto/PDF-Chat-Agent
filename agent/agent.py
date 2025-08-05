#agente ReAct con memoria e tool esterni per PDF e web search

from langchain_together import ChatTogether                     #wrapper per usare i modelli di together.ai come llm
from langchain.memory import ConversationBufferMemory           #gestione memoria della conversazione
from langchain.agents import AgentExecutor, create_react_agent  #executor e costruttore per agenti react
from langchain.prompts import PromptTemplate                    #template per costurire il prompt dell'agente
from dotenv import load_dotenv      
from agent.tools import get_all_tools                           #funzione custom per importare i tool definiti in tools.py
from agent.prompt_template import AGENT_PROMPT                  #import del prompt
import os
import logging
import time                                                     #per gestire i timeout e i retry

#configurazione del logger per il debug
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

#caricamento delle variabili d'ambiente dal file .env
load_dotenv()

#funzione per costruire l'agente ReAct con memoria
def build_agent(retriever):
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    api_key = os.getenv("TOGETHER_API_KEY")
    logger.debug(f"API Key present: {bool(api_key)}")   #controllo se la chiave API è presente
    logger.debug(f"API Key length: {len(api_key) if api_key else 'None'}") #debug lunghezza della chiave API
    
    if not api_key:
        raise ValueError("TOGETHER_API_KEY mancante nel file .env")         #errore se chiave non presente

    try:
        llm = ChatTogether( #inizializzo llama su together.ai
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            temperature=0.2,    #temperatura bassa per risposte più coerenti
            together_api_key=api_key,
            max_tokens= 512
        )
        logger.debug("LLM initialized successfully")
        
        tools = get_all_tools(retriever, llm)   #ottengo tutti i tool definiti in tools.py
        logger.debug(f"Tools initialized: {len(tools)} tools available")
        
        #costruzione del prompt per l'agente
        try:
            prompt = PromptTemplate(
                template=AGENT_PROMPT,
                input_variables=["input", "agent_scratchpad", "tool_names", "tools", "chat_history"]
            )
            
            
            tool_names = [tool.name for tool in tools] #estrae i nomi dei tool da inserire nel prompt
            logger.debug(f"Tool names: {tool_names}")
            
            agent = create_react_agent( #crea un agente basato su chain ReAct
                llm=llm,
                tools=tools,
                prompt=prompt
            )
            
            agent_executor = AgentExecutor( #avvolge l'agente in un executor che gestisce l'interazione
                agent=agent,
                tools=tools,
                memory=memory,
                verbose=True,
                handle_parsing_errors=True #tenta il retry automatico se il parsing fallisce

            )

            logger.debug("Agent created successfully")
            return agent_executor #ritorna l'agente pronto per essere "invocato"
            
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            raise
        
    except Exception as e:
        logger.error(f"Error building agent: {str(e)}")
        raise

#funzione che invoca l'agente con meccanismo di retry e gestione timeout per evitare loop
def invoke_agent(agent, message: str, session_id: str = "default", timeout_sec=20, max_retries=2) -> str:
    attempt = 0
    while attempt < max_retries:
        try:
            start_time = time.time()
            response = agent.invoke({"input": message}) #invia messaggio all'agente
            output = response.get("output")             #estrae l'output dalla risposta

            if output and isinstance(output, str):
                return output                           #se c'è un output valido, lo ritorna subito

            #fallback: parsing manuale della stringa se formato non standard
            response_str = str(response)
            if "Final Answer:" in response_str:
                return response_str.split("Final Answer:")[-1].strip() #estrae la parte dopo final answer

            raise ValueError("Nessun output leggibile ottenuto dalla catena") #nessun risultato valido o leggibile

        except Exception as e:
            elapsed = time.time() - start_time
            if "503" in str(e) and attempt < max_retries - 1:
                time.sleep(1.5)  #attende prima di tentare nuovamente in caso di errore 503 ovvero di servizio
                attempt += 1
                continue

            return f"⚠️ Errore nella risposta dell'agente: {str(e)}"

