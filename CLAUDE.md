# Ing. Assistant — note despre generarea PV-urilor (procese-verbale)

Acest fișier documentează sistemul de generare a proceselor-verbale (.docx),
istoricul problemelor de paginare rezolvate și regulile de design care TREBUIE
respectate la orice șablon PV nou (ex: "cămin de vane"), ca să nu se piardă
munca și să nu se repete aceleași bug-uri.

## Arhitectura

- Șabloanele sunt fișiere `.docx` reale în `ing-assistant/templates/pv-{cd,cm,cr,el,rz,sp,im}.docx`.
- Generarea implicită se face client-side, în browser, cu `docxtemplater` +
  `pizzip` (librării reale, încărcate din CDN — vezi `<script>` tags din
  `index.html`), NU server-side și NU prin conversie PDF/imagine. Fișierul
  livrat utilizatorului pe acest flux e întotdeauna `.docx` autentic.
- Placeholder-ele din șablon sunt de forma `{nume_camp}` și sunt înlocuite
  direct în `word/document.xml` din interiorul arhivei .docx.
- Există și un AL DOILEA flux, opțional, care generează direct `.pdf` (butonul
  „PDF” de lângă „Generează PV”) — vezi secțiunea „Generare PV ca PDF” mai
  jos. Cele două fluxuri sunt complet independente; niciuna din regulile de
  mai jos despre `.docx`/pagination nu se aplică fluxului PDF, și invers.

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

## Generare PV ca PDF (flux secundar, opțional)

Pe lângă fluxul `.docx` de mai sus (rămas neschimbat, e implicit), aplicația
mai are un buton „PDF” (per tronson) și „Generează toate PV-urile (PDF, .zip)”
(per șantier) care generează același conținut direct ca `.pdf`, cu un motor
de layout complet separat, scris de la zero (nu conversie Word→PDF). Motivul:
utilizatorul a cerut un rezultat cu layout controlat integral de cod, fără
ambiguitățile de flow ale Word-ului care au cauzat majoritatea bug-urilor de
paginare de mai sus.

- **Librării**: `pdf-lib` + `@pdf-lib/fontkit`, încărcate din CDN (aceeași
  convenție ca docxtemplater/pizzip, `<script defer>` în `<head>`).
- **Font**: Liberation Sans (Regular/Bold/Italic/BoldItalic, licență SIL OFL,
  e fontul de substituție pentru Arial al LibreOffice pe Linux) — auto-găzduit
  în `ing-assistant/pv-pdf-assets/*.ttf`, necesar pentru diacriticele
  românești ă/â/î/ș/ț (ș/ț sunt forma cu virgulă dedesubt, U+0219/U+021B — NU
  există în WinAnsiEncoding/fonturile standard-14 ale pdf-lib, trebuie font
  TTF înglobat prin fontkit).
- **Logo**: `ing-assistant/pv-pdf-assets/logo.png` (extras din
  `word/media/image1.png` al unui șablon .docx existent).
- **Conținutul fiecărui PV**: `ing-assistant/pv-pdf-content/{cd,cm,cr,el,rz,sp,im}.json`
  — extras AUTOMAT din șabloanele `.docx` reale (nu scris de mână) cu
  `ing-assistant/pv-pdf-content/extract.py` (commis în repo — dacă un șablon
  `.docx` se modifică, regenerează cu
  `python3 extract.py ../templates/pv-<cat>.docx <cat>.json` pentru fiecare
  categorie). Logica: parsează `word/document.xml`, ancorează fiecare PV pe
  linia lui „meta” care conține `{numar_pv_N}`, urcă pe blocul de titlu
  centrat dinaintea ei, apoi clasifică fiecare paragraf din corp ca
  `text`/`bullet`/`sig4col` (blocul cu 4 coloane „faze determinante”).
- **Motorul de randare**: funcțiile `renderPvPdfPages`/`buildPvPdfBytes` din
  `index.html` (lângă `buildPvArrayBuffer`). Fiecare PV al unui tronson iese
  pe PROPRIA pagină PDF nouă (nu curge Word-style) — elimină ambiguitatea de
  flow complet. Constantele de poziționare (margini, mărimi font, înălțimi de
  linie, poziția blocului de semnături, coloanele „faze determinante”) au
  fost MĂSURATE pixel-precis dintr-o randare reală Word→LibreOffice→PDF
  (PyMuPDF, nu ghicite) — nu le modifica fără să re-măsori la fel.
  Constantele cheie: `MARGIN_L=MARGIN_R=72.1pt`, `BODY_SIZE=11pt`,
  `LINE_H=12.65pt`, `SIG4_COL_X=[2.5,122.5,242.5,362.5]` (relativ la
  MARGIN_L — tab-stop-urile twips 50/2450/4850/7250 din regula 6 de mai sus,
  convertite DIRECT /20, fără ajustare după `ind left`), `SIG4_SIZE=9pt`,
  `SIG4_ROW_H=18.5pt`, `SIG_ROW_H=45.3pt`, `BASELINE_OFFSET=9.9pt` (pdf-lib
  `drawText` dă baseline-ul, PyMuPDF `bbox[1]` dă vârful glifului — trebuie
  reconciliate).
- **Bug real, rezolvat**: la PV-urile „faze determinante” (7 din 65: 2×cd,
  2×cm, 2×cr, 1×el), paragraful de corp „reprezentat de Ing.
  {constructor_reprezentant}” (NU un rând de semnătură) avea un `<w:tab/>`
  final în șablonul original, ceea ce-l făcea să fie prins fals de
  euristica de detectare a rândurilor de semnătură simple (`sigRows`) —
  rezultat: suprapunere de text cu blocul de semnături pe 4 coloane. Fix:
  euristica cere acum `:` urmat de `Ing\.`/`ing\.` (rândurile reale de
  semnătură sunt gen „Diriginte șantier:      Ing. {nume}”), nu doar
  prezența cuvântului „Ing.” oriunde în text.
- **Testare**: fără script de test commis (scratchpad-only, per convenția
  proiectului) — dar verificat exhaustiv: toate cele 65 PV-uri din cele 7
  categorii (număr pagini = număr PV-uri, 0 pagini goale), numerotare globală
  verificată prin tot fluxul (buton → dispatcher → `buildPvPdfBytes` →
  `{numar_pv_N}` → `.zip`), și un test de integrare real pe `index.html`
  nemodificat (Supabase + CDN-uri interceptate spre bundle-uri locale reale,
  click efectiv pe butoane, descărcare reală verificată byte-cu-byte).

## Workflow de deploy

Commit pe branch-ul de lucru → push → merge pe `main` → push. Bump `BUILD`
în `index.html` la fiecare schimbare de șablon/cod. Vezi istoricul de commit-uri
recente pentru exemple de mesaje de commit (în română, cu explicația cauzei
reale, nu doar "fix pagination").
