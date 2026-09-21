---
name: app-theme-design
description: >
  How to design, preview, and apply a color theme (or a variation of one —
  different shadow intensity, contrast, saturation, density, or a light/dark
  mode) for Ing. Assistant (the construction-site app in this repo). Use
  this skill whenever the user asks for new theme options, a different color
  palette, a light/dark version, "mai multe optiuni" for the app's look, or
  wants to see variations of a theme they already picked — even if they
  don't name colors or say "CSS". Always preview candidate themes as a
  realistic mockup BEFORE touching ing-assistant/index.html, and never apply
  a theme to the live app without the user having picked it from a preview
  first. Also use this skill before adding or changing a light/dark switch,
  since the localStorage timing bug documented here is easy to reintroduce.
---

# Design de teme pentru Ing. Assistant

## Regula de bază: preview înainte de aplicare

Utilizatorul nu a acceptat niciodată o temă "pe cuvânt" — a vrut mereu s-o
vadă randată pe un ecran real al aplicației înainte să decidă. Nu sări peste
pasul de preview, chiar dacă cererea pare mică ("mai fă o variantă").

1. Publică un artifact HTML cu 1 sau mai multe opțiuni, fiecare aplicată pe
   un mockup fidel al aplicației (sidebar cu șantiere, dashboard cu
   statistici, carduri de șantier, un tabel de tronsoane) — NU doar niște
   dreptunghiuri colorate. Reutilizează conținut real din aplicație (nume de
   șantiere, coduri de tronson CD/CM/CR, terminologia din interfață), ca
   utilizatorul să vadă exact cum arată, nu doar culori izolate.
2. Dacă sunt mai multe opțiuni, fă-le comutabile live (click pe o cartelă →
   tot mockup-ul se re-colorează instant) — nu publica 5 artifacts separate.
3. Publică artifactul (`Artifact` tool), deschide-l pentru utilizator, și
   commit-ul fișierului sursă `.html` în repo (utilizatorul cere asta prin
   hook-ul de git status — vezi mai jos).
4. Așteaptă alegerea explicită înainte de a atinge `index.html`.

## Structura tokens-urilor CSS din `index.html`

Aplicația folosește un singur bloc `:root { --bg: ...; --surface: ...; }`
etc. Variabilele semnificative (vezi `ing-assistant/index.html`, aproape de
începutul `<style>`):

```
--bg, --surface, --surface-2, --border, --border-strong
--ink, --ink-soft, --ink-faint
--navy, --navy-hover, --navy-soft         (accentul principal — link-uri,
                                            buton primar, tab activ, focus)
--amber, --amber-soft, --amber-strong     (semantic: avertisment)
--green, --green-soft                     (semantic: succes/activ/finalizat)
--red, --red-soft                         (semantic: eroare/pericol)
--gray-soft, --blue-soft, --purple-soft   (paleta de 6 culori din selectorul
                                            de culori al tabelului de progres
                                            — nu sunt legate de accentul temei)
```

Culorile semantice (amber/green/red) trebuie să rămână **distincte** de
accent — dacă accentul e portocaliu, nu folosi și amber portocaliu, altfel
"în lucru" (warn) și butonul principal se confundă vizual.

## Capcana #1: culori hardcodate care nu folosesc `var(--...)`

Când schimbi accentul, un `grep` pentru variabile NU e suficient — verifică
și valorile hardcodate legate de accentul VECHI, care rămân "pete" de
culoare greșită după schimbarea temei:

```bash
grep -n "box-shadow\|background: #\|background:rgba(" ing-assistant/index.html
```

Locuri unde s-a găsit deja acest bug (verifică-le din nou de fiecare dată,
sunt tentante de uitat): gradientul de fundal al `body`, glow-ul de pe
`.brand-mark`/`.login-mark`, umbra de pe `.card:hover`, gradientul
`.btn-primary`, umbra `.nav-item.active`, `.bulk-bar`, `.modal-card`,
`.login-card`. Fiecare din astea trebuie fie mutat pe `var(--navy)` /
`rgba()` recalculat pentru noul accent, fie — dacă tema nouă e "fără umbre"
(flat) — eliminat complet, nu doar recolorat.

## Capcana #2: elemente care rămân colorate fix, indiferent de temă

Câteva componente au folosit culori fixe (nu variabile) pentru că, pe vremea
când aplicația era mereu întunecată, "fix și întunecat" arăta identic cu
"folosește --surface". Asta se vede abia când adaugi un mod luminos:
`.thumb` (fundalul thumbnail-ului de pe cardul de șantier) și `.card-del`
(butonul de ștergere de pe el) foloseau `rgba(21,24,28,...)` — un negru fix,
rămas dintr-o eră veche a temei — ceea ce arăta ca un bloc negru rupt de
restul cardului odată ce cardul din jur a devenit alb. Fixul a fost simplu:
`var(--surface-2)` în loc de negru fix. Verifică orice `rgba(NN,NN,NN,` cu
numere mici (fundal închis) rămas hardcodat — dacă tema poate deveni
deschisă, componenta aia trebuie să se adapteze.

## Comutator luminos/întunecat (dacă se cere)

Tiparul stabilit (nu prefers-color-scheme — alegerea e mereu explicită,
salvată de utilizator, niciodată dedusă din sistem):

- Bloc CSS suplimentar `:root[data-theme="light"] { --bg: ...; ... }` care
  suprascrie tokens-urile din `:root`. Adaugă și
  `:root[data-theme="light"] { color-scheme: light; }` lângă
  `:root { color-scheme: dark; }`, ca și controalele native (scrollbar,
  date picker) să urmeze tema.
- Accentul din varianta deschisă NU e aceeași nuanță ca cea întunecată —
  dacă accentul e folosit și ca TEXT (link-uri, tab activ), varianta "plină"
  deseori nu trece testul de contrast AA pe alb. Coboară-l (ex. portocaliu
  plin `#ff7a29` → ars `#d9600f` pe fundal deschis) până arată corect.
- **Bug-ul de reținut**: `state.theme` se inițializează în interiorul
  obiectului `state = {...}`, care rulează ÎNAINTE ca orice `var X = "...";`
  de mai jos în fișier să fi fost asignat (hoisting-ul lui `var` ridică doar
  declarația, nu valoarea). Dacă funcția care citește din `localStorage`
  folosește o cheie dintr-un asemenea `var` extern, ea citește `undefined`
  la încărcarea inițială — alegerea se SALVEAZĂ corect (funcția de toggle
  rulează mai târziu, după ce `var`-ul e deja asignat) dar nu se mai
  CITEȘTE corect la refresh. Fix: pune string-ul cheii direct, literal, în
  ambele funcții (citire și scriere), nu într-un `var` distanțat de ele.
- Aplică tema imediat după ce `state` există (înainte de primul `render()`),
  ca pagina să nu clipească greșit la încărcare.
- Adaugă switch-ul într-un loc vizibil din bara laterală (lângă "Setări"),
  cu iconițe sun/moon — vezi implementarea curentă din `index.html` ca
  model direct de copiat (caută `data-toggle-theme`).

## Verificare înainte de deploy

1. Screenshot Playwright pe dashboard (`Șantiere`) și pe detaliul unui
   șantier, în ambele teme dacă există comutator — folosește
   `scripts/screenshot_app.js` din acest skill ca punct de plecare (mock
   Supabase inclus, generic pentru orice ecran al aplicației).
2. Dacă există comutator: verifică explicit că `data-theme` rămâne corect
   DUPĂ `page.reload()`, nu doar imediat după click — exact acolo a fost
   prins bug-ul de mai sus.
3. Rulează suita completă de regresie (11 teste — vezi `CLAUDE.md`).
4. Bump `BUILD` în `index.html`, commit cu mesaj care explică schimbarea de
   design (nu doar "update theme"), push pe branch → merge pe `main` → push.
