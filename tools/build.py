#!/usr/bin/env python3
"""Siteyi tek kaynaktan üretir.

Girdi:  src/site.html (sayfa gövdesi), seo/config.json (SEO/GEO tek karar noktası)
Çıktı:  index.html, 404.html, robots.txt, sitemap.xml, llms.txt, llms-full.txt, acilis.html

Kullanım: python3 tools/build.py
"""
import html, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
C = json.loads((ROOT / "seo/config.json").read_text(encoding="utf-8"))
UNKNOWN = "❓"
known = lambda v: bool(v) and UNKNOWN not in str(v)
esc = lambda t: html.escape(t, quote=True)

# --- kurallar: standarttaki uzunluk sınırları ---
errors = []
if len(C["title"]) > 60: errors.append(f"title {len(C['title'])} karakter (≤60)")
if len(C["description"]) > 155: errors.append(f"description {len(C['description'])} karakter (≤155)")
if errors: sys.exit("SEO kuralı: " + "; ".join(errors))

URL = C["site_url"]
ORG = URL + "#organization"
robots = "index,follow,max-image-preview:large" if C["indexable"] else "noindex,follow"

# --- JSON-LD: tek @graph, yalnız sayfada görünen ve doğrulanmış bilgi ---
org = {"@type": "Organization", "@id": ORG, "name": C["brand_display"], "url": URL,
       "logo": URL + "logo.png", "image": URL + "og.png", "description": C["summary"],
       "knowsAbout": [s["ad"] for s in C["services"]],
       "hasOfferCatalog": {"@type": "OfferCatalog", "name": "Hizmetler", "itemListElement": [
           {"@type": "OfferCatalog", "name": s["ad"], "itemListElement": [
               {"@type": "Offer", "itemOffered": {"@type": "Service", "name": i, "provider": {"@id": ORG}}} for i in s["items"]]}
           for s in C["services"]]}}
if known(C.get("legal_name")): org["legalName"] = C["legal_name"]
if known(C.get("email")): org["email"] = C["email"]
if known(C.get("phone")): org["telephone"] = C["phone"]
if C.get("same_as"): org["sameAs"] = C["same_as"]
graph = [
    org,
    {"@type": "WebSite", "@id": URL + "#website", "name": C["brand_display"], "url": URL, "inLanguage": C["lang"], "publisher": {"@id": ORG}},
    {"@type": "WebPage", "@id": URL + "#webpage", "url": URL, "name": C["title"], "description": C["description"],
     "isPartOf": {"@id": URL + "#website"}, "about": {"@id": ORG}, "inLanguage": C["lang"], "dateModified": C["date_modified"],
     "primaryImageOfPage": URL + "og.png"},
    {"@type": "FAQPage", "@id": URL + "#faq", "isPartOf": {"@id": URL + "#webpage"},
     "mainEntity": [{"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in C["faq"]]},
]
ld = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

head = f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(C["title"])}</title>
<meta name="description" content="{esc(C["description"])}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{URL}">
<meta name="theme-color" content="#F6F2EC">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<meta property="og:type" content="website">
<meta property="og:locale" content="tr_TR">
<meta property="og:site_name" content="{esc(C["brand_display"])}">
<meta property="og:title" content="{esc(C["title"])}">
<meta property="og:description" content="{esc(C["description"])}">
<meta property="og:url" content="{URL}">
<meta property="og:image" content="{URL}og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{ld}</script>
<style>:root{{color-scheme:light}}body{{margin:0}}[hidden]{{display:none!important}}img{{max-width:100%}}</style>
</head>
<body>
"""

# --- gövde: SSS küpü ve footer hizmetleri aynı kaynaktan ---
body = (ROOT / "src/site.html").read_text(encoding="utf-8")
n = len(C["faq"])
faces = "".join(
    f'<div class="fc f{i}" aria-hidden="{"false" if i == 0 else "true"}"><small>Soru {i + 1} / {n}</small><h3>{esc(f["q"])}</h3><p>{esc(f["a"])}</p>'
    + ('<a href="#iletisim" class="fq-more">Sorunuz burada yok mu? Yazın</a>' if i == n - 1 else "") + "</div>"
    for i, f in enumerate(C["faq"]))
services = "".join(f'<a href="#hizmetler">{esc(s["ad"])}</a>' for s in C["services"])
def fill(src, key, val):
    pat = re.compile(rf"<!--seo:{key}-->.*?<!--/seo:{key}-->", re.S)
    if not pat.search(src): sys.exit(f"işaret bulunamadı: seo:{key}")
    return pat.sub(lambda m: f"<!--seo:{key}-->{val}<!--/seo:{key}-->", src)
body = fill(body, "faq", faces)
body = fill(body, "services", services)
(ROOT / "src/site.html").write_text(body, encoding="utf-8")  # kaynak da güncel kalsın
(ROOT / "index.html").write_text(head + body + "\n</body>\n</html>\n", encoding="utf-8")

# --- 404: gerçek 404, noindex, canonical ve schema yok ---
(ROOT / "404.html").write_text(f"""<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sayfa bulunamadı | {esc(C["brand_display"])}</title><meta name="robots" content="noindex">
<style>body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#F6F2EC;color:#2A2433;font:16px/1.5 system-ui,sans-serif;text-align:center}}
h1{{font:italic 500 44px/1.1 Georgia,serif;color:#4E2A4A;margin:0 0 10px}}a{{display:inline-block;margin-top:18px;padding:12px 22px;border-radius:999px;color:#4E2A4A;text-decoration:none;font-weight:600;background:linear-gradient(115deg,#FBE3EA,#EEDDF6 50%,#DFE7FB)}}</style>
</head><body><main><h1>Bu sayfa burada yok.</h1><p>Aradığınız adres taşınmış ya da hiç var olmamış olabilir.</p><a href="{URL}">Ana sayfaya dönün</a></main></body></html>
""", encoding="utf-8")

# --- robots ve sitemap ---
(ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {URL}sitemap.xml\n", encoding="utf-8")
(ROOT / "sitemap.xml").write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
  <url><loc>{URL}</loc><lastmod>{C["date_modified"]}</lastmod><image:image><image:loc>{URL}og.png</image:loc><image:title>{esc(C["title"])}</image:title></image:image></url>
</urlset>
""", encoding="utf-8")

# --- llms.txt ve llms-full.txt (AI arama botları için) ---
contact = [f"- {k}: {C[k]}" for k in ("location", "email", "phone") if known(C.get(k))]
llms = [f"# {C['brand_display']}", "", f"> {C['summary']}", "", f"Resmi adı: {C['legal_name'] if known(C.get('legal_name')) else C['brand_display']}", f"Web: {URL}", ""]
if contact: llms += ["## İletişim", *contact, ""]
llms += ["## Hizmetler", *[f"- {s['ad']}: {', '.join(s['items'][:4])}" for s in C["services"]], "", "## Sayfalar", f"- [Ana sayfa]({URL})", f"- [İletişim]({URL}#iletisim)", f"- [Tam metin]({URL}llms-full.txt)", ""]
(ROOT / "llms.txt").write_text("\n".join(llms), encoding="utf-8")
full = [f"# {C['brand_display']}", "", C["summary"], "", f"Web: {URL}", f"Son güncelleme: {C['date_modified']}", ""]
if contact: full += ["## İletişim", *contact, ""]
full += ["## Hizmetler", ""]
for s in C["services"]: full += [f"### {s['ad']}", *[f"- {i}" for i in s["items"]], ""]
full += ["## Sık sorulan sorular", ""]
for f in C["faq"]: full += [f"### {f['q']}", f["a"], ""]
(ROOT / "llms-full.txt").write_text("\n".join(full), encoding="utf-8")

# --- eski deneme adresi: ana sayfaya yönlendir ---
(ROOT / "acilis.html").write_text(f"""<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="robots" content="noindex"><link rel="canonical" href="{URL}"><meta http-equiv="refresh" content="0; url=./"><title>{esc(C["brand_display"])}</title></head><body><a href="./">Ana sayfa</a></body></html>
""", encoding="utf-8")

print(f"tamam · title {len(C['title'])}/60 · description {len(C['description'])}/155 · robots {robots} · SSS {n} · hizmet {len(C['services'])}")
