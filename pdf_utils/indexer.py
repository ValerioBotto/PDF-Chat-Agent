#Indicizzazione dei chunk testuali con LangChain e FAISS
#è proprio in questa parte che ricevo le sections dal preprocessor e le converto in oggetto Document, uno per sezione
#Ogni Document ha un campo "page_content" che contiene il testo della sezione e "metadata" che contiene il titolo
#in seguito (al momento) indicizzo i document con FAISS + HuggingFaceEmbeddings
#questo mi permette di recuperare il blocco di testo più rilevante rispetto a una domanda dell'utente
from langchain.schema import Document                               #classe base per rappresentare un documento da indicizzare
from langchain_community.embeddings import HuggingFaceEmbeddings    #modello di embedding compatibile con huggingface
from langchain_community.vectorstores import FAISS                  #per indicizzare i documenti in un database vettoriale
from langchain.text_splitter import RecursiveCharacterTextSplitter  #per spezzare il testo in chunk intelligenti
from dotenv import load_dotenv
import os
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#retriever che filtra e ordina i documenti trovati per similarità semantica
class CustomRetriever:
    def __init__(self, vectorstore, k=3, score_threshold=0.5):
        self.vectorstore = vectorstore         #oggetto faiss indicizzato
        self.k = k                             #numero massimo di risultati da ritornare (3 in questo caso)
        self.score_threshold = score_threshold #soglia massima per accettare una corrispondenza
    
    def get_relevant_documents(self, query: str):
        #esegue ricerca semantica con punteggio
        docs = self.vectorstore.similarity_search_with_score(query, k=self.k)
        for doc, score in self.vectorstore.similarity_search_with_score(query, k=self.k):
            print(f"[SCORE: {score:.3f}] {doc.page_content[:100]}...")
        
        #filtra i documenti sopra la soglia di similiarità
        filtered_docs = [
            doc for doc, score in docs 
            if score <= self.score_threshold
        ]
        
        #ordina i documenti per indice di chunk e lunghezza (priorità ai primi e più lunghi)
        filtered_docs.sort(key=lambda x: (
            x.metadata['chunk_index'], 
            -len(x.page_content)
        ))
        
        return filtered_docs #ritorna i documenti più rilevanti

#funzione per costruire l'intero retriever indicizzato a partire dalle sezioni testuali
def build_retriever(
    sections: dict, 
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2", 
    k: int = 3,
    chunk_size: int = 500,
    chunk_overlap: int = 50
):
    
    #validazione input
    if not sections:
        raise ValueError("Il dizionario delle sezioni è vuoto")
    
    if not isinstance(sections, dict):
        raise TypeError("sections deve essere un dizionario")
    #carica api token huggingface
    load_dotenv()
    hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
    
    if not hf_token:
        raise ValueError("HUGGINGFACEHUB_API_TOKEN mancante nel file .env")
    
    os.environ["HUGGINGFACEHUB_API_TOKEN"] = hf_token

    logger.info(f"Inizializzazione retriever con {len(sections)} sezioni")
    
    #splitting del testo in chunk semantici
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
    )

    #creazione dei documenti a partire dalle sezioni testuali
    docs = []
    for title, content in sections.items():
        if content.strip():
            chunks = text_splitter.split_text(content)
            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "sezione": title,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "content_length": len(chunk)
                    }
                )
                docs.append(doc)

    if not docs:
        raise ValueError("Nessun contenuto valido da indicizzare")

    logger.info(f"Creati {len(docs)} documenti da processare")

    try:
        #creazione embeddings con huggingface
        embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            cache_folder="models",
            encode_kwargs={'normalize_embeddings': True}
        )
        logger.info("Embeddings model caricato correttamente")
        
        #reazione archivio vettoriale FAISS
        vectorstore = FAISS.from_documents(docs, embedding=embeddings)
        logger.info("Vectorstore FAISS creato con successo")
        
        #costruzione retriever
        retriever = CustomRetriever(
            vectorstore=vectorstore,
            k=k,
            score_threshold=0.9
        )
        logger.info("Custom retriever creato con successo")
        
        return retriever #ritorna il retriever dal tool searchpdf
        
    except Exception as e:
        logger.error(f"Errore durante la creazione degli embedding: {str(e)}")
        raise