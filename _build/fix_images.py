#!/usr/bin/env python3
"""Targeted DealCart product-image fix. Fails loudly and writes nothing if source moved."""
import sys

PATH = 'index.html'
src = open(PATH, encoding='utf-8').read()
orig_len = len(src)


def rep(old, new, count=1, label=''):
    global src
    found = src.count(old)
    if found != count:
        print('FAIL [%s]: expected %d, found %d' % (label, count, found))
        sys.exit(1)
    src = src.replace(old, new)
    print('OK   [%s] x%d' % (label, count))


# 1) Robust normalisation + multi-column resolver. Placeholders are never treated as photos.
OLD_NORM = r"""    const normalizeImages = value => {
      let list = [];
      if (Array.isArray(value)) {
        list = value;
      } else {
        const str = String(value ?? '').trim();
        if (str) {
          const parts = str.split(',').map(s => s.trim()).filter(Boolean);
          list = (parts.length > 1 && parts.every(u => /^https?:\/\//i.test(u))) ? parts : [str];
        }
      }
      const valid = list.map(x => String(x || '').trim()).filter(Boolean);
      return valid.length ? valid : [DC_PLACEHOLDER_IMG];
    };"""

NEW_NORM = r"""    // A placeholder or branded artwork is never a real product photo: such values are ignored so a
    // genuine image further down the list still wins and a logo can never masquerade as a photo.
    const isPlaceholderImage = url => /placehold\.co|placeholder\.com|via\.placeholder|text=DealCart|no[+_ -]?image/i.test(String(url || ''));
    const isImageUrl = url => {
      const s = String(url || '').trim();
      if (!s || isPlaceholderImage(s)) return false;
      if (/^data:image\//i.test(s)) return true;
      if (/^(https?:)?\/\//i.test(s)) return true;
      return /^[\w./~%-]+\.(png|jpe?g|webp|gif|avif|svg)(\?.*)?$/i.test(s);
    };
    // Accepts arrays, JSON arrays, comma/pipe/newline lists, {url} objects and single URLs.
    // A comma is only treated as a separator when every piece is itself a usable image URL.
    const normalizeImages = value => {
      let list = [];
      if (Array.isArray(value)) {
        list = value;
      } else {
        const str = String(value ?? '').trim();
        if (str) {
          if (/^\[.*\]$/.test(str)) {
            try {
              const parsed = JSON.parse(str);
              if (Array.isArray(parsed)) list = parsed;
            } catch (e) { list = []; }
          }
          if (!list.length) {
            const parts = str.split(/[,\n|]+/).map(x => x.trim()).filter(Boolean);
            list = (parts.length > 1 && parts.every(isImageUrl)) ? parts : [str];
          }
        }
      }
      const seen = Object.create(null);
      const valid = list
        .map(x => (x && typeof x === 'object') ? String(x.url || x.src || x.image || x.image_url || '') : String(x == null ? '' : x))
        .map(x => x.trim())
        .filter(isImageUrl)
        .filter(u => (seen[u] ? false : (seen[u] = true)));
      return valid.length ? valid : [DC_PLACEHOLDER_IMG];
    };
    // Reads every image column DealCart / Supabase may carry, in priority order.
    const resolveProductImages = product => {
      const p = product || {};
      const candidates = [];
      const push = v => { if (v !== undefined && v !== null && String(v).trim() !== '') candidates.push(v); };
      push(p.images); push(p.image_urls); push(p['Image URLs']); push(p.image_url);
      push(p['Image URL']); push(p.image); push(p.thumbnail); push(p.thumb); push(p.photo);
      for (let i = 1; i <= 6; i++) push(p['Product Image ' + i]);
      for (let i = 0; i < candidates.length; i++) {
        const list = normalizeImages(candidates[i]).filter(u => u !== DC_PLACEHOLDER_IMG);
        if (list.length) return list;
      }
      return [DC_PLACEHOLDER_IMG];
    };
    const productImageAt = (product, index) => {
      const list = resolveProductImages(product);
      const i = Math.max(0, Math.floor(Number(index) || 0));
      return list[Math.min(i, list.length - 1)] || DC_PLACEHOLDER_IMG;
    };"""

rep(OLD_NORM, NEW_NORM, 1, 'normalizeImages + resolveProductImages')

# 2) normalizeProduct resolves images from every known column.
rep(r"""        images: normalizeImages(raw.images ?? raw.image_url ?? raw['Image URLs'] ?? raw['Image URL'] ?? raw.image ?? raw['Product Image 1']),""",
    r"""        images: resolveProductImages(raw),""",
    1, 'normalizeProduct images')

# 3) Supabase mapper: also read images / image_urls / Image URLs.
rep(r"""                image_url: item.image_url || item['Product Image 1'] || item['Image URL'],""",
    r"""                image_url: item.image_url || item['Image URL'] || item['Product Image 1'],
                images: item.images ?? item.image_urls ?? item['Image URLs'] ?? item['Product Images'],""",
    1, 'supabase image columns')

rep(r"""                if (hasRemote(item.image_url) || hasRemote(item['Product Image 1']) || hasRemote(item['Image URL'])) patch.images = mapped.images;""",
    r"""                if (hasRemote(item.images) || hasRemote(item.image_urls) || hasRemote(item['Image URLs']) || hasRemote(item['Product Images']) || hasRemote(item.image_url) || hasRemote(item['Product Image 1']) || hasRemote(item['Image URL'])) patch.images = mapped.images;""",
    1, 'supabase images patch condition')

# 4) Product card: resolver + neutral fallback (never the branded DealCart artwork).
rep(r"""      const imageUrl = normalizeImages(p.images)[0];""",
    r"""      const imageUrl = resolveProductImages(p)[0];""",
    1, 'card image source')

rep("this.src='https://placehold.co/600x600/0A192F/D4AF37?text=DealCart';",
    "this.src='${DC_PLACEHOLDER_IMG}';",
    1, 'card onerror fallback')

# 5) Thumbnails: resolve a real URL instead of indexing a possibly-string value.
rep(r"""<img src="${esc(item.images[0])}" class="w-16 h-16""",
    r"""<img src="${esc(productImageAt(item, 0))}" class="w-16 h-16""",
    1, 'cart thumbnail')

rep(r"""<img src="${esc(it.images[0])}" class="w-10 h-10 object-contain rounded bg-slate-50 border p-0.5">""",
    r"""<img src="${esc(productImageAt(it, 0))}" class="w-10 h-10 object-contain rounded bg-slate-50 border p-0.5">""",
    1, 'order history thumbnail')

rep(r"""<img src="${esc(it.images[0])}" class="w-10 h-10 object-contain rounded bg-white border p-0.5">""",
    r"""<img src="${esc(productImageAt(it, 0))}" class="w-10 h-10 object-contain rounded bg-white border p-0.5">""",
    1, 'admin order thumbnail')

rep(r"""<img src="${esc(p.images[0])}" class="w-10 h-10 object-contain rounded bg-slate-100 border p-0.5 shrink-0">""",
    r"""<img src="${esc(productImageAt(p, 0))}" class="w-10 h-10 object-contain rounded bg-slate-100 border p-0.5 shrink-0">""",
    1, 'admin products table thumbnail')

# 6) CSV import: neutral placeholder and multi-image parsing.
rep(r"""          images: [row['image url'] || row.image || 'https://placehold.co/600x600/0A192F/D4AF37?text=DealCart'],""",
    r"""          images: normalizeImages(row['image url'] || row['image urls'] || row.image),""",
    1, 'csv import images (mode 1)')

rep(r"""          images: [row['image url'] || 'https://placehold.co/600x600/0A192F/D4AF37?text=DealCart'],""",
    r"""          images: normalizeImages(row['image url'] || row['image urls'] || row.image),""",
    1, 'csv import images (mode 2)')

# 7) Details gallery uses the same resolver so every available image is shown.
rep(r"""    var imgs = Array.isArray(product.images) ? product.images.filter(Boolean) : [];
    if (!imgs.length && product.image) imgs = [product.image];
    galleryImages = imgs.length ? imgs.map(String) : [PLACEHOLDER];""",
    r"""    var imgs = (typeof resolveProductImages === 'function') ? resolveProductImages(product) : [];
    galleryImages = imgs.length ? imgs.map(String) : [PLACEHOLDER];""",
    1, 'details gallery images')

open(PATH, 'w', encoding='utf-8').write(src)
print('\nWrote %s: %d -> %d bytes' % (PATH, orig_len, len(src)))
print('Remaining branded DealCart fallbacks: %d' % src.count('text=DealCart'))
