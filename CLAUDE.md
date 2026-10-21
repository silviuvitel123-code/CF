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
  — extras AUTOMAT din șabloanele `.docx` reale (nu scris de mână), în DOI
  pași (ambii scripturi sunt commise în `ing-assistant/pv-pdf-content/`):
  1. `extract.py <template.docx> <out.json>` parsează `word/document.xml`,
     ancorează fiecare PV pe linia lui „meta” (conține `{numar_pv_N}`), urcă
     pe blocul de titlu (linii CENTRATE SAU INTEGRAL BOLD consecutive
     dinaintea ei — vezi comentariul din fișier de ce „sau bold”: un titlu
     poate să nu aibă `jc=center` explicit, dar tot bold e), apoi clasifică
     fiecare paragraf din corp ca `text`/`bullet`/`sig4col` (blocul cu 4
     coloane „faze determinante”).
  2. `measure_gaps.py <cat> <template.docx> <word_real.pdf> <out.json>`
     ADAUGĂ peste rezultatul de mai sus un `gapBefore` (în puncte) pe
     fiecare bloc de `text`/`bullet` și un `_headerY` per PV (poziția Y
     absolută a fiecărei linii de titlu + a liniei meta) — **măsurate
     direct** dintr-o randare REALĂ a șablonului (`render_word_real.js` →
     docxtemplater/pizzip reale → `soffice --headless --convert-to pdf` →
     PyMuPDF), nu calculate dintr-o formulă. S-a încercat o formulă bazată
     pe `spacing before/after/line` din XML — a mers bine pe un PV, dar
     NU generalizează (alte PV-uri au alt spacing moștenit din
     `docDefaults`/stiluri, imposibil de reconstruit fiabil fără un motor
     complet de rezolvare a stilurilor Word) — de aceea se măsoară, nu se
     ghicește. Regenerare completă pentru o categorie:
     ```
     cd ing-assistant/pv-pdf-content
     npm install pizzip docxtemplater playwright   # o singura data
     node render_word_real.js <cat> <numarPV>       # cd/cm/cr=12,el=7,rz/sp=8,im=6
     soffice --headless --convert-to pdf word_real_<cat>.docx
     python3 measure_gaps.py <cat> ../templates/pv-<cat>.docx \
         word_real_<cat>.pdf <cat>.json
     ```
- **Motorul de randare**: funcțiile `renderPvPdfPages`/`buildPvPdfBytes` din
  `index.html` (lângă `buildPvArrayBuffer`). Fiecare PV al unui tronson iese
  pe PROPRIA pagină PDF nouă (nu curge Word-style) — elimină ambiguitatea de
  flow complet. Pozițiile liniilor de titlu/meta vin din `_headerY` (dacă
  lipsesc, constante fallback `141.99`/`19.76`/`18.65`); spațiul dinaintea
  fiecărui bloc de `text`/`bullet` vine din `gapBefore` (dacă lipsește,
  `PARA_GAP_EXTRA=6pt` doar pentru blocuri `text`, 0 pentru `bullet` — ca să
  nu se rupă randuri de buline consecutive în aceeași listă). Restul
  constantelor (margini, mărimi font, coloanele „faze determinante”, blocul
  de semnături simplu) au fost măsurate o singură dată, pixel-precis, pe
  pilotul inițial și sunt stabile — nu le modifica fără să re-măsori la fel:
  `MARGIN_L=MARGIN_R=72.1pt`, `BODY_SIZE=11pt`, `LINE_H=12.65pt`,
  `SIG4_COL_X=[2.5,122.5,242.5,362.5]` (relativ la MARGIN_L — tab-stop-urile
  twips 50/2450/4850/7250 din regula 6 de mai sus, convertite DIRECT /20,
  fără ajustare după `ind left`), `SIG4_SIZE=9pt`, `SIG4_ROW_H=18.5pt`,
  `SIG_ROW_H=45.3pt`, `BASELINE_OFFSET=9.9pt` (pdf-lib `drawText` dă
  baseline-ul, PyMuPDF `bbox[1]` dă vârful glifului — trebuie reconciliate).
  Blocul de semnături simplu (`sigRows`) rămâne ANCORAT la o distanță FIXĂ
  de baza paginii (NU urmărește `gapBefore`) — decizie explicită a
  utilizatorului („nu muta semnăturile mai sus”); singurul lucru care s-a
  corectat e că CONȚINUTUL de deasupra lui acum ocupă spațiul real pe care-l
  ocupă și în Word, deci golul dintre ele s-a redus natural, fără să se
  mute semnătura.
- **Bug-uri reale, rezolvate** (descoperite cu capturi de ecran trimise de
  utilizator, comparând direct cu Word):
  - La PV-urile „faze determinante” (7 din 65: 2×cd, 2×cm, 2×cr, 1×el),
    paragraful de corp „reprezentat de Ing. {constructor_reprezentant}” (NU
    un rând de semnătură) avea un `<w:tab/>` final în șablonul original,
    prins fals de euristica de detectare a rândurilor de semnătură simple
    (`sigRows`) → suprapunere de text cu blocul pe 4 coloane. Fix: euristica
    cere acum `:` urmat de `Ing\.`/`ing\.` (rândurile reale sunt gen
    „Diriginte șantier:      Ing. {nume}”), nu doar cuvântul „Ing.” oriunde.
  - `extract.py` arunca orice paragraf gol din șablon — dar Word chiar
    randează acel spațiu (fiecare paragraf gol are propria lui linie +
    spacing), deci conținutul ieșea sistematic mai compact decât în Word,
    lăsând un gol mare și nenatural înaintea blocului de semnături. Fix:
    `measure_gaps.py` (vezi mai sus).
  - La măsurare: marcajul de bulină „-” stă pe propriul lui „rând” de text
    (PyMuPDF), nu mereu la EXACT același y0/y1 ca textul bulinei (diferă cu
    sub 1pt în unele șabloane) — confundat cu un rând anterior real, dădea
    `gapBefore` negativ. Fix: liniile care conțin DOAR „-” sunt excluse
    complet din măsurătoare (bulina e desenată separat, la coloană fixă, de
    motorul de randare — nu are nicio relevanță pentru spațiere).
  - `pv-cr.docx` (șablonul LIVE, independent de munca de mai sus) are un bug
    de paginare real: blocul de semnături al PV#1 e orfan pe propria pagină
    (13 pagini în loc de 12 la randare reală cu date de producție) — motorul
    PDF nu e afectat (fiecare PV oricum pe propria pagină), dar
    `measure_gaps.py` nu mai poate presupune „pagina N = PV-ul N”; caută
    acum pagina fiecărui PV după textul titlului lui, înainte, din pagina
    găsită anterior. Bug-ul de paginare al `.docx`-ului în sine NU a fost
    încă reparat (ar intra sub regulile din secțiunea de mai sus).
- **Testare**: fără script de test commis separat (scratchpad-only, per
  convenția proiectului) — dar verificat exhaustiv: toate cele 65 PV-uri din
  cele 7 categorii (număr pagini = număr PV-uri, 0 pagini goale, 0 depășiri
  de pagină), conținutul fiecărui PV comparat linie-cu-linie cu randarea
  Word reală (diferențe sub 5pt pe toate transițiile verificate), și un test
  de integrare real pe `index.html` nemodificat (Supabase + CDN-uri
  interceptate spre bundle-uri locale reale, click efectiv pe butoane din
  UI, descărcare reală verificată byte-cu-byte, inclusiv arhiva .zip cu
  numerotare globală pe mai multe tronsoane).

## Materiale (listă materiale + comenzi) — subcapitol nou pe șantier

Tab nou la nivel de șantier ("Materiale", lângă Date șantier/PV/Progres/
Documente), cu două subtab-uri: **Listă materiale** (cantitățile prevăzute
inițial, din listele de cantități/deviz) și **Comenzi** (comenzile de
materiale care ajung în șantier și consumă din acel total). Cerut explicit
de utilizator, cu mockup interactiv (Artifact „Design”) aprobat înainte de
implementare.

### Model de date (Supabase)

Trei tabele noi, RLS `for all to public using (auth.role() = 'authenticated')`
(același tipar ca `santier_tronsoane`/`santier_documente`):

- **`santier_materiale`** — un rând per material: `santier_id, denumire,
  unitate_masura, cantitate_prevazuta (numeric), ordine`. `denumire` rămâne
  EXACT textul tehnic din deviz (ex: „Teava PE 100 SDR 17 PN 10 D=110x6.60
  mm”) — decizie explicită a utilizatorului, nu se traduce în limbaj comun.
- **`santier_materiale_comenzi`** — un rând per comandă: `santier_id, numar`
  (auto-generat `COM-NNN`, secvențial pe șantier), `data_comanda, data_primire`
  (nullable — necompletată = comanda nu a ajuns încă), `observatii`,
  plus `poza_path/poza_nume/poza_marime` (poză de la livrare) și
  `aviz_path/aviz_nume/aviz_marime` (avizul de expediție) — fișierele folosesc
  bucket-ul partajat `DOC_BUCKET = "santier-documente"`, același tipar ca
  `uploadJurnalPhoto`/`uploadDocFile` (path `materiale/{santierId}/{comandaId}/
  {poza|aviz}-{timestamp}-{filename}`). **NU există coloană de furnizor** —
  eliminată explicit la cererea utilizatorului (vezi mai jos); nu o reintroduce.
- **`santier_materiale_comenzi_itemi`** — tabel de legătură: o comandă poate
  conține mai multe materiale diferite (o comandă/aviz real acoperă de regulă
  mai multe tipuri de material), fiecare linie cu `comanda_id, material_id,
  cantitate`.

### Logica de avertizare (cea mai importantă regulă de business aici)

Pentru fiecare material se calculează (funcția `materialCantitati`):

- **Cantitate comandată** = suma `cantitate` din TOATE liniile de comandă ale
  acelui material, INDIFERENT dacă comanda a ajuns deja pe șantier — e o
  avertizare preventivă (depășirea bugetului de material e vizibilă chiar
  înainte ca marfa să ajungă).
- **Cantitate primită** = suma doar din liniile ale căror comenzi au
  `data_primire` completată — ACEASTA se scade efectiv din cantitatea
  prevăzută (`cantitate rămasă = prevăzută − primită`).
- **Rând roșu + badge „DEPĂȘIT”** când comandată > prevăzută; altfel badge
  verde „OK”. Această distincție comandată-vs-primită rezolvă ambiguitatea
  din cererea inițială a utilizatorului fără să fie nevoie să aleagă o
  singură interpretare — amândouă sunt utile și afișate separat.
- Statusul unei comenzi (badge „Comandat”/„Primit”) e pur derivat din
  `data_primire` fiind completată sau nu — nu există un câmp de status
  separat.

### Import din Excel ("Importă din Excel")

Buton în Listă materiale care citește un fișier `.xls`/`.xlsx` de listă de
cantități direct în browser (SheetJS, `xlsx@0.18.5`, din CDN — `<script defer>`,
aceeași convenție ca docxtemplater/pizzip/pdf-lib) și populează automat
materialele, cu o previzualizare (checkbox per rând) înainte de salvare.

**Euristică de extracție** (funcția `parseDevizMatrix`, validată pe deviz-ul
real Stăuceni — `Balanta_SIL2_completata_Stauceni.xls`, 1046 rânduri, 108
materiale reale găsite, 0 fals-pozitive pe test manual): un deviz românesc
„Borderou centralizator al situațiilor de plată cantitativ” mixează rânduri
de manoperă (operații de execuție) cu rânduri de materiale. Coloana
**„Simbol”**: valoare PUR NUMERICĂ (`/^\d+$/`) → cod real de produs/material
(SKU); valoare ALFANUMERICĂ (ex: „TSC04F1”, indicator de normă de deviz) →
operație de manoperă, se ignoră. Un material poate apărea la mai multe
poziții (același tip de țeavă folosit în secțiuni diferite ale proiectului)
— cantitatea se ADUNĂ pe cod unic, nu se ia o singură dată. Filtru adițional:
un rând cu `cantitate <= 0` se ignoră (găsit empiric un fals-pozitiv: un antet
de proiect repetat mid-sheet, cu un cod numeric întâmplător în coloana
Simbol și cantitate 0 — un material real din listă are mereu o cantitate
ofertată > 0).

### UI / convenții respectate

Subtab-urile Listă materiale/Comenzi urmează EXACT tiparul existent
`.subtabs`/`.subtab` + `state.siteForm.materialeSubTab` (ca Date șantier/
Progres Șantier). CRUD pe materiale/comenzi urmează tiparul tronsoanelor
(`addTronson`/`persistTronsonField`/`removeTronson`): rând temporar `tmp-`
afișat optimist, insert real în fundal, id-ul temporar e înlocuit la succes,
rollback vizual la eroare. Editarea unui material e explicit edit/salvează
(buton creion → rândul devine editabil → bifă salvează), nu „type-and-blur”
ca la tronsoane — tipar aprobat explicit de utilizator în mockup-ul Artifact
înainte de implementare.

**Revizuiri ulterioare, cerute explicit de utilizator după primul test în
aplicația reală (nu doar în mockup)** — toate în `comandaRowHTML`/funcțiile
`*Comanda*` din `index.html`:

- **Furnizorul a fost eliminat complet** (coloană DB + UI). În antetul
  comenzii (`.order-head`), unde era furnizorul, apare acum DENUMIREA
  primului material din comandă (`+N materiale` dacă sunt mai multe) —
  `.order-material-label`, calculat din `itemiForComanda(o.id)` +
  `matsById`, NU dintr-un câmp separat.
- **Editarea datei comenzii/primirii urmează EXACT tiparul de la Listă
  materiale** (`state.siteForm.comandaEditingId`, `startComandaEdit`/
  `saveComandaEdit`/`persistComandaDates`): câmpurile de dată sunt
  INVIZIBILE în mod normal (data e deja vizibilă, read-only, pe linia
  „Comandă / Primire” din antet) și apar editabile DOAR cât timp comanda e
  în modul de editare (creion apăsat); fără apăsarea bifei de confirmare
  (`saveComandaEdit`), modificările rămân doar în memorie (pe obiectul live
  din `materialeComenzi`, mutate direct de `input`-handler-ul pentru
  `data-comanda-field`) și NU se trimit la Supabase — de aceea NU există
  un `focusout`-persist pentru `data-comanda-field` (eliminat intenționat;
  nu-l re-adăuga, ar sparge regula „neconfirmat = nesalvat”).
- **Selectarea materialului la adăugarea unei linii în comandă e o listă de
  sugestii CUSTOM** (`.mat-search-wrap` + `.mat-suggest-list`), NU
  `<select>` și NU `<input list="...">`+`<datalist>`. Istoricul: prima
  variantă a folosit `<datalist>` nativ (ca `functii-sugestii` de la
  Pontaj) — a trecut testul automat (Chromium), dar **bug real găsit în
  producție**: utilizatorul a plasat 3 comenzi reale, niciuna n-a ajuns să
  aibă vreun material în ea (`santier_materiale_comenzi_itemi` gol, verificat
  direct în DB), pentru că `<datalist>` nu arată NICIO sugestie pe
  Safari/iOS — utilizatorul tasta, nu vedea nimic de ales, iar rezolvarea
  text→`material_id` cerea potrivire EXACTĂ pe `denumire`, deci rămânea
  goală; butonul „Adaugă” făcea un `return` tăcut, fără nicio eroare. Dublu
  fix, amândouă obligatorii la orice alt loc din app cu nevoie de căutare:
  1. Listă de sugestii randată de aplicație însăși (`div`-uri cu
     `data-comanda-item-pick="comandaId|materialId"`, deschisă la click pe
     `data-comanda-item-search-open`, închisă la alegere sau la click în
     afara ei — tipar identic cu `colorPickerOpen`), nu `<datalist>`.
  2. **`addComandaItem` nu mai face NICIODATĂ un `return` tăcut** — fără
     material ales sau fără cantitate > 0, arată `flashSyncError` cu un
     mesaj clar. O acțiune a utilizatorului care pare să reușească dar nu
     face nimic e mult mai rău decât o eroare vizibilă.
  Filtrarea listei de sugestii e LIVE (pe sub-șir, nu doar prefix) la fiecare
  literă tastată, dar handler-ul de `input` pentru
  `data-comanda-item-material-search` NU apelează `render()` (ar reconstrui
  tot `#app`, vezi comentariul din funcția `render()`, și ar fura focusul din
  input la mijlocul tastării) — patch-uiește direct nodul
  `#mat-suggest-<comandaId>` din DOM, prin `comandaItemSuggestionsListHTML()`.
  Deschiderea inițială a listei (click) TOT prin `render()` trece, pentru că
  un click e o acțiune discretă, nu tastare continuă — doar actualizările
  ulterioare, din tastare, ocolesc `render()`.
- **Runda 1 a dropdown-ului custom de mai sus (`position: absolute`) tot nu
  mergea în producție** — utilizatorul a trimis o poză reală arătând lista de
  sugestii aproape complet tăiată (doar un colț rotunjit vizibil sub bara de
  căutare), iar `santier_materiale_comenzi_itemi` rămânea gol ȘI DUPĂ acest
  prim fix. Cauza: `.mat-suggest-list` era `position: absolute` față de
  `.mat-search-wrap`, dar e cuibărit în `.items-table` ȘI `.mtable-panel`,
  care au AMÂNDOUĂ `overflow: hidden` (pus pentru colțurile lor rotunjite) —
  orice conținut poziționat absolut care depășește acea cutie e tăiat la
  randare. (Nu a reprodus identic în Chromium headless la lățimea testată
  atunci — diferă probabil cu tastatura virtuală reală de pe telefon, care
  micșorează spațiul vizibil disponibil fără ca `window.innerHeight` să
  reflecte asta pe toate browserele — dar mecanismul de tăiere la
  `overflow:hidden` e real și verificabil independent de asta.) Fix: `.mat-suggest-list`
  e acum `position: fixed`, cu `left`/`top`/`width` calculate din
  `getBoundingClientRect()` al input-ului de căutare prin `positionMatSuggestList()`
  — EXACT tiparul `.colorpop`/`.daypop` (`positionColorPopover()`/
  `positionOpenPopover()`), deja dovedit funcțional în restul aplicației,
  apelat atât din `render()` cât și direct din handler-ul de `input` (care
  ocolește `render()`, vezi mai sus). **Regula generală**: orice element
  poziționat ca popover/dropdown care poate ajunge în interiorul unui
  `.panel`/`.mtable-panel`/`.items-table` (toate cu `overflow: hidden`
  pentru colțuri rotunjite) TREBUIE să fie `position: fixed` cu poziție
  calculată din JS, NICIODATĂ `position: absolute` relativ la un ancestor
  din interiorul acelor cutii — `overflow: hidden` câștigă mereu, indiferent
  cât de sus pui `z-index`.
- **Runda 2, cauza REALĂ (confirmată, nu doar bănuită)**: utilizatorul a
  raportat A TREIA oară că materialele tot nu se contorizau în comenzi —
  DUPĂ fix-ul `position: fixed` de mai sus. În loc să ghicesc din nou dintr-o
  poză, am interogat direct log-urile proiectului Supabase
  (`mcp__Supabase__query_logs`, `source = 'edge_logs'`, filtrat după
  `comenzi_itemi`): zeci de `GET`-uri către `santier_materiale_comenzi_itemi`
  (reîncărcări de pagină), dar **NICIUN `POST`** — niciodată. Asta elimină
  orice teorie despre RLS/schema/backend și demonstrează că butonul „Adaugă”
  lovea mereu garda `if (!materialId) { flashSyncError(...); return; }`
  din `addComandaItem` — adică utilizatorul NU reușea niciodată să aleagă
  efectiv un material din listă, deși vizual (în poza trimisă) lista PĂREA
  poziționată corect. Cauza: `window.innerHeight` NU scade când se deschide
  tastatura virtuală pe majoritatea browserelor mobile (viewport-ul de
  layout rămâne fix, tastatura doar ACOPERĂ vizual partea de jos a
  ecranului) — `positionMatSuggestList()` calcula poziția o singură dată, la
  deschidere, înainte ca tastatura să termine animația de apariție, folosind
  o înălțime "fără tastatură"; o clipă mai târziu tastatura acoperea exact
  acea zonă, iar sugestiile ajungeau să stea, invizibil, SUB tastatură —
  nu puteau fi atinse, deși `position: fixed` rezolvase corect problema
  anterioară de `overflow: hidden`. Dublu fix:
  1. `window.visualViewport.height` (unde există) reflectă zona REAL
     vizibilă (exclude tastatura), spre deosebire de `window.innerHeight` —
     folosit acum ca limită de poziționare, cu un listener
     `window.visualViewport.addEventListener("resize", positionMatSuggestList)`
     înregistrat o singură dată la pornire, ca să repoziționeze lista live
     când tastatura își termină animația (nu doar la momentul inițial al
     deschiderii).
  2. Lista preferă acum să se deschidă DEASUPRA input-ului, nu dedesubt —
     tastatura acoperă mereu partea de JOS a ecranului, niciodată partea de
     sus, deci „deasupra” e structural mai sigur pentru orice dropdown legat
     de un `<input>` de text (spre deosebire de `.colorpop`/`.daypop`, care
     nu cheamă nicio tastatură și pot rămâne „dedesubt, dacă încape”).
  Plus un clamp final (`top = Math.min(top, viewportH - lh - 8)`) care NU
  are voie să lase lista să depășească zona vizibilă curentă indiferent de
  ramura aleasă mai sus — apărare suplimentară pentru cazul în care
  `r.top` al input-ului nu e încă în zona vizibilă quando se calculează
  poziția (browserul mobil derulează automat input-ul focalizat deasupra
  tastaturii, dar nu garantat înainte ca listener-ul de `resize` să ruleze).
  **Testat printr-un `visualViewport` fals**, instalat cu
  `page.addInitScript()` ÎNAINTE de navigare (ca să fie deja activ când
  codul aplicației își înregistrează propriul listener), cu o funcție
  `window.__setKeyboardOpen(bool)` care micșorează `.height` la 1/3 și
  declanșează manual callback-urile de `resize` — un `visualViewport` real
  nu poate fi micșorat la comandă dintr-un test, dar efectul unei tastaturi
  reale e identic. **Lecție pentru orice alt dropdown/popover legat de un
  `<input>` de text pe care-l mai adaugi în aplicație**: `window.innerHeight`
  NU e suficient, trebuie `window.visualViewport` + listener de `resize` +
  preferință pentru „deasupra”, nu doar `position: fixed` simplu (care
  rezolvă DOAR tăierea prin `overflow:hidden`, nu și acoperirea de
  tastatură — două bug-uri diferite, descoperite separat, în două runde).
- **Runda 3 — utilizatorul NU era pe telefon, era pe desktop browser** (a
  clarificat-o explicit abia acum) și a raportat DOUĂ simptome noi, distincte
  de tot ce era documentat mai sus:
  1. **Dropdown-ul se deschidea în SUS în loc de jos.** Normal — preferința
     „deasupra” de la runda 2 era necondiționată (presupunea mereu o
     tastatură de evitat), dar pe desktop nu există nicio tastatură virtuală
     de evitat, deci deschiderea în sus era pur și simplu greșită/surprinzătoare
     acolo. Fix: „deasupra” se aplică ACUM doar dacă există dovadă CONCRETĂ că
     o tastatură chiar acoperă ceva chiar acum (`window.innerHeight -
     window.visualViewport.height > 80`) — pe desktop diferența aia e
     întotdeauna 0, deci lista se deschide normal dedesubt, exact ca
     `.colorpop`/`.daypop`.
  2. **Nu putea scrie deloc în bara de căutare — bug real, separat, mai
     vechi decât runda 2, care exista de la introducerea dropdown-ului
     custom și nu fusese niciodată prins.** Cauza: click-ul pe
     `data-comanda-item-search-open` focalizează automat `<input>`-ul din
     interior (comportamentul implicit al browserului la click pe un câmp de
     text) — dar handler-ul de `click` din aplicație rulează apoi `render()`
     generic la finalul lanțului de `if/else`, care distruge ȘI RECONSTRUIEȘTE
     tot `#app`, inclusiv acel input proaspăt focalizat. Rezultatul: input-ul
     ARĂTA focalizat o clipă, dar tastarea nu ajungea nicăieri (focusul se
     pierduse odată cu DOM-ul vechi). Exact tiparul „a render() here would
     steal focus back off the field” documentat deja în handler-ul de
     `input` din app pentru alte câmpuri — dar NU fusese aplicat la
     deschiderea acestui dropdown. Fix: branch-ul de
     `data-comanda-item-search-open` își face acum PROPRIUL `render()`
     (nu lasă `render()`-ul generic de la final să ruleze — `needsRender =
     false`), apoi apelează explicit `.focus()` pe input-ul nou creat —
     exact tiparul deja folosit de handler-ele de `dblclick` pentru editarea
     etichetelor/celulelor (`labelInput.focus()` etc., vezi mai jos în fișier).
  **De ce testul automat nu a prins bug-ul #2 de două ori**: testul folosea
  `page.fill()` pentru bara de căutare, care forțează focus pe elementul țintă
  prin CDP, INDIFERENT de starea reală a DOM-ului paginii — deci „funcționa”
  chiar și cu bug-ul de focus prezent. Rescris să folosească `page.click()`
  (ca un click real) + `page.keyboard.type()` (care scrie DOAR în elementul
  care are ACTUALMENTE focus, exact ca o apăsare de tastă reală), plus o
  verificare explicită `document.activeElement === inputul respectiv` chiar
  după deschidere. **Lecție de testare, generală**: `page.fill()` e
  convenabil dar MASCHEAZĂ exact genul de bug „am construit un input nou dar
  am uitat să-l focalizez” — pentru orice câmp deschis dinamic (popover, rând
  nou, modal), verifică `document.activeElement` și folosește
  `keyboard.type()`, nu `fill()`, dacă vrei ca testul să conteze ceva.
- **Bug de aliniere găsit și reparat**: aplicația are o regulă GLOBALĂ
  `th, td { text-align: center }` (convenție veche, pentru alte tabele din
  app). `.mtable`/`.items-table` suprascriau explicit doar coloanele
  `.num`/`.actions` (right) — coloana de bază (`<td>` fără clasă, ex.
  Denumire/UM/Stare la Listă materiale, Material la liniile de comandă)
  MOȘTENEA centrarea globală, nu era un bug de layout nou. Fix:
  `.mtable td { text-align: left }` și `.items-table td { text-align: left }`
  explicit, cu `.num` suprascriind peste ele (right). Dacă adaugi un tabel
  nou oriunde în app, verifică explicit alinierea celulelor de bază — nu te
  baza pe default-ul browser-ului, regula globală centrată câștigă.
- **Bară de căutare la Listă materiale** (cerută explicit după ce utilizatorul
  a importat 108 materiale reale din Excel și nu mai găsea nimic cu scroll):
  `state.siteForm.materialeSearchQuery`, input cu `data-materiale-search`,
  filtrare live pe substring (case-insensitive) din `denumire`, prin
  `materialeMatchesQuery`/`materialeTbodyHTML`/`materialeCountLabelHTML`.
  Ca la căutarea din Comenzi: handler-ul de `input` NU apelează `render()`
  (ar reconstrui tot `#app` și ar fura focusul la mijlocul tastării) — în
  loc patch-uiește direct `#materiale-tbody-<siteId>` și
  `#materiale-count-<siteId>` din DOM, prin id. Capcană reală evitată
  explicit: `addMaterial` creează un rând nou cu `denumire: ""`, care NU s-ar
  potrivi niciunui filtru activ nevid — ar fi apărut invizibil, exact genul de
  „acțiune care pare să nu facă nimic" interzis explicit de regula de la
  `addComandaItem` mai sus; fix: `addMaterial` golește
  `materialeSearchQuery` înainte de `render()`, ca rândul nou (editabil) să
  fie mereu vizibil imediat. Căutarea se resetează și la navigarea către alt
  șantier (alături de celelalte câmpuri de `siteForm` legate de Materiale).

### Testare

Fără script de test commis separat (scratchpad-only, per convenția
proiectului) — dar verificat exhaustiv cu un test de integrare real
(Playwright, Chromium) pe `index.html` NEMODIFICAT, cu librăriile reale
supabase-js/xlsx (instalate local din npm, nu mock-uite): adăugare material,
editare, salvare, adăugare comandă, adăugare linie de comandă cu cantitate
care depășește prevăzutul (verificare badge „DEPĂȘIT” + rând roșu +
cantități comandată/primită/rămasă corecte), și import real din fișierul
Excel de producție Stăuceni prin UI (upload real → previzualizare → confirmă
→ 108 materiale importate, exact ca extracția validată manual). **Notă
tehnică utilă dacă se re-scrie acest test**: NU interceptați cross-origin
cu `page.route()` cererile reale către `*.supabase.co` din sandbox-uri cu
proxy — politica de rețea blochează `cdn.jsdelivr.net` ȘI
`rwxsvsqoohepcfbawfng.supabase.co` direct la proxy (403), și interceptarea
cross-origin cu `page.route()` s-a comportat inconsistent (reușea izolat,
dar pica repetabil quando combinată cu alte rute înregistrate, fără o cauză
clar identificabilă). Soluție robustă: serviți o copie same-origin a
`index.html` (doar `SUPABASE_URL` și `<script src>`-urile supabase-js/xlsx
rescrise să indice spre același server Node local), iar serverul Node însuși
joacă rolul de backend Supabase fals (rute `/rest/v1`, `/auth/v1`,
`/storage/v1` tratate direct în handler-ul HTTP) — elimină complet CORS/proxy
din ecuație.

## Workflow de deploy

Commit pe branch-ul de lucru → push → merge pe `main` → push. Bump `BUILD`
în `index.html` la fiecare schimbare de șablon/cod. Vezi istoricul de commit-uri
recente pentru exemple de mesaje de commit (în română, cu explicația cauzei
reale, nu doar "fix pagination").
