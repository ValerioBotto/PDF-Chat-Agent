#estrazione del testo da PDF usando spacy-layout

from spacy_layout import spaCyLayout
import spacy

nlp = spacy.blank("it")
layout = spaCyLayout(nlp)

def load_text_from_pdf(path_to_pdf: str) -> str:
    doc = layout(path_to_pdf)
    return doc.text
