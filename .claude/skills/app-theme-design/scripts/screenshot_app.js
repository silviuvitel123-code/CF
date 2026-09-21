#!/usr/bin/env node
/**
 * Generic screenshot helper for Ing. Assistant theme work.
 *
 * Serves ing-assistant/ locally with a mocked Supabase client (no real
 * network/auth needed), opens the Șantiere dashboard and a site detail
 * page, and saves screenshots. If a theme toggle selector is given, it also
 * clicks it, screenshots the result, then RELOADS the page and screenshots
 * again — that reload is the important part: it's what catches a theme
 * choice that saves correctly but doesn't read back correctly (see the
 * localStorage-timing bug documented in this skill's SKILL.md).
 *
 * Usage:
 *   node screenshot_app.js --root /path/to/ing-assistant --out /path/to/outdir [--toggle "[data-toggle-theme]"]
 */
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
function argVal(flag, fallback) {
  const i = args.indexOf(flag);
  return i !== -1 ? args[i + 1] : fallback;
}
const ROOT = path.resolve(argVal('--root', '.'));
const OUT = path.resolve(argVal('--out', '.'));
const TOGGLE_SELECTOR = argVal('--toggle', null);
const MIME = { '.html': 'text/html', '.js': 'application/javascript' };

const MOCK_SUPABASE_JS = `
window.__db = {
  muncitori: [], pontaj_intrari: [],
  santiere: [
    { id: "site1", nume: "Stăuceni", nume_scurt: "Stauceni", adresa: "Botoșani", status: "Activ",
      progres_coloane_order: null, progres_randuri_order: null, progres_merges: null, created_at: "2024-01-01" },
    { id: "site2", nume: "Roman, Str. Victoriei", nume_scurt: "Roman", adresa: "Neamț", status: "Finalizat",
      progres_coloane_order: null, progres_randuri_order: null, progres_merges: null, created_at: "2024-01-01" }
  ],
  santier_documente: [], santier_progres_coloane: [], santier_progres_randuri: [],
  santier_pv_date: [], santier_tronsoane: [
    { id: "t1", santier_id: "site1", categorie: "cd", cod: "CD5", specificatie_conducta: "PEHD-RC, PN 10, DN110", reper_start: "CVa2", reper_end: "H7", lungime: "348", planse: "PB9", profil_longitudinal: "PL8", ordine: 0 }
  ],
  companie: [{ id: 1, nume: "Cornell's Floor SRL", cod_fiscal: "RO123" }]
};
function makeQuery(table) {
  var filters = [];
  function filterRows() { var rows = window.__db[table]; if (!filters.length) return rows; return rows.filter(function (r) { return filters.every(function (f) { return r[f[0]] === f[1]; }); }); }
  var q = {
    select: function () { return q; }, order: function () { return q; },
    eq: function (col, val) { filters.push([col, val]); return q; },
    single: function () { return Promise.resolve({ data: filterRows()[0], error: null }); },
    upsert: function () { return Promise.resolve({ error: null }); },
    insert: function () { return { select: function () { return { single: function () { return Promise.resolve({ data: {}, error: null }); } }; }, then: function (r) { r({ error: null }); } }; },
    update: function () { return { eq: function () { return Promise.resolve({ error: null }); } }; },
    delete: function () { return { eq: function () { return Promise.resolve({ error: null }); } }; },
    then: function (resolve) { resolve({ data: filterRows().slice(), error: null }); }
  };
  return q;
}
window.supabase = { createClient: function () { return {
  auth: { getSession: function () { return Promise.resolve({ data: { session: { user: { email: "test@test.com" } } } }); }, signOut: function () { return Promise.resolve({}); } },
  from: function (table) { return makeQuery(table); }
}; } };
`;

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const server = http.createServer(function (req, res) {
    var urlPath = req.url.split('?')[0];
    if (urlPath === '/') urlPath = '/index.html';
    var filePath = path.join(ROOT, urlPath);
    fs.readFile(filePath, function (err, data) {
      if (err) { res.writeHead(404); res.end(); return; }
      var ext = path.extname(filePath);
      res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
      res.end(data);
    });
  });
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const port = server.address().port;
  const base = 'http://127.0.0.1:' + port;

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 940 } });
  await page.route('**/*', route => {
    const url = route.request().url();
    if (url.includes('supabase-js@2') || url.includes('/npm/motion@') || url.includes('/npm/pizzip@') || url.includes('/npm/docxtemplater@')) route.fulfill({ status: 200, contentType: 'application/javascript', body: '/* mocked */' });
    else if (url.includes('fonts.googleapis.com') || url.includes('fonts.gstatic.com')) route.fulfill({ status: 200, contentType: 'text/css', body: '' });
    else route.continue();
  });
  await page.addInitScript(MOCK_SUPABASE_JS);
  await page.goto(base + '/index.html');
  await page.waitForTimeout(400);
  await page.click('[data-go="sites"]');
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(OUT, '1_dashboard.png') });

  await page.click('[data-open-site="site1"]');
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(OUT, '2_site_detail.png') });

  if (TOGGLE_SELECTOR) {
    await page.click('[data-go="sites"]');
    await page.waitForTimeout(200);
    await page.click(TOGGLE_SELECTOR);
    await page.waitForTimeout(300);
    await page.screenshot({ path: path.join(OUT, '3_after_toggle.png') });

    // The important check: reload and confirm the choice actually persisted
    // (see the localStorage-timing bug in this skill's SKILL.md).
    await page.reload();
    await page.waitForTimeout(300);
    const themeAfterReload = await page.evaluate(() => document.documentElement.getAttribute('data-theme'));
    console.log('data-theme after reload:', themeAfterReload);
    await page.screenshot({ path: path.join(OUT, '4_after_reload.png') });
  }

  await browser.close();
  server.close();
  console.log('Screenshots saved to', OUT);
})();
