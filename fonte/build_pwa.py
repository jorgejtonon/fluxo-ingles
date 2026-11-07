"""Gera a versão instalável (PWA) a partir de fluxo-ingles.html, a mesma fonte do artefato."""
import re, pathlib, json
root = pathlib.Path(__file__).parent  # pasta fonte/
src = (root / 'fluxo-ingles.html').read_text()
cut = src.index('<header class="top">')
head_part, body_part = src[:cut], src[cut:]
head_part = head_part.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', '')
version = __import__('hashlib').sha1(src.encode()).hexdigest()[:8]
html = f'''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#F2F5F7" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0C1620" media="(prefers-color-scheme: dark)">
<meta name="description" content="Fluxo: conversa em inglês com correção na hora, trilha do American English File 1, pronúncia, foto da atividade e revisão.">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" type="image/png" sizes="192x192" href="icons/icon-192.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Fluxo">
<style>:root{{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0;font:14px system-ui,sans-serif}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
{head_part.strip()}
</head>
<body>
{body_part.strip()}
<script>
if ('serviceWorker' in navigator && (location.protocol === 'https:' || location.hostname === 'localhost')) {{
  addEventListener('load', () => navigator.serviceWorker.register('sw.js?v={version}').catch(() => {{}}));
}}
</script>
</body>
</html>
'''
out = root.parent
(out / 'index.html').write_text(html)
manifest = {
  "name": "Fluxo Inglês", "short_name": "Fluxo", "lang": "pt-BR",
  "description": "Conversa em inglês com correção na hora, trilha do American English File 1, pronúncia, foto da atividade e revisão.",
  "start_url": "./", "scope": "./", "display": "standalone", "orientation": "portrait",
  "background_color": "#F2F5F7", "theme_color": "#132A3F",
  "icons": [
    {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
    {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
    {"src": "icons/maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}
  ]
}
(out / 'manifest.webmanifest').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
sw = f'''// Fluxo: funciona sem internet para trilha salva, revisão e pronúncia. A professora (API) precisa de internet.
const V = 'fluxo-{version}', FONTS = 'fluxo-fonts';
const SHELL = ['./', './index.html', './manifest.webmanifest', './icons/icon-192.png', './icons/icon-512.png', './icons/maskable-512.png'];
self.addEventListener('install', e => {{ e.waitUntil(caches.open(V).then(c => c.addAll(SHELL))); self.skipWaiting(); }});
self.addEventListener('activate', e => {{
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== V && k !== FONTS).map(k => caches.delete(k)))).then(() => self.clients.claim()));
}});
self.addEventListener('fetch', e => {{
  const req = e.request; if (req.method !== 'GET') return;
  const u = new URL(req.url);
  if (u.hostname === 'api.anthropic.com') return;
  if (u.origin === location.origin) {{
    if (req.mode === 'navigate' || u.pathname.endsWith('/') || u.pathname.endsWith('.html')) {{
      e.respondWith(fetch(req).then(r => {{ const cp = r.clone(); caches.open(V).then(c => c.put('./index.html', cp)); return r; }})
        .catch(() => caches.match('./index.html')));
      return;
    }}
    e.respondWith(caches.match(req, {{ignoreSearch: true}}).then(r => r || fetch(req)));
    return;
  }}
  if (/fonts\\.(googleapis|gstatic)\\.com$/.test(u.hostname)) {{
    e.respondWith(caches.match(req).then(r => r || fetch(req).then(res => {{ const cp = res.clone(); caches.open(FONTS).then(c => c.put(req, cp)); return res; }})));
  }}
}});
'''
(out / 'sw.js').write_text(sw)
(out / '.nojekyll').write_text('')
(out / 'README.md').write_text('''# Fluxo Inglês

App pessoal de conversação em inglês do Jorge Tonon: conversa com correção na hora (voz ou texto), trilha na sequência do American English File 1 com conteúdo próprio, situações com missões, pronúncia com nota por palavra, foto da atividade, diálogos e revisão espaçada.

- Abra no Chrome do Android e toque em **Instalar o app**.
- A professora usa uma chave da API da Anthropic, guardada só no aparelho (nunca neste repositório).
- O progresso fica no aparelho; use **Ajustes → Copiar backup / Restaurar** para levar a outro aparelho.

Fonte única: `fluxo-ingles.html` (a mesma do artefato no Claude). `build_pwa.py` gera esta pasta.
''')
print('built', version)
