# Plugin & Worker Marketplace — Dinamik Genişleme
> **v1.0 SPEC | Jeff 3.0 Faz 5**

---

## 1. Business Case

Yeni bir worker eklemek için Hermes profil ayarlarına girmek gerekiyor. 
Marketplace ile tek komutla yeni bir worker kurulabilir, kaldırılabilir, güncellenebilir.

---

## 2. Dosya Yapısı

```
marketplace/
├── workers/                 ← Hazır worker tanımları
├── plugins/                 ← Hazır plugin tanımları
├── install.sh               ← Kurulum script'i
└── registry.json            ← Yüklü bileşenler
```

## 3. İşlemler

| İşlem | Açıklama |
|-------|----------|
| `install` | Worker/plugin kur |
| `update` | Güncelle |
| `remove` | Kaldır |
| `rollback` | Önceki sürüme dön |
| `version` | Sürüm kontrol |
| `dependency check` | Bağımlılık kontrolü |

## 4. Worker Template

Her worker:
```yaml
name: worker-name
version: 1.0.0
description: Ne iş yapar?
provider: opencode-go
skills: [skill1, skill2]
dependencies: []
```

## 5. Not

Bu bileşen **ileri aşama** — hemen implementasyon gerekmez. 
Önce multi-tenant yapısı oturmalı.
