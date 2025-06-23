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
            current_section = line_stripped
            sections[current_section] = ""
        else:
            sections[current_section] += line + "\n"

    return sections