# Rapor Formatı — Bilal Tercihleri (24.08.2026)

## Kural
Bilal "kapsamlı rapor" veya "sistem röntgeni" istediğinde:
- **Sadece tablo/özet YETMEZ** — gerçek kod içeriği gösterilmeli
- **Her dosyanın ilk satırları** + tam dosya linki olmalı
- **HTML formatında** preview'da açılabilir şekilde üret
- **Google Drive'a yükle** — link ver, indirip tarayıcıda açsın

## Format Şablonu
Rapor = tablolar + kod blokları + dosya linkleri (üçü bir arada)

```html
<h2>Dosya Adı</h2>
<div class="section">
<pre>{dosya_icerigi}</pre>
<p><a href="file:///path/to/file">Tam dosya</a></p>
</div>
```

## Hata Örneği
Sadece tablolarla "22 KB rapor" üretmek → Bilal "kodları göremedim" dedi.

## Doğru Yaklaşım
`read_file` ile dosya içeriklerini HTML'e göm, `<pre>` bloklarında sun.
