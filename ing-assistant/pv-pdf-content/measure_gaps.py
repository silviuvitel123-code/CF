#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
In loc sa ghicim o formula pentru spatiul dintre blocuri (nu a generalizat
sigur -- vezi incercarile anterioare: un calcul bazat pe spacing-before/line
din XML a mers bine pe un PV scurt dar a facut alt PV sa curga peste
marginea paginii), masuram DIRECT din randarea reala Word->LibreOffice cat
spatiu e intre fiecare bloc si cel de dinainte, pentru FIECARE PV, si
salvam acea valoare masurata (gapBefore, in puncte) direct in JSON. Fara
formula, fara ghiceala -- exact ce face Word, per bloc, per PV.
"""
import json, re, sys
import pymupdf as fitz

def norm(s):
    return re.sub(r'\s+', ' ', s).strip()

def fill_text(text, data):
    def repl(m):
        k = m.group(1)
        return str(data.get(k, m.group(0)))
    return re.sub(r'\{(\w+)\}', repl, text)

def block_prefix(block, data):
    segs = block.get('segs', [])
    raw = ''.join(s['t'] for s in segs)
    filled = fill_text(raw, data)
    return norm(filled)[:25]

def page_has_text(page, prefix):
    d = page.get_text('dict')
    for block in d['blocks']:
        for line in block.get('lines', []):
            text = norm(''.join(s['text'] for s in line['spans']))
            if text.startswith(prefix[:15]) or prefix[:15] in text:
                return True
    return False

def measure_category(pvs, pdf_path, data):
    # NU presupunem pagina[i] == PV[i] -- unele sabloane live au deja un bug
    # real de paginare (ex. pv-cr.docx: blocul de semnaturi al PV#1 orfan pe
    # propria pagina, 13 pagini in loc de 12), independent de munca noastra
    # -- motorul PDF nou pune oricum fiecare PV pe pagina lui proprie, deci
    # nu ne afecteaza, dar scriptul de masurat nu mai poate presupune index
    # fix. Gasim pagina fiecarui PV cautand prima linie de titlu, cautand
    # inainte de la ultima pagina gasita.
    doc = fitz.open(pdf_path)
    search_page = 0
    for pv_idx, pv in enumerate(pvs):
        title_prefix = norm(pv['titleLines'][0]) if pv['titleLines'] else None
        page_idx = None
        if title_prefix:
            for p in range(search_page, len(doc)):
                if page_has_text(doc[p], title_prefix):
                    page_idx = p
                    break
        if page_idx is None:
            page_idx = search_page  # fallback -- nu ar trebui sa se intample
        search_page = page_idx + 1
        page = doc[page_idx]
        d = page.get_text('dict')
        lines = []
        for block in d['blocks']:
            for line in block.get('lines', []):
                text = norm(''.join(s['text'] for s in line['spans']))
                if not text:
                    continue
                if text in ('-', '–', '—'):
                    # marcajul de bulina, pe propriul lui "line" -- in unele
                    # sabloane (ex. pv-cd.docx) e la un y0/y1 UȘOR diferit
                    # de randul textului lui (sub o jumatate de punct, dar
                    # peste orice toleranta rezonabila), asa ca nu ne putem
                    # baza sa-l recunoastem ca "acelasi rand" dupa pozitie --
                    # il excludem complet, nu ajuta la nimic (bulina e
                    # desenata separat, la o coloana fixa, de catre randerer).
                    continue
                y0 = line['bbox'][1]
                y1 = line['bbox'][3]
                lines.append((y0, y1, text))
        lines.sort(key=lambda t: t[0])

        # Masoara pozitia ABSOLUTA (y0, de la varful paginii) a fiecarei
        # linii de titlu si a liniei meta -- constantele vechi (yTop=141.99
        # fix + 19.76/18.65 per linie de titlu + 37.3 pana la primul bloc)
        # erau calibrate doar pe pilotul PV#1 si NU generalizeaza: alte
        # PV-uri au alt spacing-before pe titlu/meta in sablon. Masuram
        # direct, la fel ca gap-urile dintre blocuri.
        header_y = {'titleLines': [], 'meta': None}
        search_from = 0
        for tline in pv['titleLines']:
            prefix = norm(tline)[:20]
            found = None
            for i in range(search_from, len(lines)):
                if lines[i][2].startswith(prefix[:15]) or prefix[:15] in lines[i][2]:
                    found = i
                    break
            header_y['titleLines'].append(lines[found][0] if found is not None else None)
            search_from = (found + 1) if found is not None else search_from
        # linia meta contine mereu "{numar_pv_" in sablon -- in randarea
        # reala, placeholder-ul a fost inlocuit cu un numar, dar restul
        # textului (de obicei "Data" sau "/" ) ramane literal; cautam prima
        # linie de dupa titlu ce contine "Data" sau incepe cu "Nr" / "NR".
        for i in range(search_from, len(lines)):
            t = lines[i][2]
            if 'Data' in t or t.strip().startswith(('Nr', 'NR')):
                header_y['meta'] = lines[i]
                search_from = i + 1
                break
        pv['_headerY'] = header_y

        # Pasul 1: gaseste indexul liniei de START pentru fiecare bloc, in
        # ordine (fara sa incerce sa ghiceasca cate linii wrap-uite ocupa
        # blocul anterior -- asta era bug-ul: un paragraf lung (7-8 linii
        # wrap) facea gap-ul urmatorului bloc sa fie calculat fata de prima
        # lui linie, nu fata de ultima, umfland artificial golul).
        matches = []  # (block, line_index_start)
        cursor = search_from
        for b in pv['blocks']:
            if b['type'] not in ('text', 'bullet'):
                continue
            prefix = block_prefix(b, data)
            if not prefix:
                continue
            found = None
            for i in range(cursor, len(lines)):
                y0, y1, text = lines[i]
                if text.startswith(prefix[:15]) or prefix[:15] in text:
                    found = i
                    break
            if found is None:
                b['_matchFailed'] = prefix
                continue
            matches.append((b, found))
            cursor = found + 1

        # Pasul 2: gap-ul blocului i = y0 al liniei lui de start MINUS y1 al
        # liniei IMEDIAT DINAINTE (indiferent carui bloc ii apartine acea
        # linie -- poate fi a doua/a treia linie wrap-uita a blocului
        # anterior, nu neaparat prima lui linie).
        for idx, (b, line_i) in enumerate(matches):
            y0 = lines[line_i][0]
            # sari peste orice "linie" de pe ACEEASI rand vizual (ex.
            # marcajul "-" al unei buline are acelasi y0/y1 ca textul ei --
            # nu e randul anterior, e un element sibling pe acelasi rand) --
            # cautam inapoi primul y0 STRICT mai mic. Pentru idx==0 (primul
            # bloc de continut al PV-ului), linia de dinainte e chiar linia
            # meta ("Nr. X Data ...") -- masuram si acel gol, nu-l mai lasam
            # constanta fixa.
            j = line_i - 1
            while j >= 0 and lines[j][0] >= y0 - 0.5:
                j -= 1
            prev_y1 = lines[j][1] if j >= 0 else None
            b['gapBefore'] = round(y0 - prev_y1, 2) if prev_y1 is not None else None
    return doc

if __name__ == '__main__':
    import extract
    cat = sys.argv[1]
    template = sys.argv[2]
    real_pdf = sys.argv[3]
    out_json = sys.argv[4]
    data = {
        "locatie": "Stăuceni", "obiectiv": "MODERNIZARE ȘI EXTINDERE REȚEA DE ALIMENTARE CU APĂ ȘI CANALIZARE ÎN COMUNA STĂUCENI, JUDEȚUL BOTOȘANI",
        "autorizatie_nr": "56", "autorizatie_data": "21.05.2025",
        "proiect_nr": "1805/2024", "proiectant_companie": "S.C. CONALID S.R.L", "proiectant_reprezentant": "Dragoș Cojocaru",
        "diriginte_nume": "Apetrei Cătălin", "diriginte_autorizatie": "00028425 din 15.11.2013", "diriginte_domenii": "6, 3.3",
        "rte_nume": "Daniliuc Corneliu Vicentiu", "rte_atestat": "00000503 / 04.10.2017", "rte_domenii": "9.1; 1.1; 6.2; 8.2",
        "constructor_reprezentant": "Vițel Silviu",
        "tronson_cod": "CD5", "specificatie_conducta": "PEHD PN10, De 110 mm",
        "reper_start": "Pct 42 / CV6.1", "reper_end": "Pct 29 / SPAU 3", "lungime": "386",
        "planse": "2, PB5, PB6", "profil_longitudinal": "PL5"
    }
    pvs = extract.extract_pvs(template)
    measure_category(pvs, real_pdf, data)
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(pvs, f, ensure_ascii=False, indent=1)
    failed = 0
    for pv_idx, pv in enumerate(pvs):
        for b in pv['blocks']:
            if b.get('_matchFailed'):
                failed += 1
                print(f"PV{pv_idx+1}: NEPOTRIVIT: {b['_matchFailed']!r}")
    print(f"gata -> {out_json} ({failed} nepotriviri)")
