<script>
/* =========================================================================
   UNIFIED PRODUCT DETAIL + IMAGE GALLERY  (single implementation)
   Replaces the previous duplicate handlers / synthetic fallback stubs.
   ========================================================================= */
(function () {
  var PLACEHOLDER = (typeof DC_PLACEHOLDER_IMG === 'string' && DC_PLACEHOLDER_IMG) ? DC_PLACEHOLDER_IMG : 'https://placehold.co/600x600/F1F5F9/64748B?text=No+Image+Available';
  var galleryImages = [];
  var galleryIndex = 0;
  var currentProductId = null;
  var touchStartX = null;
  var touchStartY = null;

  function byId(id) { return document.getElementById(id); }
  function escAttr(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  function allProducts() {
    try { if (typeof products !== 'undefined' && Array.isArray(products)) return products; } catch (e) {}
    return [];
  }
  function findProduct(id) {
    if (id === null || id === undefined || id === '') return null;
    var key = String(id);
    return allProducts().filter(function (p) { return p && String(p.id) === key; })[0] || null;
  }
  function setText(id, value) {
    var el = byId(id);
    if (el) el.textContent = value == null ? '' : String(value);
  }
  function money(v) {
    try { return ru(v); } catch (e) { return '\u20b9' + Number(v || 0); }
  }
  function stockOf(p) {
    var raw = (typeof parseMoney === 'function') ? parseMoney(p.stock) : Number(p.stock) || 0;
    return Math.max(0, Math.floor(raw));
  }

  function renderGallery() {
    var wrap = byId('dcModalThumbnails');
    var multi = galleryImages.length > 1;
    if (wrap) {
      if (!multi) {
        wrap.innerHTML = '';
        wrap.classList.add('hidden');
      } else {
        wrap.classList.remove('hidden');
        wrap.innerHTML = galleryImages.map(function (src, i) {
          var active = i === galleryIndex ? 'border-brand-gold' : 'border-slate-200';
          return '<button type="button" onclick="dcGallerySelect(' + i + ')" aria-label="Image ' + (i + 1) + '" class="shrink-0 w-16 h-16 rounded-xl overflow-hidden border-2 ' + active + ' bg-slate-50">' +
            '<img src="' + escAttr(src) + '" alt="View ' + (i + 1) + '" class="w-full h-full object-cover" onerror="this.onerror=null;this.src=\'' + PLACEHOLDER + '\'">' +
            '</button>';
        }).join('');
      }
    }
    var prev = byId('dcModalPrevBtn');
    var next = byId('dcModalNextBtn');
    if (prev) prev.classList.toggle('hidden', !multi);
    if (next) next.classList.toggle('hidden', !multi);
    var counter = byId('dcModalImgCounter');
    if (counter) {
      counter.textContent = multi ? (galleryIndex + 1) + ' / ' + galleryImages.length : '';
      counter.classList.toggle('hidden', !multi);
    }
  }

  function showImage(index) {
    if (!galleryImages.length) return;
    var n = galleryImages.length;
    galleryIndex = ((index % n) + n) % n;
    var main = byId('dcModalMainImg');
    if (main) {
      main.onerror = function () { main.onerror = null; main.src = PLACEHOLDER; };
      main.src = galleryImages[galleryIndex] || PLACEHOLDER;
    }
    renderGallery();
  }

  function openProduct(product) {
    if (!product) return false;
    currentProductId = String(product.id == null ? '' : product.id);

    var imgs = Array.isArray(product.images) ? product.images.filter(Boolean) : [];
    if (!imgs.length && product.image) imgs = [product.image];
    galleryImages = imgs.length ? imgs.map(String) : [PLACEHOLDER];
    galleryIndex = 0;

    var price = (typeof parseMoney === 'function') ? parseMoney(product.price) : Number(product.price) || 0;
    var mrp = (typeof parseMoney === 'function') ? parseMoney(product.mrp) : Number(product.mrp) || 0;
    var stock = stockOf(product);
    var hasMrp = mrp > price;
    var off = hasMrp ? Math.round(((mrp - price) / mrp) * 100) : 0;

    setText('dcModalCategory', product.category || 'Product');
    setText('dcModalTitle', product.name || 'Product');
    setText('dcModalPrice', money(price));

    var mrpEl = byId('dcModalMrp');
    if (mrpEl) {
      mrpEl.textContent = hasMrp ? money(mrp) : '';
      mrpEl.classList.toggle('hidden', !hasMrp);
    }
    var discEl = byId('dcModalDiscount');
    if (discEl) {
      discEl.textContent = off > 0 ? off + '% OFF' : '';
      discEl.classList.toggle('hidden', off <= 0);
    }
    var stockEl = byId('dcModalStock');
    if (stockEl) {
      stockEl.textContent = stock > 0 ? ('In Stock \u00b7 ' + stock + ' left') : 'Out of Stock';
      stockEl.className = 'inline-block text-[10px] font-extrabold uppercase tracking-wider px-2.5 py-1 rounded-full ' +
        (stock > 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700');
    }

    var desc = (product.description == null ? '' : String(product.description)).trim();
    setText('dcModalDesc', desc || 'No description available for this product.');

    var atb = byId('dcModalAddToBagBtn');
    var buy = byId('dcModalBuyNowBtn');
    [atb, buy].forEach(function (btn) {
      if (!btn) return;
      btn.disabled = stock <= 0;
      btn.classList.toggle('opacity-50', stock <= 0);
      btn.classList.toggle('pointer-events-none', stock <= 0);
    });

    showImage(0);

    var modal = byId('dcProductDetailModal');
    if (modal) {
      modal.classList.remove('hidden');
      modal.classList.add('flex');
    }
    document.body.classList.add('overflow-hidden');
    return true;
  }

  function closeProduct() {
    var modal = byId('dcProductDetailModal');
    if (modal) {
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }
    document.body.classList.remove('overflow-hidden');
    currentProductId = null;
    touchStartX = null;
    touchStartY = null;
  }

  function requireProduct() {
    var p = findProduct(currentProductId);
    if (!p) {
      try { showToast('Product not found. Please refresh and try again.', false); } catch (e) {}
      return null;
    }
    return p;
  }

  window.openDcProductModalById = function (id) {
    var p = findProduct(id);
    if (!p) {
      try { showToast('Product not found. Please refresh and try again.', false); } catch (e) {}
      return;
    }
    openProduct(p);
  };
  window.openDcProductModal = function (productOrId) {
    if (productOrId && typeof productOrId === 'object') { openProduct(productOrId); return; }
    window.openDcProductModalById(productOrId);
  };
  window.closeDcProductModal = closeProduct;
  window.dcGalleryStep = function (delta) { showImage(galleryIndex + (delta || 0)); };
  window.dcGallerySelect = function (index) { showImage(index); };

  window.dcModalAddToBag = function () {
    var p = requireProduct();
    if (!p) return;
    if (stockOf(p) <= 0) {
      try { showToast('This product is out of stock', false); } catch (e) {}
      return;
    }
    if (typeof addToBag === 'function') addToBag(p.id, 1);
    closeProduct();
  };

  window.dcModalBuyNow = function () {
    var p = requireProduct();
    if (!p) return;
    if (stockOf(p) <= 0) {
      try { showToast('This product is out of stock', false); } catch (e) {}
      return;
    }
    if (typeof addToBag === 'function') addToBag(p.id, 1);
    closeProduct();
    try { if (typeof navigateTo === 'function') navigateTo('checkout'); } catch (e) {}
  };

  var wrapEl = byId('dcModalImgWrap');
  if (wrapEl) {
    wrapEl.addEventListener('touchstart', function (e) {
      if (!e.touches || e.touches.length !== 1) return;
      touchStartX = e.touches[0].clientX;
      touchStartY = e.touches[0].clientY;
    }, { passive: true });
    wrapEl.addEventListener('touchend', function (e) {
      if (touchStartX === null || !e.changedTouches || !e.changedTouches.length) return;
      var dx = e.changedTouches[0].clientX - touchStartX;
      var dy = e.changedTouches[0].clientY - touchStartY;
      touchStartX = null;
      touchStartY = null;
      if (Math.abs(dx) < 40 || Math.abs(dx) < Math.abs(dy)) return;
      showImage(galleryIndex + (dx < 0 ? 1 : -1));
    }, { passive: true });
  }
  document.addEventListener('keydown', function (e) {
    var modal = byId('dcProductDetailModal');
    if (!modal || modal.classList.contains('hidden')) return;
    if (e.key === 'Escape') closeProduct();
    else if (e.key === 'ArrowLeft') showImage(galleryIndex - 1);
    else if (e.key === 'ArrowRight') showImage(galleryIndex + 1);
  });
  var modalEl = byId('dcProductDetailModal');
  if (modalEl) {
    modalEl.addEventListener('click', function (e) {
      if (e.target === modalEl) closeProduct();
    });
  }
})();
</script>
