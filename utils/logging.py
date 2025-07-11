import logging

#configuro un logging semplice e utile per il testing, in modo tale da 
#tenere traccia di cosa fa l'agente ad ogni richiesta: quale tool usa, quale input riceve
#e quali risultati restituisce

logging.basicConfig(
    level=logging.INFO,  
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def log_tool_usage(tool_name, query, result_preview=None):
    logging.info(f"[TOOL INVOCATO] {tool_name}")
    logging.info(f"[QUERY] {query}")
    if result_preview:
        snippet = result_preview[:300].replace('\n', ' ')
        logging.info(f"[RISULTATO PARZIALE] {snippet}...")