#funzione per suddividere il documento in sezioni logiche usando le label fornite da spacylayout
def split_sections_with_layout(doc) -> dict:
    #inizializza dizionario per contenere sezioni con un titolo iniziale predefinito
    sections = {}
    current_title = "INTRODUZIONE"
    sections[current_title] = ""

    #scorre tutti gli span etichettati nel livello "layout"
    for span in doc.spans.get("layout", []):
        label = span.label_.upper()
        if label in ("SECTION_HEADER", "TITLE", "BOLD", "BOLD_CAPTION"):
            #ogni volta che trova un'etichetta di sezione, aggiorna il titolo corrente
            current_title = span.text.strip().upper()
            if current_title not in sections:
                sections[current_title] = ""
        elif label == "TEXT":
            #aggiunge il testo sotto la sezione corrente
            sections[current_title] += span.text + "\n"

    #pulisce le sezioni vuote e rimuove spazi iniziali/finali
    cleaned = {k: v.strip() for k, v in sections.items() if v.strip()}
    #se non c'è nessuna sezione con contenuto valido, ritorna l'intero testo come una sezione unica
    return cleaned if cleaned else {"DOCUMENTO": doc.text.strip()}