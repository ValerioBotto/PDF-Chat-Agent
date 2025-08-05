#l'obiettivo di questa parte di codice è creare una connessione a Neo4, creare vari nodi tra cui
#User e Topic, e creare relazioni tra questi nodi del tipo "HAS_PREFERENCE"

#L'obiettivo è il seguente: ogni volta che un utente fa una domanda, se individuiamo un concetto chiave
#o preferenza, lo salviamo automaticamente nel grafo.

from neo4j import GraphDatabase
import logging
import os
from langchain_together import ChatTogether
from agent.prompt_template import SCRUTINATORE_PROMPT
from agent.prompt_template import PDF_TOPICS_PROMPT
import hashlib

#setup logging per debug
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GraphDB:
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="logogramma"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info("Connesione a Neo4j stabilita")
    
    def close(self):
        self.driver.close()
        logger.info("Connessione a Neo4j chiusa")
    

    #eseguiamo una query generica
    def run_query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return result
    
    #creaiamo un nodo User
    def create_user(self, user_id):
        query = """
        MERGE (u:User {id: $user_id})
        RETURN u
        """
        return self.run_query(query, {"user_id": user_id})
    
    def create_document(self, filename, title=None):
        #creo un nodo Documento con nome file e titolo opzionale
        doc_id = hashlib.md5(filename.encode()).hexdigest()[:12] #ID unico e compatto

        query = """
        MERGE (d:Document {id: $doc_id})
        SET d.filename = $filename,
            d.title = COALESCE($title, d.title)
        RETURN d
        """

        return self.run_query(query, {
            "doc_id": doc_id,
            "filename": filename,
            "title": title if title else None
        })
    
    def link_user_to_document(self, user_id, filename):
        #creo la relazione (User)-[:INTERACTED_WITH]->(Document)
        doc_id=hashlib.md5(filename.encode()).hexdigest()[:12]

        query = """
        MATCH (u:User {id: $user_id})
        MATCH (d:Document {id: $doc_id})
        MERGE (u)-[:INTERACTED_WITH]->(d)
        """

        return self.run_query(query, {
            "user_id": user_id,
            "doc_id": doc_id
        })
    
    #funzione per creare i nodi Topic e le relazioni TALKS_ABOUT
    def link_document_to_topics(self, filename, topics: list):
        doc_id = hashlib.md5(filename.encode()).hexdigest()[:12]

        for topic in topics:
            query = """
            MATCH (d:Document {id: $doc_id})
            MERGE (t:Topic {name: $topic})
            MERGE (d)-[:TALKS_ABOUT]->(t)
            """
            self.run_query(query, {
                "doc_id": doc_id,
                "topic": topic.lower()
            })

    #crea nodo topic e relazione di preferenza
    def add_preference(self, user_id, topic_name):
        query = """
        MATCH (u:User {id: $user_id})
        MERGE (t:Topic {name: $topic_name})
        MERGE (u)-[:HAS_PREFERENCE]->(t)
        RETURN u, t
        """
        return self.run_query(query, {
            "user_id": user_id, 
            "topic_name": topic_name.lower().strip()
        })
    


#agente "scrutinatore" per individuare preferenze dell'utente

def infer_preferences(user_input: str) -> list:
    #interroga il LLM per inferire le preferenze dall'enunciato
    prompt = SCRUTINATORE_PROMPT.format(user_input=user_input)

    try:
        llm = ChatTogether(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            temperature=0.2,
            together_api_key=os.getenv("TOGETHER_API_KEY"),
            max_tokens=128
        )

        result = llm.invoke(prompt)
        print(f"[Scrutinatore Output Grezzo] {result}")
        return [p.strip() for p in result.content.split(",") if p.strip()]
    
    except Exception as e:
        logger.error(f"Errore nell'inferire le preferenze: {str(e)}")
        return []
    

def handle_user_preferences(user_id: str, user_input: str):
    #estrae le preferenze da user_input con un LLM dedicato e le salva nel grafo
    preferences = infer_preferences(user_input)

    if preferences:
        logger.info(f"[Scrutinatore] Preferenze trovate: {preferences}")
        db = GraphDB(password="logogramma")
        db.create_user(user_id)
        for topic in preferences:
            db.add_preference(user_id, topic)
        db.close()
    else:
        logger.info("[Scrutinatore] Nessuna preferenza rilevata")


def extract_topics_from_pdf(content: str) -> list:
    #uso un llm per inferire gli argomenti/il tema principale del documento caricato
    prompt = PDF_TOPICS_PROMPT.format(content=content[:3000]) #limito a 3000 caratteri per evitare token limit

    try:
        llm = ChatTogether(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            temperature=0.2,
            together_api_key=os.getenv("TOGETHER_API_KEY"),
            max_tokens=128
        )
        result = llm.invoke(prompt)
        print(f"[Scrutinatore PDF] Output: {result.content}")
        return [t.strip() for t in result.content.split(",") if t.strip()]
    
    except Exception as e:
        logger.error(f"Errore nell'estrarre gli argomenti dal PDF: {str(e)}")

        return []




