# -*- coding: utf-8 -*-
import io
import re

path = 'index.html'
src = io.open(path, encoding='utf-8').read()
report = []


def rep(old, new, label, count=1):
    global src
    found = src.count(old)
    if found != count:
        report.append('MISS %s (found %d, expected %d)' % (label, found, count))
        return False
    src = src.replace(old, new)
    report.append('OK   %s' % label)
    return True


# ---------- F1: admin products table ReferenceError (price -> p.price) ----------
rep(
    '            <div class="font-black text-brand-navy">${ru(price)}</div>\n'
    '            <div class="text-[10px] text-slate-400">Wholesale: ${ru(p.wholesaleCost || 0)}</div>',
    '            <div class="font-black text-brand-navy">${ru(p.price)}</div>\n'
    '            <div class="text-[10px] text-slate-400">Wholesale: ${ru(p.wholesaleCost || 0)}</div>',
    'admin products table price')

# ---------- F2: dashboard supplier dues + honest profit ----------
rep(
    "      let totalWholesale = 0;\n"
    "      let totalSupplierDues = 0;\n"
    "      orders.forEach(o => {\n"
    "        if (o.orderStatus !== 'Cancelled') {\n"
    "          o.items.forEach(it => {\n"
    "            totalWholesale += (it.wholesaleCost || 0) * it.qty;\n"
    "          });\n"
    "        }\n"
    "      });\n"
    "\n"
    "      const totalRecordedExpenses = expenses.reduce((s, e) => s + e.amount, 0);\n"
    "      const estimatedProfit = Math.max(0, totalSales - totalWholesale - totalRecordedExpenses);",
    "      let totalWholesale = 0;\n"
    "      let totalSupplierDues = 0;\n"
    "      orders.forEach(o => {\n"
    "        if (o.orderStatus !== 'Cancelled') {\n"
    "          (o.items || []).forEach(it => {\n"
    "            const lineWholesale = (it.wholesaleCost || 0) * (it.qty || 0);\n"
    "            totalWholesale += lineWholesale;\n"
    "            const linkedProduct = products.find(p => String(p.id) === String(it.id));\n"
    "            const isSupplierItem = !!it.supplierId || (linkedProduct && linkedProduct.productType === 'SUPPLIER');\n"
    "            if (isSupplierItem) {\n"
    "              const ledger = (o.supplierOrders || []).find(s => String(s.productId) === String(it.id));\n"
    "              if (!ledger || !ledger.supplierPaid) totalSupplierDues += lineWholesale;\n"
    "            }\n"
    "          });\n"
    "        }\n"
    "      });\n"
    "\n"
    "      const totalRecordedExpenses = expenses.reduce((s, e) => s + e.amount, 0);\n"
    "      // Real profit: a genuine loss must stay visible instead of being floored at zero.\n"
    "      const estimatedProfit = totalSales - totalWholesale - totalRecordedExpenses;",
    'dashboard dues + profit')

# ---------- F3: checkout validation (phone / pincode) ----------
rep(
    '      if (!name || phone.length < 10 || !pin || !house || !street) {\n'
    '        showToast("Please fill all required delivery fields", false);\n'
    '        return;\n'
    '      }',
    '      const phoneDigits = String(phone || \'\').replace(/\\D/g, \'\');\n'
    '      if (!name || !phone || !pin || !house || !street) {\n'
    '        showToast("Please fill all required delivery fields", false);\n'
    '        return;\n'
    '      }\n'
    '      if (!/^[6-9]\\d{9}$/.test(phoneDigits.slice(-10)) || phoneDigits.length < 10) {\n'
    '        showToast("Please enter a valid 10-digit mobile number", false);\n'
    '        return;\n'
    '      }\n'
    '      if (!/^\\d{6}$/.test(String(pin))) {\n'
    '        showToast("Please enter a valid 6-digit pincode", false);\n'
    '        return;\n'
    '      }',
    'checkout phone + pincode validation')

# ---------- F4: UTR validation + stock check before the order is created ----------
rep(
    '      // Build Order Object\n'
    '      const orderObj = {',
    '      if (selectedPayMethod !== \'COD\' && !/^[A-Za-z0-9]{6,30}$/.test(String(utr || \'\'))) {\n'
    '        showToast("Please enter a valid UTR / transaction reference (6-30 letters or digits)", false);\n'
    '        return;\n'
    '      }\n'
    '\n'
    '      // Refuse the order when requested quantity exceeds available stock.\n'
    '      const stockShortfall = cart.find(item => {\n'
    '        const prod = products.find(p => String(p.id) === String(item.id));\n'
    '        if (!prod) return true;\n'
    '        const available = Math.max(0, Math.floor(Number(prod.stock) || 0));\n'
    '        return available < Math.max(1, Math.floor(Number(item.qty) || 1));\n'
    '      });\n'
    '      if (stockShortfall) {\n'
    '        showToast("Not enough stock available for " + (stockShortfall.name || "this product"), false);\n'
    '        return;\n'
    '      }\n'
    '\n'
    '      // Build Order Object\n'
    '      const orderObj = {',
    'UTR + pre-order stock check')

# ---------- F5: decrement stock after the order is persisted ----------
rep(
    "      // 1. Save to Local Persistence\n"
    "      orders.unshift(orderObj);\n"
    "      localStorage.setItem(STORAGE_KEYS.ORDERS, JSON.stringify(orders));",
    "      // 1. Save to Local Persistence\n"
    "      orders.unshift(orderObj);\n"
    "      localStorage.setItem(STORAGE_KEYS.ORDERS, JSON.stringify(orders));\n"
    "\n"
    "      // 1b. Reduce stock by the ordered quantity. Existing stock values are only decreased,\n"
    "      // never reset, and never allowed to go below zero.\n"
    "      orderObj.items.forEach(item => {\n"
    "        const prod = products.find(p => String(p.id) === String(item.id));\n"
    "        if (!prod) return;\n"
    "        const qty = Math.max(0, Math.floor(Number(item.qty) || 0));\n"
    "        if (qty <= 0) return;\n"
    "        prod.stock = Math.max(0, Math.floor(Number(prod.stock) || 0) - qty);\n"
    "      });\n"
    "      localStorage.setItem(STORAGE_KEYS.PRODUCTS, JSON.stringify(products));",
    'stock decrement on order')

# ---------- F6: surface Supabase order write errors ----------
rep(
    "          await client.from('orders').insert([{",
    "          const { error: orderSyncError } = await client.from('orders').insert([{",
    'order insert error capture')
rep(
    "            created_at: timestamp\n"
    "          }]);\n"
    "        } catch (e) {\n"
    '          console.log("Supabase order sync logged locally:", e);\n'
    "        }",
    "            created_at: timestamp\n"
    "          }]);\n"
    "          if (orderSyncError) {\n"
    "            console.error('Supabase order sync failed:', orderSyncError);\n"
    "            showToast('Order saved locally, but cloud sync failed: ' + (orderSyncError.message || 'unknown error'), false);\n"
    "          }\n"
    "        } catch (e) {\n"
    '          console.error("Supabase order sync failed:", e);\n'
    "          showToast('Order saved locally, but cloud sync failed.', false);\n"
    "        }",
    'order insert error surface')

# ---------- F7: multi-image save + surface Supabase product write errors ----------
rep(
    "          await client.from('products').upsert([{",
    "          const { error: productSyncError } = await client.from('products').upsert([{",
    'product upsert error capture')
rep(
    "            image_url: productObj.images[0],",
    "            // All gallery images travel in the existing image_url column (comma separated URLs),\n"
    "            // so no schema change is needed and existing single-image rows stay readable.\n"
    "            image_url: (productObj.images || []).filter(Boolean).join(',') || productObj.images[0],",
    'multi-image save')
rep(
    "        } catch (e) {\n"
    "          console.log('Supabase product sync logged locally:', e);\n"
    "        }",
    "          if (productSyncError) {\n"
    "            console.error('Supabase product sync failed:', productSyncError);\n"
    "            showToast('Product saved locally, but cloud sync failed: ' + (productSyncError.message || 'unknown error'), false);\n"
    "          }\n"
    "        } catch (e) {\n"
    "          console.error('Supabase product sync failed:', e);\n"
    "          showToast('Product saved locally, but cloud sync failed.', false);\n"
    "        }",
    'product upsert error surface')

# ---------- F8: remote merge must not overwrite fields the remote row does not have ----------
rep(
    "              if (existingIndex >= 0) {\n"
    "                // Supabase is the shared catalog source: refresh the existing local copy instead of leaving stale price/status/image data.\n"
    "                products[existingIndex] = { ...products[existingIndex], ...mapped };\n"
    "              } else {",
    "              if (existingIndex >= 0) {\n"
    "                // Only fields that the remote row actually supplies are refreshed. A column that is\n"
    "                // missing remotely must never be replaced by a local default (0 / placeholder image).\n"
    "                const hasRemote = v => v !== undefined && v !== null && String(v).trim() !== '';\n"
    "                const patch = {};\n"
    "                if (hasRemote(item.name) || hasRemote(item.title) || hasRemote(item['Product Name'])) patch.name = mapped.name;\n"
    "                if (hasRemote(item.category)) patch.category = mapped.category;\n"
    "                if (hasRemote(item.price) || hasRemote(item['Price']) || hasRemote(item['Selling Price'])) patch.price = mapped.price;\n"
    "                if (hasRemote(item.mrp) || hasRemote(item.MRP) || hasRemote(item['Compare at Price'])) patch.mrp = mapped.mrp;\n"
    "                if (hasRemote(item.wholesale) || hasRemote(item['Wholesale Price'])) patch.wholesaleCost = mapped.wholesaleCost;\n"
    "                if (hasRemote(item.stock)) patch.stock = mapped.stock;\n"
    "                if (hasRemote(item.image_url) || hasRemote(item['Product Image 1']) || hasRemote(item['Image URL'])) patch.images = mapped.images;\n"
    "                if (hasRemote(item.description)) patch.description = mapped.description;\n"
    "                if (item.cod !== undefined && item.cod !== null) patch.cod = mapped.cod;\n"
    "                if (hasRemote(item.status)) patch.status = mapped.status;\n"
    "                if (hasRemote(item.productType)) patch.productType = mapped.productType;\n"
    "                if (hasRemote(item.supplierId)) patch.supplierId = mapped.supplierId;\n"
    "                if (hasRemote(item.rating)) patch.rating = mapped.rating;\n"
    "                if (hasRemote(item.ratingCount)) patch.ratingCount = mapped.ratingCount;\n"
    "                products[existingIndex] = { ...products[existingIndex], ...patch };\n"
    "              } else {",
    'remote merge no-clobber')

# ---------- F9: WhatsApp number normalisation helper ----------
rep(
    "    const ru = n => '₹' + parseMoney(n).toLocaleString('en-IN', { maximumFractionDigits: 2 });",
    "    const ru = n => '₹' + parseMoney(n).toLocaleString('en-IN', { maximumFractionDigits: 2 });\n"
    "    // Normalises an Indian number to wa.me format without ever double-prefixing 91.\n"
    "    const waNumber = phone => {\n"
    "      const digits = String(phone || '').replace(/\\D/g, '');\n"
    "      if (!digits) return '';\n"
    "      if (digits.length > 10) return digits;\n"
    "      return '91' + digits.slice(-10);\n"
    "    };",
    'waNumber helper')

rep(
    "      supWa.href = `https://wa.me/91${appConfig.sellerPhone.replace(/\\D/g,'')}?text=${waMsg}`;",
    "      supWa.href = `https://wa.me/${waNumber(appConfig.sellerPhone)}?text=${waMsg}`;",
    'support whatsapp link')

rep(
    "                <a href=\"https://wa.me/91${appConfig.sellerPhone.replace(/\\D/g,'')}?text=${encodeURIComponent('Inquiry regarding Order #' + ord.id)}\"",
    "                <a href=\"https://wa.me/${waNumber(appConfig.sellerPhone)}?text=${encodeURIComponent('Inquiry regarding Order #' + ord.id)}\"",
    'order whatsapp link')

rep(
    "                        <a href=\"https://wa.me/91${sup.phone.replace(/\\D/g,'')}?text=",
    "                        <a href=\"https://wa.me/${waNumber(sup.phone)}?text=",
    'supplier whatsapp link')

# ---------- F10: search source + discount sort ----------
rep(
    "      const query = ($('desktopSearchInput').value || $('mobileSearchInput').value || '').trim().toLowerCase();",
    "      const desktopQuery = ($('desktopSearchInput').value || '').trim();\n"
    "      const mobileQuery = ($('mobileSearchInput').value || '').trim();\n"
    "      // Whichever search box the customer actually typed in wins; a stale value in the other\n"
    "      // box must never override it.\n"
    "      const query = ((window.__dcLastSearch === 'mobileSearchInput'\n"
    "        ? (mobileQuery || desktopQuery)\n"
    "        : (desktopQuery || mobileQuery)) || '').toLowerCase();",
    'search input source')

rep(
    "      else if (sort === 'DISCOUNT') list.sort((a,b) => ((b.mrp - b.price)/b.mrp) - ((a.mrp - a.price)/a.mrp));",
    "      else if (sort === 'DISCOUNT') {\n"
    "        const discountRatio = p => (p.mrp > 0 && p.mrp > p.price) ? (p.mrp - p.price) / p.mrp : 0;\n"
    "        list.sort((a, b) => discountRatio(b) - discountRatio(a));\n"
    "      }",
    'discount sort NaN')

# ---------- F11: CSV review row money parsing + duplicate detection ----------
rep(
    "        const name = r['product name'] || r.title || 'Untitled';\n"
    "        const price = r['selling price'] || r.price || 0;\n"
    "        const wholesale = r['wholesale price'] || r.wholesale || 0;\n"
    "        const img = r['image url'] || r.image || '';\n"
    "        const isDuplicate = products.some(p => p.sku.toLowerCase() === sku.toLowerCase());",
    "        const name = r['product name'] || r.title || 'Untitled';\n"
    "        const price = parseMoney(r['selling price'] || r.price || '');\n"
    "        const priceInvalid = !(Number.isFinite(price) && price > 0);\n"
    "        const wholesale = parseMoney(r['wholesale price'] || r.wholesale || '');\n"
    "        const img = r['image url'] || r.image || '';\n"
    "        const nameKey = String(name).trim().toLowerCase();\n"
    "        const isDuplicate = products.some(p =>\n"
    "          String(p.sku || '').toLowerCase() === String(sku || '').toLowerCase() ||\n"
    "          String(p.name || '').trim().toLowerCase() === nameKey);",
    'csv review price + duplicate')

rep(
    "              ${isDuplicate ? '<span class=\"text-rose-600 font-bold bg-rose-50 px-1 rounded\">⚠️ Duplicate SKU</span>' : '<span class=\"text-green-700 font-bold\">✓ Ready</span>'}",
    "              ${isDuplicate ? '<span class=\"text-rose-600 font-bold bg-rose-50 px-1 rounded\">⚠️ Duplicate Product</span>' : (priceInvalid ? '<span class=\"text-rose-600 font-bold bg-rose-50 px-1 rounded\">⚠️ Invalid Price</span>' : '<span class=\"text-green-700 font-bold\">✓ Ready</span>')}",
    'csv review status cell')

# ---------- F12: CSV import executors use parseMoney instead of Number() ----------
before = src
src = re.sub(
    r"Number\((\w+)\['selling price'\]\s*\|\|\s*\1\.price\s*\|\|\s*0\)",
    r"parseMoney(\1['selling price'] || \1.price)",
    src)
src = re.sub(
    r"Number\((\w+)\['wholesale price'\]\s*\|\|\s*\1\.wholesale\s*\|\|\s*0\)",
    r"parseMoney(\1['wholesale price'] || \1.wholesale)",
    src)
report.append('OK   csv executor money parsing' if src != before else 'MISS csv executor money parsing')

# ---------- F13: SKU duplicate guard when saving a product ----------
rep(
    "      const sku = $('editProdSku').value.trim();",
    "      const sku = $('editProdSku').value.trim();\n"
    "      if (sku && products.some(p => String(p.sku || '').toLowerCase() === sku.toLowerCase() && String(p.id) !== String(id))) {\n"
    "        showToast('SKU ' + sku + ' is already used by another product. Please use a unique SKU.', false);\n"
    "        return;\n"
    "      }",
    'sku duplicate guard')

# ---------- F14: resilient boot (no blank app when crypto/subtle is unavailable) ----------
rep(
    "    window.addEventListener('DOMContentLoaded', async () => {\n"
    "      await initAdminSecurity();\n"
    "      setupPwaManifest();\n"
    "      await loadInitialData();\n"
    "      populateFilterCategoriesDropdown();\n"
    "      renderHomeView();",
    "    window.addEventListener('DOMContentLoaded', async () => {\n"
    "      try {\n"
    "        await initAdminSecurity();\n"
    "      } catch (e) {\n"
    "        console.warn('Admin security init skipped:', e);\n"
    "      }\n"
    "      try {\n"
    "        setupPwaManifest();\n"
    "        await loadInitialData();\n"
    "      } catch (e) {\n"
    "        console.warn('Initial data load error:', e);\n"
    "      }\n"
    "      populateFilterCategoriesDropdown();\n"
    "      renderHomeView();",
    'resilient boot')

# ---------- F15: remember which search box was typed in ----------
rep(
    "  var wrapEl = byId('dcModalImgWrap');",
    "  ['desktopSearchInput', 'mobileSearchInput'].forEach(function (id) {\n"
    "    var el = byId(id);\n"
    "    if (el) el.addEventListener('input', function () { window.__dcLastSearch = id; });\n"
    "  });\n"
    "\n"
    "  var wrapEl = byId('dcModalImgWrap');",
    'search input tracker')

io.open(path, 'w', encoding='utf-8').write(src)
print('\n'.join(report))
print('lines', src.count('\n') + 1)
