import io

path = 'index.html'
src = io.open(path, encoding='utf-8').read()

# 1) Replace ALL legacy tail scripts (duplicate handlers + stub fallback) with one implementation.
marker = "<script>\n  function openDcProductModal(product) {"
start = src.index(marker)
end = src.rindex("</script>")
tail = io.open('_build/newtail.js', encoding='utf-8').read().rstrip('\n')
src = src[:start] + tail + src[end + len("</script>"):]

# 2) Rewrite the broken legacy openProductDetailModal(prodId) body as a safe delegate.
fstart = src.index("function openProductDetailModal(prodId) {")
brace = src.index("{", fstart)
depth = 0
j = brace
while j < len(src):
    if src[j] == '{':
        depth += 1
    elif src[j] == '}':
        depth -= 1
        if depth == 0:
            break
    j += 1
newfn = "function openProductDetailModal(prodId) {\n      openDcProductModalById(prodId);\n    }"
src = src[:fstart] + newfn + src[j + 1:]

# 3) Card click -> real product id through the unified handler.
old_click = "onclick=\"openProductDetailModal('${p.id}')\""
new_click = "onclick=\"openDcProductModalById('${esc(p.id)}')\""
click_replaced = src.count(old_click)
src = src.replace(old_click, new_click)

io.open(path, 'w', encoding='utf-8').write(src)
print('tail_replaced', True)
print('click_replaced', click_replaced)
print('lines', src.count('\n') + 1)
