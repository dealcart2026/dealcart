// Verifies the REAL image helpers extracted from index.html against the value shapes that
// existing Supabase product rows actually use. Temporary check; removed after running.
import fs from 'node:fs';

const html = fs.readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const start = html.indexOf('const DC_PLACEHOLDER_IMG');
const end = html.indexOf('const genProductId');
if (start < 0 || end < 0) { console.error('EXTRACT FAILED'); process.exit(1); }
const block = html.slice(start, end);

const sandbox = { window: {}, appConfig: { supabaseUrl: 'https://mdobwluczmjtybjmdzvz.supabase.co' } };
const factory = new Function('window', 'appConfig', block + `
  return { DC_PLACEHOLDER_IMG, isPlaceholderImage, isImageUrl, toDisplayableImageUrl,
           imageValueToUrl, normalizeImages, resolveProductImages, productImageAt };
`);
const api = factory(sandbox.window, sandbox.appConfig);
const PH = api.DC_PLACEHOLDER_IMG;

let pass = 0, fail = 0;
const check = (name, got, want) => {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  if (ok) { pass++; console.log('PASS  ' + name); }
  else { fail++; console.log('FAIL  ' + name + '\n   got:  ' + JSON.stringify(got) + '\n   want: ' + JSON.stringify(want)); }
};

const U1 = 'https://images.unsplash.com/photo-1533867617858-e7b97e060509?w=800&auto=format&fit=crop&q=80';
const U2 = 'https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=800';

// 1. Existing single-image rows (array form) keep their photo.
check('array with one real photo', api.resolveProductImages({ images: [U1] }), [U1]);

// 2. Existing single-image rows stored only in image_url (the mapped Supabase column).
check('legacy image_url column', api.resolveProductImages({ image_url: U1 }), [U1]);

// 3. Supabase jsonb object shape -> publicUrl was previously dropped.
check('{publicUrl} object', api.resolveProductImages({ images: [{ publicUrl: U1 }] }), [U1]);

// 4. getPublicUrl() response shape {data:{publicUrl}}.
check('getPublicUrl response', api.resolveProductImages({ images: [{ data: { publicUrl: U2 } }] }), [U2]);

// 5. Comma-joined gallery (what the save path writes) keeps the usable entries.
check('comma list with one bad entry', api.resolveProductImages({ image_url: U1 + ',not-a-url,' + U2 }), [U1, U2]);

// 6. Genuine file whose name mentions "no image" is no longer rejected.
const NOIMG = 'https://cdn.example.com/products/no-image-saree.jpg';
check('filename containing no-image', api.resolveProductImages({ images: [NOIMG] }), [NOIMG]);

// 7. Retired branded artwork is still never shown as a product photo.
check('old DealCart artwork rejected', api.resolveProductImages({ images: ['https://placehold.co/600x600/0A192F/D4AF37?text=DealCart'] }), [PH]);

// 8. Bare Supabase Storage path completed against the EXISTING configured project.
check('storage bucket path', api.resolveProductImages({ images: ['product-images/abc123.jpg'] }),
  ['https://mdobwluczmjtybjmdzvz.supabase.co/storage/v1/object/public/product-images/abc123.jpg']);

// 9. Protocol-relative URL upgraded to https instead of resolving against the site.
check('protocol-relative url', api.resolveProductImages({ images: ['//cdn.example.com/a.jpg'] }), ['https://cdn.example.com/a.jpg']);

// 10. JSON string array column.
check('JSON string array', api.resolveProductImages({ images: JSON.stringify([U1, U2]) }), [U1, U2]);

// 11. Truly imageless product still gets the neutral placeholder.
check('no images at all', api.resolveProductImages({ name: 'x' }), [PH]);

// 12. productImageAt clamps gallery indexes.
check('productImageAt index 1', api.productImageAt({ images: [U1, U2] }, 1), U2);

console.log('\n' + pass + ' passed, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
