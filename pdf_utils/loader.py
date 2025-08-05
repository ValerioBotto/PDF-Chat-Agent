#fornisce il layout extractor tramite spaCyLayout (struttura + testo)

from spacy_layout import spaCyLayout
import spacy

#inizializza spaCy con una pipeline vuota per la lingua italiana
nlp = spacy.blank("it") #non carica modelli linguistici, serve solo per compatibilità con spaCyLayout

##crea un oggetto spaCyLayout che può ricevere pdf in bytes ed estrarre layout (testo+struttura)
layout = spaCyLayout(nlp)
#questo oggetto verrà usato nel main per estrarre blocchi strutturati dal pdf


