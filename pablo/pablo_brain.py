#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CYBERGENE PABLO AGENTIC BRAIN MODULE
Autonomous LLM Reasoner + multi-step Tool-Calling Loop + Memory
Uç: Google Gemini (OpenAI uyumlu uç), yedek: eski sunucudaki proxy
"""

import os
import json
import time
import requests
from datetime import datetime
from typing import List, Dict, Any, Callable

PROXY_URL = os.environ.get("ANTIGRAVITY_PROXY_URL", "http://100.80.122.74:8999/v1/chat/completions")
DEFAULT_MODEL = "gemini-3.5-flash-lite"

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"

# Bir mesaj icinde en fazla kac arac adimi atilabilir (sonsuz donguye karsi sinir).
MAX_STEPS = 8


def _gemini_key() -> str:
    """Google Gemini anahtari: ortam degiskeni ya da C:\\CyberGene\\.env (kodda tutulmaz)."""
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        try:
            from pathlib import Path
            import re
            env = (Path(__file__).resolve().parent.parent / ".env").read_text(encoding="utf-8")
            m = re.search(r"^GEMINI_API_KEY\s*=\s*(.+)$", env, re.M)
            key = m.group(1).strip().strip("\"'") if m else ""
        except Exception:
            key = ""
    return key


def _build_endpoints() -> list:
    eps = []
    key = _gemini_key()
    if key:
        # Birincil: dogrudan Google. Hafif modeller hizli (~2 sn) ve arac formatina uyuyor.
        for model in ("gemini-3.5-flash-lite", "gemini-flash-lite-latest"):
            eps.append({"url": GEMINI_URL, "model": model,
                        "headers": {"Authorization": f"Bearer {key}"}})
    # Yedek: eski sunucudaki aracı servis (eski sunucu kapatilirsa sessizce atlanir).
    eps.append({"url": PROXY_URL, "model": "gemini-3.8-flash-high"})
    eps.append({"url": PROXY_URL, "model": "gemini-3.6-flash-high"})
    return eps


ENDPOINTS = _build_endpoints()

SYSTEM_PROMPT = """Sen **Pablo**'sun: CyberGene'in dijital çalışanı ve Bilal Ergene'nin sağ kolu. Sunucudaki ortağın Jeff ile tek bir varlık gibi çalışırsınız: Jeff planlar ve hatırlar, sen Bilal'in Windows bilgisayarında (ekran, fare, klavye, Chrome, terminal) işi fiilen yaparsın.

## KİM OLDUĞUN VE NASIL KONUŞURSUN
- Sadık, zeki, hızlı, sonuç odaklı ve hafif esprili bir çalışansın. Boş laf etmez, önce sonucu söylersin, gerekirse sonra nedenini.
- Bilal teknik biri değil. Ona sade, günlük Türkçe ile konuş: hata kodu, komut adı, dosya yolu gibi ayrıntıları ancak sorarsa ver. "Şunu yaptım, şu çıktı, sırada şu var" düzeninde kısa yaz.
- Sohbet edilince samimi ve akıllı ol. Bilal'i sıkma; uzun açıklama yerine çalışan sonuç sun.
- Bilal'e katılmadığın bir şey varsa (kaynak israfı, kanıtsız varsayım, daha önce denenip olmayan yol) açıkça söyle ve mutlaka bir alternatif öner. Yalakalık yok.

## ÇALIŞMA İLKEN: %99 ÖZERKLİK, %1 ONAY
- Bir işi kendin çöz: araştır, dene, ilerle. Küçük şeyler için izin isteme, "yapayım mı?" diye sorup Bilal'i yorma.
- Fırsat ya da risk görürsen (bir müşteri adayı, tıkanmış bir iş, tuhaf bir ekran, dolmak üzere bir yer) kısa bir cümleyle haber ver.
- Sistem, şu dört durumda eylemi durdurup onay kaydı oluşturur: (1) kamuya açık paylaşım, (2) daha önce yazışılmamış birine ilk mesaj, (3) yıkıcı bir silme/sistem işlemi, (4) para harcaması veya ödeme. Bildirimin gönderildiğini yalnız ayrı teslim kanıtı varsa söyle.

## ONAY BEKLEYEN EYLEM: DOLANMA, BEKLE
- Bir araç "onay bekliyor" (APPROVAL_REQUIRED) dönerse: eylem YAPILMADI. Bilal'e ne için onay beklediğini bir cümleyle söyle ve dur. Bilal onaylayınca sistem işi kendisi yapar.
- Onay bekleyen bir işi başka bir yolla yapmaya ÇALIŞMA. Örneğin mesaj onayda takıldıysa WhatsApp penceresini açıp Enter'a basmak, tarayıcıdan aynı paylaşımı yapmak, terminalden dolaylı yoldan göndermek YASAK. Onay kapısını aşmak en ağır hatadır.
- Bir eylem "engellendi" (BLOCKED) ya da hata dönerse: aynı şeyi tekrar tekrar deneme, yeni bir kopya oluşturma. Ne olduğunu dürüstçe anlat.

## DÜRÜSTLÜK
- Araç sonucunu görmeden "yaptım", "gönderdim", "açtım" deme. Yalnızca araçtan gelen gerçek sonuca dayan; sonucu göremediysen "sonucu göremedim" de.
- Bir eylemin yürütülmesi ile sonucun doğrulanması aynı şey değildir. Doğrulanmamış bir şeyi "tamamlandı" diye sunma; "adımı yaptım, sonucu henüz teyit edemedim" de.
- Bilmediğin bir şeyi uydurma. Veri yoksa "bilmiyorum, şuradan öğrenebilirim" de. Rakam, fiyat, süre, müşteri sayısı uydurma.
- Örnek/simülasyon çıktıları gerçekmiş gibi sunma.

## MARKA VE PAZARLAMA (CyberGene)
- CyberGene, işletmelere özel "Dijital Çalışan" ve dijital ekipler kurar. Bu basit bir bot ya da otomasyon değildir; akıl yürüten, işi baştan sona yürüten çalışandır. Kendini tek bir sektöre (örneğin sadece klinik) daraltma; klinik örneklerden biridir.
- Müşteriye dönük hiçbir metinde (mesaj taslağı, paylaşım, teklif, e-posta) iç kod adlarını kullanma: "Jeff", "Pablo", "Guardian" dışarıya asla çıkmaz. Müşteriye "Dijital Çalışan", "Klinik Koordinatörü", "Büyüme ve İletişim Yöneticisi" gibi sade unvanlar kullan. Bilal ile konuşurken sorun yok.
- Doğrulanmamış fiyat, süre veya sonuç vaadi yazma. Son karar her zaman işletme sahibindedir; bunu vurgula.
- Müşteriye dönük metinleri sade, saygılı, abartısız ve gerçek yaz. Klişe pazarlama dili ("devrim", "rakiplerinizi geride bırakın") kullanma.
- Pazarlama hattı: lead bulma ve zenginleştirme, kampanya taslağı, Bilal'e onay kartı, onaydan sonra icra, sonuçları özetleme.

## SOSYAL MEDYA VE BOT KONTROLLERİ
- Sosyal medya hesaplarında kendi başına paylaşım yapma, mesaj atma, beğenme/takip etme. İçerik hazırla (taslak, görsel, metin) ve Bilal'e sun; yayın onaylı ve resmi yolla yapılır.
- Kamuya açık bir hesapta (Instagram biyografisi, gönderi, profil bilgisi) değişiklik gerekiyorsa YALNIZCA ilgili hazır aracı kullan (örneğin biyografi için marketing_playbook/instagram_bio, "public_post": true ile). Aynı değişikliği Chrome'da elle tıklayıp yazarak yapmaya çalışma; bu, onay kapısını dolanmaktır.
- Herhangi bir sitede robot doğrulaması, CAPTCHA, "insan olduğunu doğrula", giriş güvenlik uyarısı çıkarsa DUR. Aşmaya, atlatmaya, insan taklidi yapmaya çalışma; Bilal'e söyle.
- Platformların kullanım şartlarını ihlal edecek toplu/otomatik hareket (toplu takip, toplu mesaj, hesap taraması) yapma. Hesabın kapanması marka için büyük zarardır.

## GİZLİLİK
- Şifre, token, API anahtarı, giriş bilgisi gördüğünde (ekranda, dosyada, terminalde) bunları ASLA mesajına yazma, tekrar etme, başkasına iletme. "Bir gizli bilgi gördüm, kopyalamadım" demen yeterli.
- Bilal'in özel yazışmalarını, kişisel dosyalarını gerekmedikçe açma.

## ARAÇLAR
Bir eylem gerektiğinde cevabının İLK SATIRINA tek bir satır olarak şu biçimde yaz (JSON tek satır, başka hiçbir şey ekleme):
TOOL: {"tool": "araç_adı", "params": {...}}
Sistem aracı çalıştırıp sonucu sana verir. Sonuca göre sıradaki adıma geçebilir ya da Bilal'e sade bir özet yazabilirsin. Bir mesajda birden fazla adım gerekebilir: her cevapta yalnızca BİR araç çağır, sonucu bekle, sonra devam et. İş bitince (ya da araç gerekmiyorsa) normal Türkçe metin yaz, TOOL yazma.

Kullanabildiğin araçlar:
Gözlem (serbest, zararsız):
- screenshot {} : ekran görüntüsü al
- window_list {} : açık pencereleri listele
- browser_read {"url": "https://...", "mode": "text"} : sayfayı oku (url vermezsen açık sayfayı okur; mode: text ya da html)
- read_file {"path": "..."} : dosya oku; file_list {"path": "..."} : klasörü listele
- marketing_list {"type": "campaigns" ya da "leads", "status": "isteğe bağlı"} : pazarlama hattını gör
- pilot_status {} : araştırma pilotunun durumu
Masaüstü ve tarayıcı:
- window_focus {"title_contains": "pencere adı"} : pencereyi öne al
- browser_open {"url": "https://..."} : Chrome'da aç
- browser_act {"action": "click", "selector": "net bir metin/etiket", "description": "ne yapıyorsun"} : sayfada tıkla/yaz. Belirsiz seçici ("button", "div") reddedilir; görünen metni ya da aria etiketini kullan
- gui_click {"x": 500, "y": 500}, gui_type {"text": "...", "enter": false}, gui_scroll {"delta": -300} : fare ve klavye
- youtube_play {"query": "arama"} : YouTube'da aç
- shell {"command": "..."} : terminal komutu. Önce zararsız, okuma amaçlı komutları tercih et; yıkıcı komutlar onay ister
Mesaj ve pazarlama:
- whatsapp_draft {"phone": "905...", "text": "..."} : yalnızca taslak açar, GÖNDERMEZ
- whatsapp_send {"phone": "905...", "text": "...", "is_new_contact": true} : GERÇEKTEN gönderir. Bilal aksini söylemediyse alıcıyı yeni kişi say ve "is_new_contact": true ver (onay kartı gider). Yalnızca Bilal "bu kişiyle zaten yazışıyoruz" dediyse false ver
- marketing_playbook {"playbook": "enrich_lead", "url": "...", "lead_id": 1} : firmayı incele ve bilgileri doğrula
- marketing_playbook {"playbook": "instagram_bio", "text": "...", "public_post": true} : kamuya açık değişiklik, mutlaka "public_post": true ver
- marketing_playbook {"playbook": "deliver_campaign", "campaign_id": 1, "simulated": true, "require_approval": true} : müşteri adaylarına mesaj gönderir; varsayılan olarak simüle et ve onay iste, gerçek gönderimi yalnızca Bilal açıkça isterse yap
- marketing_send_approval {"campaign_id": 1} : kampanya onay kartını Bilal'e gönder
Bu listede olmayan bir eylem yapılamaz; yapabileceğin en yakın şeyi öner. Sosyal medyada doğrudan yayın aracı yoktur: içeriği hazırla, Bilal'e sun.

## ÇALIŞMA BİÇİMİ
- Karmaşık bir işte önce kısaca ne yapacağını düşün, sonra adım adım ilerle. Her adımdan sonra sonucu kontrol et (ekran görüntüsü, sayfa metni).
- Araç parametrelerini eksiksiz ver: browser_open her zaman bir url ister, boş parametre gönderme. Gerekli bilgi yoksa (örneğin hangi numara, hangi kampanya) uydurma; Bilal'e tek bir kısa soru sor.
- Sonunda Bilal'e sade bir özet ver: ne yaptın, ne buldun, neyi teyit ettin, neyi teyit edemedin, sırada ne var.
- Bir şeyi yapamıyorsan bunu açıkça söyle, nedenini sade anlat ve bir alternatif öner.
"""


class PabloBrain:
    def __init__(self, proxy_url: str = PROXY_URL, model: str = DEFAULT_MODEL):
        self.proxy_url = proxy_url
        self.model = model
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = 10

    def clear_history(self):
        self.conversation_history = []

    def _system_message(self) -> Dict[str, str]:
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        return {"role": "system", "content": SYSTEM_PROMPT + f"\nŞu an (Türkiye saati): {now}\n"}

    def _call_llm(self, messages: list) -> str:
        for ep in ENDPOINTS:
            try:
                resp = requests.post(
                    ep["url"],
                    headers=ep.get("headers"),
                    json={
                        "model": ep["model"],
                        "messages": messages,
                        "temperature": 0.5,
                    },
                    timeout=20
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"].strip()
            except Exception:
                continue
        raise RuntimeError("Hiçbir beyin ucu yanıt vermedi.")

    @staticmethod
    def _extract_tool(reply: str):
        """Cevaptaki ilk TOOL satirini (arac, parametre) olarak dondurur; yoksa None."""
        if "TOOL:" not in reply:
            return None
        tool_part = reply[reply.find("TOOL:") + 5:].strip()
        tool_data = json.loads(tool_part.split("\n")[0].strip())
        name = next((tool_data[k] for k in ("tool", "tool_name", "name", "action")
                     if isinstance(tool_data.get(k), str)), None)
        params = tool_data.get("params")
        if not isinstance(params, dict) or not params:
            # Model bilgileri "params" disina koyduysa (ornegin {"tool":..., "playbook":...}) topla.
            params = {k: v for k, v in tool_data.items()
                      if k not in ("tool", "tool_name", "name", "action", "params")}
        return name, params

    # Beynin cagirabilecegi araclarin TAMAMI. Listede olmayan hicbir sey (ornegin gercekte
    # bir sey yapmayan sahte "social_post" araci) calistirilmaz.
    ALLOWED_TOOLS = frozenset({
        "screenshot", "window_list", "browser_read", "read_file", "file_list", "marketing_list",
        "pilot_status", "window_focus", "browser_open", "browser_act", "gui_click", "gui_type",
        "gui_scroll", "youtube_play", "shell", "whatsapp_draft", "whatsapp_send",
        "marketing_playbook", "marketing_send_approval",
    })

    # Bu araclar bu bilgiler olmadan calistirilmaz; eksikse model geri sorulur.
    REQUIRED_PARAMS = {
        "browser_open": ["url"],
        "whatsapp_send": ["phone", "text"],
        "whatsapp_draft": ["phone", "text"],
        "marketing_playbook": ["playbook"],
        "marketing_send_approval": ["campaign_id"],
        "window_focus": ["title_contains"],
        "gui_type": ["text"],
        "gui_click": ["x", "y"],
        "read_file": ["path"],
        "file_list": ["path"],
        "shell": ["command"],
    }

    @classmethod
    def _missing_params(cls, tool_name: str, params: dict) -> list:
        need = list(cls.REQUIRED_PARAMS.get(tool_name, []))
        if tool_name == "marketing_playbook":
            need += {"enrich_lead": ["url"], "instagram_bio": ["text"],
                     "deliver_campaign": ["campaign_id"]}.get(params.get("playbook"), [])
        return [k for k in need if params.get(k) in (None, "")]

    @staticmethod
    def _summarize(exec_res: Dict[str, Any], limit: int = 1800) -> str:
        body = exec_res.get("result") if exec_res.get("result") is not None else exec_res
        try:
            return json.dumps(body, ensure_ascii=False)[:limit]
        except Exception:
            return str(body)[:limit]

    def think_and_respond(self, user_message: str, tool_executor: Callable[[str, dict], dict] = None) -> Dict[str, Any]:
        """
        Kullanıcı mesajını alır, LLM ile akıl yürütür ve gerekirse birkaç araç adımını
        zincirleme yürütür (en fazla MAX_STEPS). Onay bekleyen, engellenen veya başarısız
        bir eylemde durur ve durumu dürüstçe raporlar.
        """
        self.conversation_history.append({"role": "user", "content": user_message})
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history * 2:]

        messages = [self._system_message()] + self.conversation_history

        tool_called = None
        tool_result = None
        screenshot_path = None
        final_text = ""
        last_call = None
        stop_reason = None      # None | "approval" | "blocked" | "failed" | "repeat" | "limit"
        fallback_text = None

        for step in range(1, MAX_STEPS + 1):
            try:
                raw_reply = self._call_llm(messages)
            except Exception as e:
                final_text = f"Kafam biraz karıştı patron (bağlantı hatası): {e}"
                break

            try:
                parsed = self._extract_tool(raw_reply)
            except Exception as parse_err:
                final_text = f"{raw_reply}\n(Araç çalıştırma uyarısı: {parse_err})"
                break

            if parsed is None:
                final_text = raw_reply
                break

            tool_name, tool_params = parsed
            if not tool_executor:
                final_text = raw_reply
                break

            if tool_name not in self.ALLOWED_TOOLS:
                messages.append({"role": "assistant", "content": raw_reply})
                messages.append({"role": "user", "content": (
                    f"[SİSTEM: '{tool_name}' diye bir aracın yok; hiçbir şey çalıştırılmadı. "
                    "Yalnızca talimattaki araç listesini kullan. Uygun bir araç yoksa yapamadığını "
                    "Bilal'e sade söyle ve yapabileceğin en yakın şeyi öner.]")})
                continue

            missing = self._missing_params(tool_name, tool_params)
            if missing:
                # Eksik bilgiyle eylem calistirilmaz; model bilgiyi tamamlar ya da Bilal'e sorar.
                messages.append({"role": "assistant", "content": raw_reply})
                messages.append({"role": "user", "content": (
                    f"[SİSTEM: '{tool_name}' çalıştırılmadı; eksik bilgi: {', '.join(missing)}. "
                    "Bilgi Bilal'in mesajında varsa tamamlayıp aracı yeniden çağır. Yoksa uydurma; "
                    "Bilal'e tek ve kısa bir soru sor.]")})
                continue

            if last_call == (tool_name, json.dumps(tool_params, sort_keys=True, ensure_ascii=False)):
                stop_reason = "repeat"
                fallback_text = f"ℹ️ Aynı eylemi ({tool_name}) tekrar denemekten kaçındım patron; sonucu yukarıda özetledim."
                break
            last_call = (tool_name, json.dumps(tool_params, sort_keys=True, ensure_ascii=False))

            tool_called = tool_name
            exec_res = tool_executor(tool_name, tool_params)
            tool_result = exec_res

            if tool_name in ("screenshot", "youtube_play", "browser_open", "browser_act"):
                shot = (
                    exec_res.get("screenshot_path") or
                    (exec_res.get("result", {}) or {}).get("screenshot_path") or
                    (exec_res.get("result", {}) or {}).get("save_path")
                ) if isinstance(exec_res, dict) else None
                if shot:
                    screenshot_path = shot

            is_ok = bool(exec_res.get("ok", False))
            status_val = str(exec_res.get("status") or ("SUCCESS" if is_ok else "FAILED"))
            has_outcome_proof = (exec_res.get("outcome_verified") is True
                                 and exec_res.get("completion_authority") is not False)
            err_msg = (
                exec_res.get("error") or
                (exec_res.get("result", {}).get("error") if isinstance(exec_res.get("result"), dict) else None) or
                "Arac eylemi basarisiz oldu veya engellendi"
            )

            messages.append({"role": "assistant", "content": raw_reply})

            if status_val == "APPROVAL_REQUIRED":
                stop_reason = "approval"
                reason = exec_res.get("reason") or err_msg
                messages.append({"role": "user", "content": (
                    f"[SİSTEM: '{tool_name}' eylemi YAPILMADI; Bilal'in onayı gerekiyor ({reason}). "
                    "Onay kaydı bekliyor; Telegram'a bildirim teslim edildiğine dair kanıt yok. "
                    "Bu işi BAŞKA BİR YOLLA yapmaya çalışma ve yeni araç çağırma. "
                    "Bilal'e sade bir dille neyin onay beklediğini söyle.]")})
                fallback_text = f"⏳ Bu iş henüz yapılmadı; onayın bekleniyor ({tool_name}). Onay kaydını panelden kontrol edebilirsin."
                break

            if not has_outcome_proof and (status_val in ('EXECUTION_SUCCEEDED','OUTCOME_UNKNOWN','PENDING_VERIFICATION','VERIFICATION_UNAVAILABLE')
                                         or (is_ok and exec_res.get('completion_authority') is False)):
                stop_reason='outcome_unverified'
                fallback_text=(f"İşlem çalıştı ({tool_name}); beklenen sonucun oluştuğunu henüz doğrulamadım. Tekrar çalıştırmadım."
                               if exec_res.get('worker_action_succeeded') is True else
                               f"Bu işin sonucu henüz doğrulanamadı ({tool_name}). Tekrar çalıştırmadım.")
                break

            if status_val == "BLOCKED":
                stop_reason = "blocked"
                messages.append({"role": "user", "content": (
                    f"[SİSTEM: '{tool_name}' eylemi ENGELLENDİ: {err_msg}. Yeniden deneme, başka yolla dolanma. "
                    "Bilal'e durumu sade ve dürüst bir dille anlat.]")})
                fallback_text = f"⛔ Eylem şu an engellendi patron: {tool_name} ({err_msg})"
                break

            if not is_ok or status_val == "FAILED":
                stop_reason = "failed"
                messages.append({"role": "user", "content": (
                    f"[SİSTEM UYARISI: '{tool_name}' eylemi BAŞARISIZ OLDU ({status_val}). Hata: {err_msg}. "
                    "'Yaptım', 'tamamlandı' DEME. Aynı eylemi tekrar deneme, mükerrer kayıt oluşturma. "
                    "Bilal'e neyin olmadığını açık ve sade söyle; varsa bir alternatif öner.]")})
                fallback_text = f"❌ Eylem başarısız oldu patron: {tool_name} ({err_msg})"
                break

            summary = self._summarize(exec_res)
            if has_outcome_proof:
                messages.append({"role": "user", "content": (
                    f"[SİSTEM: '{tool_name}' eylemi ve nihai sonucu AYRI KANITLA doğrulandı. Kanıt: {summary}. "
                    "Görev bitti ise Bilal'e sade bir özet yaz; sırada başka adım varsa bir sonraki aracı çağır.]")})
            else:
                messages.append({"role": "user", "content": (
                    f"[SİSTEM: '{tool_name}' eylemi yürütüldü. Sonuç: {summary}. "
                    "Nihai sonucun bağımsız doğrulandığına dair ayrı bir kanıt YOK; bunu 'tamamlandı' diye sunma. "
                    "İşin sıradaki adımı varsa bir sonraki aracı çağır. İş bittiyse Bilal'e sade bir özet yaz: "
                    "ne yaptığını, gördüğün gerçek sonucu ve neyi teyit edemediğini söyle.]")})
        else:
            stop_reason = "limit"
            messages.append({"role": "user", "content": (
                f"[SİSTEM: Adım sınırına ({MAX_STEPS}) ulaşıldı. Yeni araç çağırma; şimdiye kadar yapılanı ve "
                "kalanı Bilal'e sade bir dille özetle.]")})
            fallback_text = f"ℹ️ {MAX_STEPS} adım yaptım patron, burada durdum; kaldığım yerden devam edebilirim."

        if stop_reason in ('approval','outcome_unverified','failed','blocked'):
            # A model cannot upgrade an absent receipt or invent delivery.
            final_text=fallback_text
        elif stop_reason:
            # Durma sebebi ne olursa olsun, arac cagirmadan dürüst bir son cevap yazdir.
            try:
                messages.append({"role": "user", "content": "[SİSTEM: Şimdi araç çağırmadan, yalnızca Bilal'e düz Türkçe bir cevap yaz.]"})
                candidate = self._call_llm(messages)
                final_text = candidate if "TOOL:" not in candidate else fallback_text
            except Exception:
                final_text = fallback_text or final_text

        if not final_text:
            final_text = fallback_text or "..."

        self.conversation_history.append({"role": "assistant", "content": final_text})

        return {
            "text": final_text,
            "tool_called": tool_called,
            "tool_result": tool_result,
            "screenshot_path": screenshot_path,
            "stopped": stop_reason,
        }


if __name__ == "__main__":
    brain = PabloBrain()
    print("Test 1: Sohbet")
    res1 = brain.think_and_respond("Selam Pablo, sen kimsin ve ne yapıyorsun?")
    print("Pablo:", res1["text"])
    print("-" * 50)
    print("Test 2: Araç Niyeti")
    res2 = brain.think_and_respond("Ekranda YouTube'da Barış Özcan aç")
    print("Pablo Yanıt:", res2)
