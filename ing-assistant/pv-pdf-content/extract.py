#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrage structura completa a unui sablon pv-*.docx in JSON. Ancora de
segmentare: fiecare PV are EXACT o linie "meta" (Nr./Data) cu {numar_pv_N}.
Gaseste liniile meta (fara ambiguitate), urca pe blocul de titlu: orice linie
CENTRATA SAU INTEGRAL BOLD, consecutiva (fara alt continut intre), dinaintea
liniei meta. De ce "sau bold" si nu doar centrat: in pv-cd.docx (si pv-cm,
pv-cr), prima aparitie a titlului "PROCES VERBAL PENTRU VERIFICAREA
CALITATII / LUCRARILOR CE DEVIN ASCUNSE" are a doua linie centrata dar PRIMA
linie NU are jc=center explicit in XML (are doar indentare, probabil o
inconsistenta veche de editare manuala) -- insa e tot bold, la fel ca restul
titlurilor, deci criteriul "bold" o prinde corect fara sa depinda de un
atribut XML care lipseste doar la acel unic paragraf. Unele sabloane mai au
si o linie centrata nebold intre titlu si Nr., ex. "Incheiat astazi" (prinsa
de criteriul "centrat"). Orice alt paragraf bold+centrat din corpul unui PV
(ex. "SE AUTORIZEAZA CONTINUAREA EXECUTARII LUCRARILOR") ramane continut
normal, nu devine titlu nou, pentru ca bucla urca DOAR inapoi de la linia
meta, nu scaneaza tot documentul. Blocul special de semnaturi pe 4 coloane
(DIRIGINTE SANTIER / PROIECTANT / CONSTRUCTOR / R.T.E., folosit la PV-urile
de "faze determinante") e detectat si descompus pe coloane folosind
pozitiile reale de tab stop din pPr.
"""
import zipfile, json, sys, os, re
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
NS = {"w": W.strip("{}")}

def load_paragraphs(docx_path):
    with zipfile.ZipFile(docx_path) as z:
        xml_bytes = z.read("word/document.xml")
    root = ET.fromstring(xml_bytes)
    body = root.find("w:body", NS)
    return body.findall("w:p", NS)

def classify(p):
    pPr = p.find("w:pPr", NS)
    numPr = pPr.find("w:numPr", NS) if pPr is not None else None
    jc = pPr.find("w:jc", NS) if pPr is not None else None
    jc_val = jc.get(W + "val") if jc is not None else None
    segs = []       # text runs, in order, ignorand tab-urile (pt. afisare normala)
    tab_cols = []    # text impartit pe coloane de tab (pt. randuri cu tab-uri)
    cur_col = []
    has_tab = False
    for r in p.findall("w:r", NS):
        rpr = r.find("w:rPr", NS)
        bold = rpr is not None and rpr.find("w:b", NS) is not None
        italic = rpr is not None and rpr.find("w:i", NS) is not None
        for child in r:
            tag = child.tag.split("}")[-1]
            if tag == "t" and child.text:
                seg = {"t": child.text}
                if bold: seg["b"] = 1
                if italic: seg["i"] = 1
                segs.append(seg)
                cur_col.append(child.text)
            elif tag == "tab":
                has_tab = True
                tab_cols.append("".join(cur_col))
                cur_col = []
    tab_cols.append("".join(cur_col))
    text = "".join(s["t"] for s in segs)
    all_bold = bool(segs) and all(s.get("b") for s in segs)
    return {"numPr": numPr is not None, "jc": jc_val, "text": text, "segs": segs,
            "has_tab": has_tab, "all_bold": all_bold, "tab_cols": tab_cols}

SIG4_LABELS = ["DIRIGINTE", "PROIECTANT", "CONSTRUCTOR", "R.T.E"]
# Pozitii reale ale tab-stop-urilor (vezi pPr/tabs: 50/2450/4850/7250 twips),
# masurate DIRECT dintr-o randare reala Word->LibreOffice a unui PV "faze
# determinante" (PyMuPDF, span x0): 74.60/194.60/314.60/434.60pt absolut, cu
# MARGIN_L=72.10pt -> relativ la margine: 2.5/122.5/242.5/362.5pt. Astea sunt
# twips/20 DIRECT, fara ajustare dupa ind left=-1400 (acel atribut nu
# afecteaza pozitia absoluta a tab stop-urilor in randarea reala).
SIG4_COL_X = [2.5, 122.5, 242.5, 362.5]
SIG4_SIZE = 9
SIG4_ROW_H = 18.5

def is_sig4_header(info):
    return info["has_tab"] and all(lbl in info["text"] for lbl in SIG4_LABELS)

# Randuri de semnatura simple gen "Diriginte șantier:      Ing. {nume}" --
# ancora e un ":" urmat de spatii apoi "Ing."/"ing." (nu doar "Ing." oriunde
# in text, care prindea fals paragrafe de continut precum "reprezentat de
# Ing. {constructor_reprezentant}" -- acelea NU au ":" inainte de Ing.).
SIG_ROW_RE = re.compile(r":\s*[Ii]ng\.")

def extract_pvs(docx_path):
    infos = [classify(p) for p in load_paragraphs(docx_path)]
    n = len(infos)
    meta_idx = [i for i, info in enumerate(infos) if "{numar_pv_" in info["text"]]

    pv_starts = []
    for mi in meta_idx:
        start = mi
        j = mi - 1
        while j >= 0 and infos[j]["text"].strip() == "":
            j -= 1
        while j >= 0 and (infos[j]["jc"] == "center" or infos[j]["all_bold"]) and infos[j]["text"].strip() != "" and "{numar_pv_" not in infos[j]["text"]:
            start = j
            j -= 1
            while j >= 0 and infos[j]["text"].strip() == "":
                j -= 1
        pv_starts.append(start)

    pvs = []
    for k, start in enumerate(pv_starts):
        end = pv_starts[k + 1] if k + 1 < len(pv_starts) else n
        meta_i = meta_idx[k]
        pv = {"titleLines": [], "meta": infos[meta_i]["text"], "blocks": [], "sigHeader": None, "sigRows": []}
        for i in range(start, meta_i):
            if infos[i]["text"].strip():
                pv["titleLines"].append(infos[i]["text"].strip())
        i = meta_i + 1
        while i < end:
            info = infos[i]
            text = info["text"].strip()
            if text == "":
                i += 1; continue
            if "Nume" in text and "Prenume" in text and "Semn" in text:
                pv["sigHeader"] = True
            elif is_sig4_header(info):
                header_cols = [c.strip() for c in info["tab_cols"] if c.strip()]
                names_cols = []
                if i + 1 < end and infos[i + 1]["has_tab"]:
                    names_cols = [c.strip() for c in infos[i + 1]["tab_cols"] if c.strip()]
                    i += 1
                pv["blocks"].append({"type": "sig4col", "header": header_cols, "names": names_cols})
            elif info["has_tab"] and SIG_ROW_RE.search(text) and len(text) < 90:
                # doar partea de dinaintea primului tab (eticheta + nume) --
                # punctele de semnat sunt desenate separat, la o coloana fixa,
                # nu cele originale din sablon (care ar dubla punctele).
                pv["sigRows"].append(info["tab_cols"][0].strip())
            elif info["numPr"]:
                pv["blocks"].append({"type": "bullet", "segs": info["segs"]})
            elif info["jc"] == "center" and info["all_bold"]:
                pv["blocks"].append({"type": "text", "segs": info["segs"], "center": True})
            else:
                pv["blocks"].append({"type": "text", "segs": info["segs"]})
            i += 1
        pvs.append(pv)
    return pvs

if __name__ == "__main__":
    docx_path = sys.argv[1]
    out_path = sys.argv[2]
    pvs = extract_pvs(docx_path)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(pvs, f, ensure_ascii=False, indent=1)
    print(f"{os.path.basename(docx_path)}: {len(pvs)} PV-uri extrase -> {out_path}")
    for i, pv in enumerate(pvs):
        has4col = any(b["type"] == "sig4col" for b in pv["blocks"])
        print(f"  PV {i+1}: {' / '.join(pv['titleLines'])[:60]:60s} "
              f"blocuri={len(pv['blocks']):2d} antet-semn={'da' if pv['sigHeader'] else 'NU':3s} "
              f"randuri-semn={len(pv['sigRows'])} 4col={'DA' if has4col else ''}")
