---
name: pv-docx-pagination
description: >
  How to create or fix a proces-verbal (PV) .docx template for Ing. Assistant
  (the construction-site app in this repo) without reintroducing the
  pagination bugs that took many rounds to find and fix: blank pages between
  PVs, a signature block or a title landing orphaned on the wrong page, and a
  multi-column signature row wrapping a name onto a second line. Use this
  skill whenever the user asks to add a new PV template (e.g. "cămin de
  vane"), asks to fix pages/paging/blank-page/orphaned-title/signature
  problems in an existing pv-*.docx template, or reports that a generated PV
  doesn't look right — even if they just say "e stricat PV-ul" or paste a
  screenshot of a .docx page without naming the cause. Also use it before
  touching any pageBreakBefore, keepNext, or tab-stop XML in
  ing-assistant/templates/*.docx, since a change that looks correct in the
  raw XML can still produce a blank page or an orphaned title when actually
  rendered — this skill explains why and how to check.
---

# Paginare pentru șabloanele PV (.docx)

Aceste reguli au fost descoperite dureros, în multe runde de bug-uri reale
raportate de utilizator cu poze — un fix care arată corect structural în XML
tot poate produce o pagină goală sau un titlu rupt de propriul conținut o
dată randat. Nu le redescoperi; aplică-le de la început.

## Arhitectura (context necesar înainte de orice fix)

- Șabloanele sunt fișiere `.docx` reale în `ing-assistant/templates/pv-{cd,cm,cr}.docx`
  (și, curând, poate un al patrulea pentru "cămin de vane").
- Generarea se face client-side, în browser, cu `docxtemplater` + `pizzip`
  (librării reale din CDN, vezi `<script>` în `index.html`) — NU server-side,
  NU prin conversie PDF/imagine. Rezultatul livrat e mereu `.docx` autentic.
- Placeholder-ele sunt `{nume_camp}`, înlocuite direct în `word/document.xml`
  din interiorul arhivei .docx.
- **`santier_pv_date`** (Supabase) — UN SINGUR rând per șantier: `locatie,
  obiectiv, autorizatie_nr, autorizatie_data, proiect_nr,
  proiectant_companie, proiectant_reprezentant, diriginte_nume,
  diriginte_autorizatie, diriginte_domenii, rte_nume, rte_atestat,
  rte_domenii, constructor_reprezentant`. Aceleași nume apar în TOATE
  PV-urile unui șantier, indiferent de categoria tronsonului.
- **`santier_tronsoane`** — un rând per tronson: `categorie` (`cd`/`cm`/`cr`/…),
  `cod, specificatie_conducta, reper_start, reper_end, lungime, planse,
  profil_longitudinal, ordine`. Câmpurile din șablon nu au prefix `tronson_`.
- Un șablon per categorie generează, pentru UN tronson, o secvență de mai
  multe PV-uri diferite unul după altul în același document (12, la
  categoriile existente cd/cm/cr). Un tronson nou pe un șantier existent, sau
  un șantier nou, funcționează automat — șabloanele sunt per-categorie, nu
  per-șantier/tronson, deci nu ai nevoie să modifici nimic pentru date noi.

## Cele 7 reguli

0. **Pentru un șablon nou, construit de la zero (nu cd/cm/cr) — pune
   `pageBreakBefore` pe FIECARE titlu de PV, fără excepție, inclusiv al
   doilea PV al documentului.** Nu te baza pe "curge natural, dacă mai
   încape" pentru un șablon nou. Motivul e un bug real, costisitor, găsit
   abia în Word real: la pv-el/rz/sp/im.docx, verificarea empirică cu
   LibreOffice a arătat paginare corectă (fiecare PV pe propria pagină), dar
   randat în Microsoft Word real, mai multe PV-uri scurte s-au înghesuit pe
   aceeași pagină — LibreOffice și Word NU sunt de acord întotdeauna unde se
   rupe conținut scurt aflat aproape de limita paginii (diferă la nivel de
   metrici de font/hinting). Utilizatorul vede documentele în Word/tipărite,
   nu în LibreOffice — deci verificarea empirică "las titlul să curgă, apoi
   testez" NU e suficientă pentru un șablon nou; un break EXPLICIT e
   singurul lucru pe care Word și LibreOffice îl interpretează identic.
   Regula #2 de mai jos (curgere naturală) rămâne valabilă DOAR pentru
   cd/cm/cr — acelea au fost calibrate de un om direct în Word real, nu de
   Claude, și verificate cu ani de utilizare reală. Pentru orice șablon nou
   scris de Claude, sări regula #2 și pune break pe fiecare titlu (exceptând
   primul PV al documentului, care nu are nevoie — e deja pe pagina 1).

1. **`pageBreakBefore` nu se pune pe titlu.** Se pune pe primul paragraf
   IMEDIAT după ultimul conținut real al PV-ului anterior (fără gol de
   paragrafe goale între ele). Un gol de paragrafe goale înainte de titlu
   înseamnă că oricare din ele poate sări singur pe pagina lui — asta creează
   o pagină goală, chiar dacă titlul următor pare corect legat de break.

2. **[Doar pentru cd/cm/cr, șabloane originale] Nu fiecare titlu are nevoie
   de `pageBreakBefore`.** Dacă PV-ul anterior se termină cu loc de rezervă
   pe pagină, lasă titlul următor să curgă natural pe același spațiu —
   altfel irosești pagini fără motiv. Nu poți ști dinainte care titluri au
   nevoie de break forțat și care nu: testează empiric cu randare reală
   (vezi mai jos), nu prin deducție din XML. **NU aplica această regulă la
   un șablon nou construit de la zero** — vezi regula #0 de mai sus.

3. **`keepNext` peste tot blocul de semnături** (fiecare rând nume + linie de
   semnat), ca blocul să nu se rupă niciodată la mijloc între o pagină și
   următoarea.

4. **`keepNext` de la titlu până la primul conținut real** — înlănțuit prin:
   linia (liniile) de titlu → rândul "Nr.../Data..." → primul paragraf de
   conținut. Fără asta, titlul poate rămâne singur la finalul unei pagini
   (pentru că el singur încape) în timp ce restul conținutului lui sare pe
   pagina următoare — un titlu "orfan", vizual la fel de rupt ca o pagină
   goală, dar mai greu de observat la o citire rapidă a XML-ului.

5. **Niciun paragraf gol în plus** între sfârșitul unui PV și titlul următor —
   exact UN paragraf gol (cel care poartă `pageBreakBefore`, dacă există),
   nimic mai mult. Paragrafele goale acumulate din runde vechi de fix-uri fac
   titlurile să pornească de la înălțimi diferite pe pagină ȘI irosesc spațiu
   care poate face diferența dintre "încape" și "sare pe pagină nouă".

6. **Rânduri de semnături pe mai multe coloane** (ex. "faze determinante" cu
   4 coloane: DIRIGINTE ȘANTIER, / PROIECTANT, / CONSTRUCTOR / R.T.E.,): NU
   folosi tab-uri CENTRATE. Un tab centrat dă coloanei doar jumătate din
   lățime utilă (irosită simetric stânga-dreapta) — insuficient pentru un
   nume lung, mai ales cel de la R.T.E., care e aproape mereu cel mai lung.
   Folosește tab-uri ALINIATE LA STÂNGA, cu lățimi ASIMETRICE — coloana cu
   numele cel mai lung primește cel mai mult spațiu. Valorile curente
   (twips, relativ la margine, cu `ind left="-1400" right="-1400"`): coloane
   la 50 / 2450 / 4850 / 7250, font 9pt (`sz="18"`) — nu micșora fontul ca
   soluție rapidă, utilizatorul vrea litere mari.

7. **Verifică ÎNTOTDEAUNA cu randare reală, nu doar structural.** O modificare
   XML care pare corectă (pPr în ordinea corectă, keepNext la locul potrivit)
   tot poate produce o pagină goală sau un titlu orfan — asta se vede DOAR
   randat. Vezi secțiunea următoare.

## Cum verifici (LibreOffice + PyMuPDF)

`soffice --headless --convert-to pdf` funcționează în acest sandbox, dar are
nevoie de pachetul `libreoffice-writer`, nu doar `libreoffice-core` (care e
tot ce vine preinstalat). Dacă `soffice` dă eroare "source file could not be
loaded" pe un .docx valid, asta e cauza aproape sigur — nu e un profil stricat
sau un bug de sandbox:

```bash
apt-get update && apt-get install -y libreoffice-writer
```

Folosește `scripts/scan_pdf_pages.py` (bundlat cu acest skill) ca să
convertești și să scanezi rapid orice PDF rezultat pentru pagini goale:

```bash
soffice --headless -env:UserInstallation=file:///tmp/lo_check \
  --convert-to pdf --outdir /tmp/pvcheck fisier.docx
python3 <path-catre-acest-skill>/scripts/scan_pdf_pages.py /tmp/pvcheck/fisier.pdf
```

Scriptul afișează, per pagină, numărul de caractere și marchează cele
suspect de goale (sub prag — antetul repetat pe fiecare pagină contribuie
~230 caractere, deci orice pagină sub ~260 e aproape sigur goală sau aproape
goală). Pentru verificările specifice de conținut — un titlu care se termină
o pagină fără restul lui, un nume de pe rândul de semnături rupt pe 2 linii —
extrage textul cu `page.get_text()` (PyMuPDF) și caută manual tiparul, pentru
că astea depind de textul exact al fiecărui șablon.

**Nu te opri la "0 pagini goale".** Verifică și: (a) niciun rând de semnătură
rupt pe 2 linii, (b) niciun titlu care se termină o pagină fără restul lui,
(c) N PV-uri → N pagini EXACT pentru un șablon nou (nu "aproximativ" — vezi
regula #0; o diferență e semnul că un PV s-a înghesuit cu altul pe aceeași
pagină sau s-a rupt pe 2, exact bug-ul găsit la pv-el/rz/sp/im.docx).

Pentru un șablon nou, verificarea de mai sus (fără pagini goale) NU e
suficientă — folosește și `scripts/check_one_pv_per_page.py`, care verifică
EXPLICIT că fiecare PV își începe propria pagină, în ordine, dat un șir de
markere (un fragment scurt și unic din titlul fiecărui PV):

```bash
python3 <path-catre-acest-skill>/scripts/check_one_pv_per_page.py fisier.pdf \
  "titlu PV 1" "titlu PV 2" "titlu PV 3" ...
```

Un simplu "N pagini pentru N PV-uri" poate trece din întâmplare chiar dacă
două PV-uri s-au înghesuit pe o pagină și altul s-a rupt în două — acest
script elimină acea ambiguitate verificând poziția exactă a fiecărui titlu.

Pentru un test end-to-end real (nu doar șablonul izolat), rulează testul
Playwright canonic al acestui repo, care generează un PV real din aplicație
cu librăriile reale (nu mock-uite):

```bash
node <scratchpad>/test_pv_real_docx.js
```

Orice modificare de șablon trebuie re-testată cu acesta, plus suita completă
de regresie (vezi `CLAUDE.md` din rădăcina repo-ului pentru lista completă,
azi 17 teste) înainte de commit. Pentru un șablon NOU, scrie un test
`test_pv_real_<categorie>.js` propriu (după modelul celor existente pentru
el/rz/sp/im), care include OBLIGATORIU verificarea cu
`check_one_pv_per_page.py`, nu doar `scan_pdf_pages.py` — vezi regula #0.

## Date reale de producție (șantierul Stăuceni)

Folosește-le la testare, ca datele să reflecte cazuri reale (ex. cel mai lung
nume RTE, care e motivul pentru care coloana lui e cea mai lată):

- Diriginte: **Apetrei Cătălin** · Proiectant: **Dragoș Cojocaru** /
  S.C. CONALID S.R.L · RTE: **Daniliuc Corneliu Vicentiu** (fără cratimă, în
  DB) · Constructor: **Vițel Silviu**

## Workflow de deploy

1. Aplică fix-ul, validează XSD/paritate paragrafe (skill-ul `docx` are
   `scripts/office/validate.py --original <vechi> <nou>`).
2. Randare + scanare (secțiunea de mai sus) pe toate categoriile afectate.
3. Rulează testul PV real end-to-end + suita completă de 11 teste.
4. Bump `BUILD` în `ing-assistant/index.html` (format `bNN-YYYY-MM-DD`).
5. Commit pe branch-ul de lucru, cu mesaj în română care explică CAUZA
   reală găsită, nu doar "fix pagination" (vezi istoricul de commit-uri
   recente pentru exemple de ton și nivel de detaliu).
6. Push pe branch → fetch/checkout/merge pe `main` → push pe `main`.

Pentru contextul complet al bug-urilor deja rezolvate (inclusiv exemple XML
concrete și explicația fiecărui bug găsit pe parcurs), citește `CLAUDE.md`
din rădăcina repo-ului — acest skill e rezumatul operațional, CLAUDE.md e
istoricul complet.
