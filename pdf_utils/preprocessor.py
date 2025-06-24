# Segmentazione del testo in sezioni basata su euristiche

import re

def is_likely_section_title(line: str) -> bool:
    line = line.strip()
    score = 0

    # Euristiche
    if line.isupper():
        score += 2
    if re.match(r"^(\d+(\.\d+)*\s+)?[A-Z][^\n]{3,}$", line):
        score += 2
    if len(line) <= 100:
        score += 1
    if not line.endswith(('.', ':')):
        score += 1

    return score >= 4

def split_sections(text: str) -> dict:
    sections = {}
    current_section = "INTRODUZIONE"
    sections[current_section] = ""

    for line in text.split("\n"):
        line_stripped = line.strip()
        if is_likely_section_title(line_stripped):
            current_section = line_stripped.upper()[:80]  # Limita lunghezza e uniforma
            sections[current_section] = ""
        else:
            sections[current_section] += line + "\n"

    # Fallback se c'è solo una sezione e poco testo
    total_text = "\n".join(s for s in sections.values())
    if len(sections) <= 1 or len(total_text.strip()) < 300:
        return {"PDF": text.strip()}

    return sections
