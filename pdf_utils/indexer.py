# Indicizzazione dei chunk testuali con LangChain e FAISS

from langchain.schema import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS

def build_retriever(sections: dict, model_name: str = "all-MiniLM-L6-v2", k: int = 1):
    docs = [
        Document(page_content=content.strip(), metadata={"sezione": title})
        for title, content in sections.items()
        if content.strip()
    ]

    if not docs:
        raise ValueError("Nessun contenuto valido da indicizzare. Il PDF potrebbe essere vuoto o malformato.")

    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    vectorstore = FAISS.from_documents(docs, embedding=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    return retriever
