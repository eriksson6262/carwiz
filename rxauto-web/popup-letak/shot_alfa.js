const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 794, height: 1123 }, deviceScaleFactor: 2 });
  await p.goto('file://' + process.cwd() + '/alfa.html');
  await p.waitForTimeout(800);
  await p.screenshot({ path: 'alfa.png', clip: { x: 0, y: 0, width: 794, height: 1123 } });
  await b.close();
})();
