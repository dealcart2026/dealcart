// Focused check: multi-image gallery (thumbnail strip + switching) on the deployed app.
// Seeds a second image into localStorage of an isolated browser only - no Supabase or user data is touched.
const { chromium } = require('/opt/appjet/browser/node_modules/playwright');

const TARGET = process.env.DC_URL || 'https://zuxsqlrh4p.dev.ap-jt.com/';

(async () => {
  const out = { url: TARGET, errors: [] };
  const browser = await chromium.launch({
    executablePath: '/opt/appjet/browser-binaries/chromium-1234/chrome-linux64/chrome',
    args: ['--no-sandbox', '--disable-dev-shm-usage']
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  page.on('pageerror', e => out.errors.push('pageerror: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') out.errors.push('console: ' + m.text()); });

  await page.goto(TARGET, { waitUntil: 'networkidle', timeout: 45000 });
  await page.waitForSelector('#trendingGrid div.group img', { timeout: 30000 });

  // 1. Do cards show real photos, or the branded DealCart artwork?
  out.cards = await page.evaluate(() => {
    const imgs = Array.from(document.querySelectorAll('#trendingGrid div.group img'));
    return {
      total: imgs.length,
      realPhotoLoaded: imgs.filter(i => /images\.unsplash\.com/.test(i.currentSrc || i.src) && i.naturalWidth > 0).length,
      placeholder: imgs.filter(i => /placehold\.co/.test(i.currentSrc || i.src)).length,
      brandedDealCart: imgs.filter(i => /text=DealCart/.test(i.currentSrc || i.src)).length
    };
  });

  // 2. Give the first product two real images (localStorage only)
  const seeded = await page.evaluate(() => {
    const KEY = 'dealcart_v2_products';
    const list = JSON.parse(localStorage.getItem(KEY) || '[]');
    if (!list.length) return { ok: false, reason: 'no products in localStorage' };
    const urls = [];
    for (let i = 0; i < list.length && urls.length < 2; i++) {
      const raw = list[i].images;
      const arr = Array.isArray(raw) ? raw : [raw];
      for (let j = 0; j < arr.length; j++) {
        const u = String(arr[j] || '');
        if (/^https?:\/\//.test(u) && urls.indexOf(u) === -1) urls.push(u);
      }
    }
    if (urls.length < 2) return { ok: false, reason: 'need two distinct image urls' };
    list[0].images = [urls[0], urls[1]];
    localStorage.setItem(KEY, JSON.stringify(list));
    return { ok: true, id: list[0].id, name: list[0].name, images: list[0].images };
  });
  out.seed = seeded;
  if (!seeded.ok) { await browser.close(); console.log(JSON.stringify(out, null, 2)); process.exit(1); }

  // 3. Reload and open that product's details
  await page.reload({ waitUntil: 'networkidle', timeout: 45000 });
  await page.waitForSelector('#trendingGrid div.group img', { timeout: 30000 });
  await page.click('#trendingGrid div.group:first-of-type img');
  await page.waitForSelector('#dcModalMainImg', { timeout: 15000 });
  await page.waitForTimeout(400);

  const mainSrc = () => page.evaluate(() => {
    const m = document.getElementById('dcModalMainImg');
    return m.currentSrc || m.src;
  });

  out.gallery = await page.evaluate(() => {
    const wrap = document.getElementById('dcModalThumbnails');
    return {
      thumbCount: document.querySelectorAll('#dcModalThumbnails img').length,
      thumbsVisible: wrap ? !wrap.classList.contains('hidden') : false,
      prevVisible: !document.getElementById('dcModalPrevBtn').classList.contains('hidden'),
      nextVisible: !document.getElementById('dcModalNextBtn').classList.contains('hidden'),
      counter: (document.getElementById('dcModalImgCounter') || {}).textContent || ''
    };
  });

  // 4. Second thumbnail switches the main image
  const before = await mainSrc();
  await page.click('#dcModalThumbnails img:nth-child(2)');
  await page.waitForTimeout(600);
  const afterThumb = await mainSrc();

  // 5. Arrow also steps the gallery
  await page.click('#dcModalNextBtn');
  await page.waitForTimeout(600);
  const afterArrow = await mainSrc();

  out.switching = {
    before: before.slice(0, 80),
    afterThumb: afterThumb.slice(0, 80),
    afterArrow: afterArrow.slice(0, 80),
    thumbChangedMain: before !== afterThumb,
    thumbMatchesSecondImage: afterThumb === seeded.images[1],
    arrowChangedMain: afterArrow !== afterThumb
  };

  await browser.close();
  console.log(JSON.stringify(out, null, 2));
})().catch(e => { console.log('FATAL ' + e.message); process.exit(1); });
