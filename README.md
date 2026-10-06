# Ajans web sitesi

Ajansın kendi sitesinin prototipi. GitHub Pages ile yayında.

## Nasıl güncellenir

- Sayfa gövdesi: `src/site.html`
- SEO/GEO ayarları (tek karar noktası): `seo/config.json` — başlık, açıklama, canonical, indekslenme, schema, sık sorulanlar küpü, footer hizmetleri, `robots.txt`, `sitemap.xml`, `llms.txt`
- Üret: `python3 tools/build.py` → `index.html`, `404.html`, `robots.txt`, `sitemap.xml`, `llms.txt`, `llms-full.txt`

Standart: icerik-vault `02-Websites/_kutuphane/seo-geo/00-seo-geo-standardi.md`.

## Notlar

- Site, ad ve alan adı netleşene kadar `indexable: false` (noindex). Netleşince `config.json`'da `brand`, `brand_display`, `site_url`, `title`, `indexable: true` güncellenir ve build alınır.
- Sitedeki görünen marka adı `src/site.html` içindeki `CONFIG = { BRAND: "sayfa" }` satırından gelir.
- İletişim formu henüz bir e-postaya bağlı değil.
- Kütüphaneler CDN'den: GSAP, Three.js, Matter.js, Lenis.
