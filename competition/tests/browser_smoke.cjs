// Optional real-browser smoke test. Dependencies are installed only under the
// ignored competition/.cache/browser directory, never added to the root app.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createRequire } = require('node:module');
const local = createRequire(path.resolve(__dirname, '../.cache/browser/package.json'));
const { chromium } = local('playwright-core');
const runtime = local('@sparticuz/chromium');
const lambda = runtime.default || runtime;
const root = path.resolve(__dirname, '..');
const base = process.env.BROWSER_BASE_URL || 'http://127.0.0.1:8816/';
let activeBrowser;
(async () => {
  // Use the browser package's bundled NSS libraries in this minimal sandbox.
  const { pathToFileURL } = require('node:url');
  const buildDir = path.dirname(local.resolve('@sparticuz/chromium'));
  const { inflate } = await import(pathToFileURL(path.join(buildDir,'lambdafs.js')).href);
  const libRoot = await inflate(path.resolve(buildDir,'../bin/al2023.tar.br'));
  const env = {...process.env, LD_LIBRARY_PATH:path.join(libRoot,'lib') + ':' + (process.env.LD_LIBRARY_PATH || ''), FONTCONFIG_PATH:path.join(require('node:os').tmpdir(),'fonts')};
  const args = lambda.args.filter(a => !['--single-process','--disable-web-security','--allow-running-insecure-content'].includes(a));
  const browser = await chromium.launch({executablePath:await lambda.executablePath(),args,env,headless:true});
  activeBrowser = browser;
  const errors = [];
  const pages = fs.readdirSync(root).filter(p => p.endsWith('.html')).sort();
  const results = [];
  for (const [device,viewport] of [['desktop',{width:1440,height:1000}],['mobile',{width:390,height:844}],['small-mobile',{width:320,height:740}]]) {
    const context = await browser.newContext({viewport});
    const page = await context.newPage();
    page.on('pageerror', e => errors.push(`${device}: ${e.message}`));
    page.on('console', m => {if(m.type()==='error') errors.push(`${device}: ${m.text()}`);});
    page.on('requestfailed', r => errors.push(`${device}: ${r.url()} ${r.failure()?.errorText}`));
    for (const file of pages) {
      const response = await page.goto(new URL(file,base).href);
      assert.equal(response.status(),200,file);
      assert.equal(await page.locator('h1').count(),1,file);
      assert.ok(await page.locator('h1').isVisible(),file);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1),false,`${device}: body overflow on ${file}`);
      assert.equal(await page.locator('a[target="_blank"]:not([rel~="noopener"])').count(),0,file);
      results.push({device,page:file,status:'PASS'});
    }
    await page.goto(new URL('singles.html',base).href);
    await page.locator('#prices input').fill('LV');
    assert.equal(await page.locator('#prices tbody tr:visible').count(),1,'market filter');
    await page.locator('#prices input').fill('no-such-fixture');
    assert.equal(await page.locator('#prices tbody tr:visible').count(),0,'empty filter');
    assert.ok(await page.locator('#prices .table-empty').isVisible(),'empty state');
    await page.locator('#prices input').fill('');
    assert.equal(await page.locator('#prices tbody tr:visible').count(),15,'clear filter');
    await page.locator('#baseline button[data-column="1"]').click();
    let values = await page.locator('#baseline tbody tr td:nth-child(2)').allTextContents();
    values = values.map(Number);
    assert.deepEqual(values,[...values].sort((a,b)=>a-b),'numeric ascending sort');
    await page.locator('#baseline button[data-column="1"]').click();
    values = (await page.locator('#baseline tbody tr td:nth-child(2)').allTextContents()).map(Number);
    assert.deepEqual(values,[...values].sort((a,b)=>b-a),'numeric descending sort');
    await page.goto(new URL('leaderboard.html',base).href);
    assert.equal(await page.locator('#board tbody tr').count(),8,'catalog size');
    assert.ok(await page.locator('#board tbody').evaluate(t => Array.from(t.rows).every(r => [3,4,5,6,7].every(i => r.cells[i].textContent === ''))),'unknown performance must be blank');
    await page.goto(new URL('player-props.html',base).href);
    assert.ok(await page.locator('#prop-quotes tbody').evaluate(t => Array.from(t.rows).every(r => [3,4,5].every(i => r.cells[i].textContent === ''))),'ambiguous props stay blank');
    await page.goto(new URL('index.html',base).href);
    if(device!=='desktop') {
      const toggle = page.locator('.menu-toggle');
      await toggle.click();
      assert.equal(await toggle.getAttribute('aria-expanded'),'true');
      assert.ok(await page.locator('.sidebar').isVisible(),'mobile menu open');
      await page.keyboard.press('Escape');
      assert.equal(await toggle.getAttribute('aria-expanded'),'false');
      assert.equal(await page.locator('.sidebar').isVisible(),false,'mobile escape closes menu');
      await toggle.click();
      await page.locator('.sidebar a[href="singles.html"]').click();
      assert.ok(await page.locator('h1').filter({hasText:'Single bets'}).isVisible(),'mobile navigation');
      await page.goto(new URL('index.html',base).href);
    }
    await page.screenshot({path:path.join(root,`.cache/${device}.png`),fullPage:true});
    await context.close();
  }
  assert.deepEqual(errors,[],'browser errors');
  const version = browser.version();
  await browser.close();
  const report = {status:'PASS',browser:`Chromium ${version}`,playwright:local('playwright-core/package.json').version,viewports:['1440×1000','390×844','320×740'],pages_checked:results.length,checks:['200 responses','one visible h1','no horizontal body overflow','safe external targets','filter / clear / empty state','numeric ascending/descending sort','unknown performance blank','unknown prop quotes blank','mobile menu / Escape / navigation','no page/console/request errors'],external_publisher_http_checked:false,results};
  fs.writeFileSync(path.join(root,'results/browser-check.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({...report,results:undefined},null,2));
})().catch(async error => {console.error(error); if(activeBrowser) await activeBrowser.close().catch(()=>{}); process.exitCode=1;});
