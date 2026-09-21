# Ing. Assistant — note despre generarea PV-urilor (procese-verbale)

Acest fișier documentează sistemul de generare a proceselor-verbale (.docx),
istoricul problemelor de paginare rezolvate și regulile de design care TREBUIE
respectate la orice șablon PV nou (ex: "cămin de vane"), ca să nu se piardă
munca și să nu se repete aceleași bug-uri.

## Arhitectura

- Șabloanele sunt fișiere `.docx` reale în `ing-assistant/templates/pv-{cd,cm,cr}.docx`.
- Generarea se face client-side, în browser, cu `docxtemplater` + `pizzip`
  (librării reale, încărcate din CDN — vezi `<script>` tags din `index.html`),
  NU server-side și NU prin conversie PDF/imagine. Rezultatul livrat
  utilizatorului este întotdeauna `.docx` autentic.
- Placeholder-ele din șablon sunt de forma `{nume_camp}` și sunt înlocuite
  direct în `word/document.xml` din interiorul arhivei .docx.

## Sursele de date (Supabase)

- **`santier_pv_date`** — UN SINGUR rând per șantier (`santier_id`). Conține
  câmpurile comune tuturor PV-urilor, indiferent de categorie (cd/cm/cr):
  `locatie, obiectiv, autorizatie_nr, autorizatie_data, proiect_nr,
  proiectant_companie, proiectant_reprezentant, diriginte_nume,
  diriginte_autorizatie, diriginte_domenii, rte_nume, rte_atestat,
  rte_domenii, constructor_reprezentant`.
  → Aceleași nume de diriginte/proiectant/RTE/constructor apar în TOATE
  PV-urile generate pentru un șantier, indiferent de categoria tronsonului.
- **`santier_tronsoane`** — un rând per tronson, cu `categorie` (`cd`/`cm`/`cr`),
  `cod, specificatie_conducta, reper_start, reper_end, lungime, planse,
  profil_longitudinal, ordine`.
- Câmpurile din șablon corespund exact numelor de coloane de mai sus (fără
  prefix `tronson_`, ex: `{lungime}`, `{planse}`, nu `{tronson_lungime}`).

Adăugarea unui tronson nou pe un șantier existent, sau a unui șantier nou cu
tronsoane și date PV noi, **funcționează automat** — nu necesită nicio
modificare de șablon, pentru că șabloanele sunt per-categorie (cd/cm/cr), nu
per-șantier/tronson.

## Structura unui șablon (12 procese-verbale, în ordine)

Fiecare șablon (`pv-cd`, `pv-cm`, `pv-cr`) generează, pentru UN tronson, o
secvență de 12 PV-uri diferite, unul după altul în același document:

1. PROCES VERBAL DE PREDARE – PRIMIRE / FRONT DE LUCRU
2. PROCES-VERBAL DE TRASARE
3. PROCES VERBAL PENTRU VERIFICAREA CALITĂȚII LUCRĂRILOR CE DEVIN ASCUNSE (#1)
4. PROCES VERBAL PENTRU VERIFICAREA CALITĂȚII LUCRĂRILOR CE DEVIN ASCUNSE (#2)
5. PROCES VERBAL DE CONTROL AL CALITATII LUCRARILOR IN FAZE DETERMINANTE (#1)
6. PROCES VERBAL DE RECEPȚIE CALITATIVĂ
7. PROCES-VERBAL PENTRU VERIFICAREA CALITATII LUCRARILOR CE DEVIN ASCUNSE
8. PROCES VERBAL / DE RECEPȚIE CALITATIVĂ
9. PROCES-VERBAL DE RECEPTIE CALITATIVA
10. PROCES VERBAL DE CONTROL AL CALITATII LUCRARILOR IN FAZE DETERMINANTE (#2)
11. PROCES-VERBAL DE RECEPTIE CALITATIVA
12. PROCES-VERBAL DE RECEPTIE (final)

**Rezultatul corect, verificat cu date reale: 12 PV-uri → exact 12 pagini,
0 pagini goale.**

## Regulile de design (OBLIGATORII la orice șablon PV nou)

Aceste reguli au fost descoperite dureros, în multe runde de bug-uri reale
raportate de utilizator cu poze. La orice șablon nou (ex: cămin de vane),
aplică-le de la început, nu le redescoperi:

1. **`pageBreakBefore` nu se pune pe titlu.** Se pune pe primul paragraf
   IMEDIAT după ultimul conținut real al PV-ului anterior (fără gol de
   paragrafe goale între ele) — altfel orice paragraf gol rămas în acel gol
   poate sări singur pe pagina lui, creând o pagină goală.

2. **Nu fiecare titlu are nevoie de `pageBreakBefore`.** Dacă PV-ul anterior
   se termină cu loc de rezervă pe pagină, lasă titlul următor să curgă
   natural pe același spațiu — altfel irosești pagini. În șabloanele actuale,
   titlurile #1, #3, #9, #12 (din cele 12 de mai sus) NU au break forțat;
   restul (#2,4,5,6,7,8,10,11) au. Acest tipar a fost calibrat empiric
   (comparând cu un document corectat manual de utilizator) — dacă adaugi
   un PV nou, testează empiric cu LibreOffice care titluri au nevoie de break.

3. **`keepNext` peste tot blocul de semnături** (nume + linie de semnat, toate
   rândurile), ca blocul să nu se rupă niciodată la mijloc.

4. **`keepNext` de la titlu până la primul conținut real** — înlănțuit prin:
   linia (liniile) de titlu → rândul "Nr.../Data..." → primul paragraf de
   conținut. Altfel titlul poate rămâne singur la finalul unei pagini, cu
   restul conținutului sărind pe pagina următoare (bug real, cu poză, rezolvat
   în commit `27e39c3`).

5. **Nu lăsa paragrafe goale acumulate** între sfârșitul unui PV și titlul
   următor. Exact UN paragraf gol (cel care poartă `pageBreakBefore`, dacă
   există) — nimic mai mult. Paragrafele goale în plus (rămase din runde
   vechi de fix-uri) fac ca titlurile să pornească de la înălțimi diferite pe
   pagină ȘI irosesc spațiu care poate face diferența dintre "încape" și
   "sare pe pagină nouă".

6. **Rânduri de semnături pe mai multe coloane (ex: "faze determinante" cu 4
   coloane: DIRIGINTE ȘANTIER, / PROIECTANT, / CONSTRUCTOR / R.T.E.,):
   NU folosi tab-uri CENTRATE.** Un tab centrat dă coloanei doar jumătate din
   lățime utilă (irosită simetric stânga-dreapta), insuficient pentru un nume
   lung. Folosește tab-uri ALINIATE LA STÂNGA, cu lățimi ASIMETRICE — coloana
   cu numele cel mai lung (de regulă R.T.E.) primește cel mai mult spațiu.
   Valorile curente (twips, relativ la margine, cu `ind left="-1400"
   right="-1400"`): coloane la 50 / 2450 / 4850 / 7250. Font 9pt (sz=18) —
   utilizatorul vrea litere mari, nu micșora fontul ca soluție rapidă.

7. **Verifică ÎNTOTDEAUNA cu randare reală (LibreOffice), nu doar structural.**
   `soffice --headless --convert-to pdf` funcționează în acest sandbox (are
   nevoie de pachetul `libreoffice-writer`, nu doar `libreoffice-core` — dacă
   lipsește: `apt-get update && apt-get install -y libreoffice-writer`).
   Extrage textul pagină-cu-pagină cu PyMuPDF (`fitz`) și verifică: (a) nicio
   pagină aproape goală (heuristică: `len(text.strip()) - 230 < 30`, cele
   ~230 caractere fiind antetul repetat pe fiecare pagină), (b) niciun rând de
   semnătură rupt pe 2 linii, (c) niciun titlu care se termină o pagină fără
   restul conținutului lui.

## Datele reale de producție (șantierul Stăuceni)

- `santier_id`: `bcbd60bb-d1af-4bba-a859-629cf1d53bdd`
- Diriginte: **Apetrei Cătălin** (nu "Bota Petru Serban" — asta era date vechi
  de test, nu mai e valabilă)
- Proiectant: **Dragoș Cojocaru** / S.C. CONALID S.R.L
- RTE: **Daniliuc Corneliu Vicentiu** (fără cratimă, în DB) — cel mai lung
  nume, motiv pentru care coloana R.T.E. e cea mai lată în rândul cu 4 coloane
- Constructor: **Vițel Silviu**

## Fișiere de test relevante

- `test_pv_real_docx.js` — testul e2e canonic (Playwright + librării reale
  docxtemplater/pizzip din CDN, nu mock-uite), generează un PV real din
  aplicație. Orice modificare de șablon trebuie re-testată cu acesta.
- Suita completă de regresie (11 teste) trebuie să treacă înainte de orice
  commit pe șabloane: `test_drag_render_guard.js, test_cell_formulas.js,
  test_progres_subtabs.js, test_multiselect.js, test_persistence.js,
  test_cell_merge.js, test_motion_transitions.js, test_pwa_install.js,
  test_pwa_real_server.js, test_pv_generation.js, test_pv_real_docx.js`.

## Workflow de deploy

Commit pe branch-ul de lucru → push → merge pe `main` → push. Bump `BUILD`
în `index.html` la fiecare schimbare de șablon/cod. Vezi istoricul de commit-uri
recente pentru exemple de mesaje de commit (în română, cu explicația cauzei
reale, nu doar "fix pagination").
