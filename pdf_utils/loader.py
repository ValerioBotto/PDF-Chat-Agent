# loader.py
from spacy_layout import spaCyLayout
import spacy

nlp = spacy.blank("it")
layout = spaCyLayout(nlp)

def load_text_from_pdf(uploaded_file) -> str:
    try:
        # Passa direttamente i bytes
        raw_bytes = uploaded_file.getvalue()
        doc = layout(raw_bytes)  # layout si aspetta bytes, non BytesIO
        text = doc.text.strip()
        if not text:
            raise ValueError("Il testo estratto dal PDF è vuoto.")
        return text
    except Exception as e:
        raise RuntimeError(f"Errore durante il caricamento o l'analisi del PDF: {e}")
