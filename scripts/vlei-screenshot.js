const { chromium, devices } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE = 'https://vlei.raafetchoukri.com';

// Sections to capture. The app is a hash-routed SPA, so we drive routing by
// setting location.hash and waiting for re-render rather than full navigation.
const SECTIONS = [
  { name: 'registry', hash: '#registry' },
  { name: 'request', hash: '#request' },
  { name: 'identity', hash: '#identity' },
  { name: 'policy', hash: '#policy' },
  { name: 'verdict', hash: '#verdict' },
  { name: 'audit', hash: '#audit' },
];

const VIEWPORTS = [
  { name: 'desktop', viewport: { width: 1440, height: 900 }, isMobile: false },
  { name: 'mobile', viewport: { width: 390, height: 844 }, isMobile: true, deviceScaleFactor: 3, userAgent: devices['iPhone 14'].userAgent },
];

const OUT = path.resolve(__dirname, '..', 'screenshots');
const LOG = path.resolve(__dirname, '..', 'console.log');
const REGISTRY_HTML = path.resolve(__dirname, '..', 'registry.html');

fs.mkdirSync(OUT, { recursive: true });
fs.writeFileSync(LOG, '');

const logLine = (line) => fs.appendFileSync(LOG, line + '\n');

(async () => {
  const browser = await chromium.launch();

  for (const vp of VIEWPORTS) {
    const context = await browser.newContext({
      viewport: vp.viewport,
      deviceScaleFactor: vp.deviceScaleFactor || 1,
      isMobile: vp.isMobile,
      hasTouch: vp.isMobile,
      userAgent: vp.userAgent,
      ignoreHTTPSErrors: true,
    });
    const page = await context.newPage();

    page.on('console', (msg) => {
      if (msg.type() === 'error' || msg.type() === 'warning') {
        logLine(`[${vp.name}] [${msg.type()}] ${msg.text()}`);
      }
    });
    page.on('pageerror', (err) => {
      logLine(`[${vp.name}] [pageerror] ${err.message}`);
    });
    page.on('requestfailed', (req) => {
      logLine(`[${vp.name}] [requestfailed] ${req.url()} - ${req.failure()?.errorText}`);
    });

    // Initial load. Go to registry first; subsequent sections just change the hash.
    const firstUrl = `${BASE}/${SECTIONS[0].hash}`;
    console.log(`[${vp.name}] loading ${firstUrl}`);
    await page.goto(firstUrl, { waitUntil: 'networkidle', timeout: 60_000 });
    await page.waitForTimeout(800);

    for (const s of SECTIONS) {
      // Hash-route by assigning location.hash, which triggers SPA route handler.
      await page.evaluate((h) => { window.location.hash = h; }, s.hash);
      // Give the SPA time to re-render and any lazy assets to load.
      try {
        await page.waitForLoadState('networkidle', { timeout: 10_000 });
      } catch (e) {
        logLine(`[${vp.name}] [info] networkidle timeout on ${s.name}`);
      }
      await page.waitForTimeout(800);

      const file = path.join(OUT, `${s.name}-${vp.name}.png`);
      await page.screenshot({ path: file, fullPage: true });
      console.log(`[${vp.name}] wrote ${file}`);

      if (s.name === 'registry' && vp.name === 'desktop') {
        const html = await page.content();
        fs.writeFileSync(REGISTRY_HTML, html);
        console.log(`wrote ${REGISTRY_HTML} (${html.length} bytes)`);
      }
    }

    await context.close();
  }

  await browser.close();
  console.log('done');
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
