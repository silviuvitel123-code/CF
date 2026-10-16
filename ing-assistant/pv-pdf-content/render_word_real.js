#!/usr/bin/env node
// Randare REALA a unui sablon pv-<cat>.docx cu docxtemplater/pizzip reale
// (nu mock-uite), cu date de productie Stauceni -- pasul 1 din regenerarea
// gap-urilor masurate pentru motorul PDF (vezi "Generare PV ca PDF" in
// CLAUDE.md). Rulare:
//
//   npm install pizzip docxtemplater playwright
//   node render_word_real.js <categorie> <numarPV>
//   soffice --headless --convert-to pdf word_real_<categorie>.docx
//   python3 measure_gaps.py <categorie> ../templates/pv-<categorie>.docx \
//       word_real_<categorie>.pdf ../pv-pdf-content/<categorie>.json
//
// (numarPV = TRONSON_PV_COUNT[categorie] din index.html: cd/cm/cr=12, el=7,
// rz/sp=8, im=6). Scrie word_real_<categorie>.docx langa acest script.
const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');

const HERE = __dirname;
const CAT = process.argv[2];
const PV_COUNT = parseInt(process.argv[3], 10);
if (!CAT || !PV_COUNT) { console.error('usage: node render_word_real.js <categorie> <numarPV>'); process.exit(1); }
const TEMPLATE = path.join(HERE, '..', 'templates', 'pv-' + CAT + '.docx');
const OUT = path.join(HERE, 'word_real_' + CAT + '.docx');

(async () => {
  const server = http.createServer((req, res) => {
    const urlPath = req.url.split('?')[0];
    const filePath = path.join(HERE, urlPath === '/' ? '/blank.html' : urlPath);
    fs.readFile(filePath, (err, data) => {
      if (err) { res.writeHead(404); res.end('not found'); return; }
      const ext = path.extname(filePath);
      const mime = { '.html': 'text/html', '.js': 'application/javascript' };
      res.writeHead(200, { 'Content-Type': mime[ext] || 'application/octet-stream' });
      res.end(data);
    });
  });
  fs.writeFileSync(path.join(HERE, 'blank.html'), '<!doctype html><html><body></body></html>');
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const port = server.address().port;
  const base = 'http://127.0.0.1:' + port;

  const browser = await chromium.launch();
  const page = await browser.newPage();
  page.on('pageerror', e => console.log('PAGE ERROR:', e.message));
  await page.goto(base + '/blank.html');
  await page.addScriptTag({ path: path.join(HERE, 'node_modules', 'pizzip', 'dist', 'pizzip.min.js') });
  await page.addScriptTag({ path: path.join(HERE, 'node_modules', 'docxtemplater', 'build', 'docxtemplater.min.js') });

  const templateB64 = fs.readFileSync(TEMPLATE).toString('base64');
  // Date reale de productie, santierul Stauceni -- vezi CLAUDE.md.
  const data = {
    locatie: "Stăuceni", obiectiv: "MODERNIZARE ȘI EXTINDERE REȚEA DE ALIMENTARE CU APĂ ȘI CANALIZARE ÎN COMUNA STĂUCENI, JUDEȚUL BOTOȘANI",
    autorizatie_nr: "56", autorizatie_data: "21.05.2025",
    proiect_nr: "1805/2024", proiectant_companie: "S.C. CONALID S.R.L", proiectant_reprezentant: "Dragoș Cojocaru",
    diriginte_nume: "Apetrei Cătălin", diriginte_autorizatie: "00028425 din 15.11.2013", diriginte_domenii: "6, 3.3",
    rte_nume: "Daniliuc Corneliu Vicentiu", rte_atestat: "00000503 / 04.10.2017", rte_domenii: "9.1; 1.1; 6.2; 8.2",
    constructor_reprezentant: "Vițel Silviu",
    tronson_cod: "CD5", specificatie_conducta: "PEHD PN10, De 110 mm",
    reper_start: "Pct 42 / CV6.1", reper_end: "Pct 29 / SPAU 3", lungime: "386",
    planse: "2, PB5, PB6", profil_longitudinal: "PL5"
  };
  for (let i = 1; i <= PV_COUNT; i++) data['numar_pv_' + i] = i;

  const outB64 = await page.evaluate(({ templateB64, data }) => {
    return new Promise((resolve, reject) => {
      const bin = atob(templateB64);
      const bytes = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
      const zip = new PizZip(bytes);
      const DocxCtor = window.docxtemplater || window.Docxtemplater;
      const doc = new DocxCtor(zip, { paragraphLoop: true, linebreaks: true });
      try { doc.render(data); } catch (e) { reject(new Error('render failed: ' + JSON.stringify(e.properties || e.message))); return; }
      const outBuf = doc.getZip().generate({ type: 'arraybuffer' });
      const outBytes = new Uint8Array(outBuf);
      let bin2 = '';
      for (let i = 0; i < outBytes.length; i++) bin2 += String.fromCharCode(outBytes[i]);
      resolve(btoa(bin2));
    });
  }, { templateB64, data });

  fs.writeFileSync(OUT, Buffer.from(outB64, 'base64'));
  console.log('wrote', OUT);

  await browser.close();
  server.close();
})().catch(err => {
  console.error('FAILED:', err.message);
  process.exit(1);
});
