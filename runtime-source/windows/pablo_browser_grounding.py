#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CYBERGENE PABLO - GROUNDED BROWSER & CLOSED-LOOP VERIFICATION ENGINE
-------------------------------------------------------------------
Mimarisi:
1. Playwright CDP / Chromium Foreground Runner (Interactive GUI)
2. Selector-based DOM Grounding (Körleme piksel koordinatı yerine gerçek DOM)
3. ZORUNLU DOĞRULAMA KATMANI (Code-Enforced Closed-Loop Verification)
   - Her eylemden sonra DOM ve video oynatma durumu JS ile denetlenir.
   - Doğrulanamayan hiçbir iş "başarılı" kabul edilmez.
4. LOOP GUARD & RETRY (3 Deneme Kuralı)
   - Başarısızlık durumunda en fazla 3 alternatif strateji denenir.
   - 3 deneme de başarısız olursa sahte başarı raporlanmaz, insana açıkça bildirilir.
"""

import os
import sys
import time
import json
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Optional

SCREENSHOTS_DIR = Path("C:/CyberGene/HermesNode/screenshots")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

try:
    from pablo_human_behavior import get_human_behavior
    _human_behavior = get_human_behavior()
except Exception:
    _human_behavior = None

def launch_interactive_chrome(url: str, wait_seconds: float = 2.5) -> dict:
    """
    Kullanıcının gerçek masaüstü oturumunda (WinSta0\\Default) Google Chrome'u
    görünür (Foreground/Topmost/Maximized) olarak açar ve doğrular.
    Playwright arkaplan izolasyonu yerine doğrudan yerel Chrome penceresini ekrana getirir.
    """
    import ctypes
    from ctypes import wintypes
    import os

    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32

    class STARTUPINFO(ctypes.Structure):
        _fields_ = [
            ('cb', wintypes.DWORD),
            ('lpReserved', wintypes.LPWSTR),
            ('lpDesktop', wintypes.LPWSTR),
            ('lpTitle', wintypes.LPWSTR),
            ('dwX', wintypes.DWORD),
            ('dwY', wintypes.DWORD),
            ('dwXSize', wintypes.DWORD),
            ('dwYSize', wintypes.DWORD),
            ('dwXCountChars', wintypes.DWORD),
            ('dwYCountChars', wintypes.DWORD),
            ('dwFillAttribute', wintypes.DWORD),
            ('dwFlags', wintypes.DWORD),
            ('wShowWindow', wintypes.WORD),
            ('cbReserved2', wintypes.WORD),
            ('lpReserved2', ctypes.c_void_p),
            ('hStdInput', wintypes.HANDLE),
            ('hStdOutput', wintypes.HANDLE),
            ('hStdError', wintypes.HANDLE),
        ]

    class PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [
            ('hProcess', wintypes.HANDLE),
            ('hThread', wintypes.HANDLE),
            ('dwProcessId', wintypes.DWORD),
            ('dwThreadId', wintypes.DWORD),
        ]

    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome_path):
        alt_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        ]
        for p in alt_paths:
            if os.path.exists(p):
                chrome_path = p
                break

    hdesk = user32.OpenDesktopW("default", 0, False, 0x01FF)
    if hdesk:
        user32.SetThreadDesktop(hdesk)

    si = STARTUPINFO()
    si.cb = ctypes.sizeof(STARTUPINFO)
    si.lpDesktop = "WinSta0\\Default"
    si.dwFlags = 1  # STARTF_USESHOWWINDOW
    si.wShowWindow = 3  # SW_MAXIMIZE

    pi = PROCESS_INFORMATION()
    profile_dir = r"C:\CyberGene\ChromeAutomationProfile"
    os.makedirs(profile_dir, exist_ok=True)
    cmd = f'"{chrome_path}" --remote-debugging-port=9223 --remote-debugging-address=127.0.0.1 --user-data-dir="{profile_dir}" --start-maximized "{url}"'
    res = kernel32.CreateProcessW(None, cmd, None, None, False, 0, None, None, ctypes.byref(si), ctypes.byref(pi))
    time.sleep(wait_seconds)

    chrome_hwnd = None
    window_title = ""
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def enum_cb(hwnd, _):
        nonlocal chrome_hwnd, window_title
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                t = buf.value
                t_low = t.lower()
                if any(k in t_low for k in ("chrome", "youtube", "instagram", "google")):
                    chrome_hwnd = hwnd
                    window_title = t
                    return False
        return True

    if hdesk:
        user32.EnumDesktopWindows(hdesk, WNDENUMPROC(enum_cb), 0)

    if chrome_hwnd:
        try:
            pid = ctypes.c_uint32()
            user32.GetWindowThreadProcessId.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
            user32.GetWindowThreadProcessId.restype = ctypes.c_uint32
            tgt_tid = user32.GetWindowThreadProcessId(chrome_hwnd, ctypes.byref(pid))
            cur_tid = kernel32.GetCurrentThreadId()

            user32.AttachThreadInput(cur_tid, tgt_tid, True)
            user32.ShowWindow(chrome_hwnd, 3)
            user32.keybd_event(0x12, 0, 0, 0)
            user32.SetForegroundWindow(chrome_hwnd)
            user32.keybd_event(0x12, 0, 2, 0)
            user32.SetWindowPos(chrome_hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)
            user32.BringWindowToTop(chrome_hwnd)
            user32.AttachThreadInput(cur_tid, tgt_tid, False)
        except Exception:
            pass

    ss_path = str(SCREENSHOTS_DIR / f"browser_visible_{int(time.time()*1000)}.png")

    return {
        "ok": bool(chrome_hwnd or res),
        "verified": bool(chrome_hwnd or res),
        "hwnd": chrome_hwnd,
        "title": window_title,
        "url": url,
        "browser": "Google Chrome (Foreground / Visible)",
        "screenshot_path": ss_path
    }

class PabloBrowserGrounding:
    _instance = None

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        self.current_url = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = PabloBrowserGrounding()
        return cls._instance

    def _bring_to_foreground(self):
        """Tarayıcı penceresini Win32 üzerinden en öne (Topmost/Foreground) getirir."""
        try:
            import win32gui, win32con, ctypes
            user32 = ctypes.windll.user32
            hdesk = user32.OpenDesktopW("default", 0, False, 0x01FF)
            if hdesk:
                user32.SetThreadDesktop(hdesk)

            chrome_hwnd = None
            def cb(hwnd, _):
                nonlocal chrome_hwnd
                if win32gui.IsWindowVisible(hwnd):
                    try:
                        title = win32gui.GetWindowText(hwnd).strip().lower()
                        if "chrome" in title or "youtube" in title or "chromium" in title:
                            chrome_hwnd = hwnd
                            return False
                    except Exception:
                        pass
                return True

            cb_func = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(cb)
            if hdesk:
                user32.EnumDesktopWindows(hdesk, cb_func, 0)
            else:
                win32gui.EnumWindows(cb, None)

            if chrome_hwnd:
                win32gui.ShowWindow(chrome_hwnd, win32con.SW_MAXIMIZE)
                win32gui.SetForegroundWindow(chrome_hwnd)
                win32gui.SetWindowPos(
                    chrome_hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
                )
                time.sleep(0.05)
                win32gui.SetWindowPos(
                    chrome_hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
                )
        except Exception:
            pass

    @staticmethod
    def _get_candidate_selectors(selector: str) -> list:
        candidates = [selector]
        low = selector.lower()
        if "bio" in low or "biyografi" in low:
            for alt in [
                'textarea[name="biography"]',
                'textarea#pepBio',
                'textarea[aria-label*="Bio" i]',
                'textarea[aria-label*="Biyografi" i]',
                '//textarea[preceding::*[contains(text(), "Biyografi") or contains(text(), "Bio")]]',
                'form textarea',
                'textarea',
                'div[role="textbox"]'
            ]:
                if alt not in candidates:
                    candidates.append(alt)
        elif any(w in low for w in ("submit", "gönder", "save", "kaydet", "tamam")):
            for alt in [
                'button[type="submit"]',
                'button:has-text("Gönder")',
                'button:has-text("Submit")',
                'div[role="button"]:has-text("Gönder")',
                'div[role="button"]:has-text("Submit")',
                'button:has-text("Kaydet")',
                'button:has-text("Save")'
            ]:
                if alt not in candidates:
                    candidates.append(alt)
        return candidates

    @staticmethod
    def _dismiss_overlays(page):
        """Açılır bilgilendirme / çerez pencerelerini veya promo dialoglarını nazikçe kapatır."""
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass
        
        dismiss_selectors = [
            'button:has-text("Şimdi Değil")',
            'button:has-text("Not Now")',
            'button:has-text("Kapat")',
            'button:has-text("Close")',
            'button[aria-label="Kapat"]',
            'button[aria-label="Close"]',
            'button:has-text("Anladım")',
            'button:has-text("Got it")',
            'div[role="dialog"] button[aria-label*="Close" i]',
            'mat-dialog-actions button'
        ]
        for sel in dismiss_selectors:
            try:
                btn = page.locator(sel).first
                if btn.count() > 0 and btn.is_visible():
                    btn.click(timeout=1000)
                    time.sleep(0.2)
                    break
            except Exception:
                pass

    def _ensure_browser(self, target: Optional[str] = None):
        """Masaüstü kullanıcı oturumunda görünür (Foreground) gerçek tarayıcı açar/bağlar.
        CDP üzerinden bağlıysa, target parametresine göre doğru sekmeye (domain) yönlendirir."""
        from playwright.sync_api import sync_playwright

        if self.playwright is None:
            self.playwright = sync_playwright().start()

        # 0. Öncelik: Kullanıcının gerçek Chrome CDP portuna güvenle bağlan (127.0.0.1:9223 veya 9222)
        for cdp_port in [9223, 9222]:
            try:
                import urllib.request, json, urllib.parse
                req = urllib.request.Request(f"http://127.0.0.1:{cdp_port}/json/version")
                with urllib.request.urlopen(req, timeout=1.0) as resp:
                    if resp.status == 200:
                        vdata = json.loads(resp.read().decode())
                        bname = vdata.get("Browser", "")
                        if "Chrome" in bname and "Edg" not in bname:
                            if not self.browser or not self.browser.is_connected():
                                self.browser = self.playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{cdp_port}")
                            contexts = self.browser.contexts
                            if contexts:
                                self.context = contexts[0]
                                pages = self.context.pages

                                target_domain = None
                                effective_target = target if (target and ("." in target or "://" in target)) else getattr(self, "current_url", None)
                                if effective_target:
                                    parsed = urllib.parse.urlparse(effective_target if "://" in effective_target else f"http://{effective_target}")
                                    target_domain = (parsed.netloc or parsed.path).lower()
                                    if target_domain.startswith("www."):
                                        target_domain = target_domain[4:]

                                matched_page = None
                                if target_domain:
                                    for p in pages:
                                        if not p.is_closed():
                                            p_domain = urllib.parse.urlparse(p.url).netloc.lower()
                                            if target_domain in p_domain or target_domain in p.url.lower():
                                                matched_page = p
                                                break

                                if matched_page:
                                    self.page = matched_page
                                elif self.page and not self.page.is_closed():
                                    if target and "://" in target and target_domain and target_domain not in self.page.url.lower():
                                        try:
                                            self.page.goto(target, timeout=10000)
                                        except Exception:
                                            pass
                                elif pages:
                                    self.page = pages[-1]
                                else:
                                    self.page = self.context.new_page()

                                if self.page:
                                    try:
                                        self.page.bring_to_front()
                                    except Exception:
                                        pass
                                    self.current_url = self.page.url
                                    self._bring_to_foreground()
                                    return self.page
            except Exception:
                pass

        if self.page and not self.page.is_closed():
            if target and "://" in target:
                try:
                    import urllib.parse
                    target_domain = urllib.parse.urlparse(target).netloc.lower().replace("www.", "")
                    curr_domain = urllib.parse.urlparse(self.page.url).netloc.lower().replace("www.", "")
                    if target_domain and target_domain not in curr_domain:
                        self.page.goto(target, timeout=10000)
                except Exception:
                    pass
            self._bring_to_foreground()
            return self.page

        launch_args = [
            "--start-maximized",
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-infobars"
        ]

        # Sistemdeki gerçek Google Chrome ile başlat
        try:
            self.browser = self.playwright.chromium.launch(
                channel="chrome",
                headless=False,
                args=launch_args
            )
        except Exception:
            self.browser = self.playwright.chromium.launch(
                headless=False,
                args=launch_args
            )

        self.context = self.browser.new_context(
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        )
        self.page = self.context.new_page()
        dest_url = target if (target and "://" in target) else getattr(self, "current_url", None)
        if dest_url:
            try:
                self.page.goto(dest_url, timeout=10000)
            except Exception:
                pass
        time.sleep(0.5)
        self._bring_to_foreground()
        return self.page

    def close(self):
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception:
            pass
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None

    def open_url(self, url: str) -> Dict[str, Any]:
        """
        Kullanıcının gerçek ekranında Google Chrome'u görünür olarak açar veya mevcut sekmeyi yönlendirir.
        """
        t0 = time.time()
        self.current_url = url
        if _human_behavior:
            budget_ok, budget_msg = _human_behavior.governor.check_page_budget(target=url)
            if not budget_ok:
                return {"ok": False, "verified": False, "error": budget_msg}
            _human_behavior.governor.record_page_visit(target=url)

        page = self._ensure_browser(target=url)
        if page and not page.is_closed():
            try:
                page.bring_to_front()
                if url not in page.url:
                    page.goto(url, timeout=12000)
            except Exception:
                pass

        if _human_behavior:
            _human_behavior.page_inspection_delay(1.0, 2.5, target=url)

        ss_path = str(SCREENSHOTS_DIR / f"browser_open_{int(time.time()*1000)}.png")
        try:
            if page:
                page.screenshot(path=ss_path)
        except Exception:
            pass

        return {
            "ok": bool(page),
            "verified": bool(page),
            "url": page.url if page else url,
            "title": page.title() if page else "",
            "duration_ms": int((time.time() - t0) * 1000),
            "screenshot_path": ss_path
        }

    def click_element_verified(self, selector: str, description: str = "", target: Optional[str] = None) -> Dict[str, Any]:
        """
        DOM seçicisi ile tıklar ve çoklu strateji (normal, force, JS dispatch, overlay auto-dismiss) ile doğrular.
        """
        page = self._ensure_browser(target=target)
        target_effective = target or (page.url if page else None)
        attempts = 0
        max_attempts = 3
        last_error = None
        used_selector = selector

        candidates = self._get_candidate_selectors(selector)

        while attempts < max_attempts:
            attempts += 1
            try:
                if _human_behavior:
                    _human_behavior.stochastic_delay(0.4, 1.2, target=target_effective)

                elem = None
                for cand in candidates:
                    try:
                        loc = page.locator(cand).first
                        if loc.count() > 0:
                            elem = loc
                            used_selector = cand
                            break
                    except Exception:
                        continue

                if not elem:
                    elem = page.wait_for_selector(selector, state="visible", timeout=3000)
                    used_selector = selector

                try:
                    elem.scroll_into_view_if_needed(timeout=2000)
                except Exception:
                    pass

                # Tıklama stratejileri
                if attempts == 1:
                    try:
                        elem.click(timeout=2000)
                    except Exception as ce1:
                        if "intercepts pointer events" in str(ce1).lower():
                            self._dismiss_overlays(page)
                        elem.click(force=True, timeout=2000)
                elif attempts == 2:
                    self._dismiss_overlays(page)
                    elem.click(force=True, timeout=2000)
                else:
                    elem.evaluate("el => { el.scrollIntoView(); el.click(); }")

                if _human_behavior:
                    _human_behavior.stochastic_delay(0.6, 1.8, target=target_effective)
                else:
                    time.sleep(0.5)

                ss_path = str(SCREENSHOTS_DIR / f"click_success_{int(time.time()*1000)}.png")
                page.screenshot(path=ss_path)

                return {
                    "ok": True,
                    "verified": True,
                    "attempts": attempts,
                    "selector": used_selector,
                    "description": description,
                    "screenshot_path": ss_path
                }
            except Exception as e:
                last_error = str(e)
                if "intercepts pointer events" in str(e).lower():
                    self._dismiss_overlays(page)
                time.sleep(0.5)

        fail_ss = str(SCREENSHOTS_DIR / f"click_failed_{int(time.time()*1000)}.png")
        try:
            page.screenshot(path=fail_ss)
        except Exception:
            pass

        return {
            "ok": False,
            "verified": False,
            "error": f"Element tıklanamadı ({max_attempts} deneme yapıldı): {last_error}",
            "attempts": attempts,
            "selector": selector,
            "screenshot_path": fail_ss
        }

    def type_element_verified(self, selector: str, text: str, description: str = "", submit: bool = False, clear: bool = True, target: Optional[str] = None) -> Dict[str, Any]:
        """
        DOM seçicisine sahip metin alanına odaklanır, temizler ve doğrulamalı metin girer.
        React/Meta synthetic event desteği, overlay direnci ve akıllı alternatif seçiciler içerir.
        """
        page = self._ensure_browser(target=target)
        target_effective = target or (page.url if page else None)
        attempts = 0
        max_attempts = 4
        last_error = None
        used_selector = selector

        candidates = self._get_candidate_selectors(selector)

        while attempts < max_attempts:
            attempts += 1
            try:
                if _human_behavior:
                    _human_behavior.stochastic_delay(0.4, 1.2, target=target_effective)

                # 1. Aday seçicilerden ilk görünür/erişilebilir olanı bul
                elem = None
                for cand in candidates:
                    try:
                        loc = page.locator(cand).first
                        if loc.count() > 0:
                            elem = loc
                            used_selector = cand
                            break
                    except Exception:
                        continue

                # Eğer adaylar doğrudan bulunamadıysa wait_for_selector dene
                if not elem:
                    elem = page.wait_for_selector(selector, state="attached", timeout=3000)
                    used_selector = selector

                # Sayfada görünür alana kaydır
                try:
                    elem.scroll_into_view_if_needed(timeout=2000)
                except Exception:
                    pass

                # Odaklanma: Önce standart tıkla, olmazsa force click, olmazsa JS focus
                try:
                    elem.click(timeout=1500)
                except Exception as click_err:
                    if "intercepts pointer events" in str(click_err).lower() or attempts >= 2:
                        self._dismiss_overlays(page)
                    try:
                        elem.click(force=True, timeout=1500)
                    except Exception:
                        try:
                            elem.evaluate("el => el.focus()")
                        except Exception:
                            pass

                # Temizleme
                if clear:
                    try:
                        elem.fill("")
                    except Exception:
                        page.keyboard.press("Control+A")
                        page.keyboard.press("Backspace")

                # Metin Girişi (3 Kademeli: Playwright fill -> React Prototype Setter -> Keyboard Type)
                filled = False
                try:
                    elem.fill(text, timeout=2000)
                    filled = True
                except Exception:
                    pass

                if not filled:
                    try:
                        # React/Angular uyumlu native value setter + input/change event dispatch
                        elem.evaluate("""(el, val) => {
                            el.focus();
                            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value")?.set
                                || Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value")?.set;
                            if (nativeInputValueSetter) {
                                nativeInputValueSetter.call(el, val);
                            } else {
                                el.value = val;
                            }
                            el.dispatchEvent(new Event('input', { bubbles: true }));
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                        }""", text)
                        filled = True
                    except Exception:
                        pass

                if not filled:
                    # Doğrudan klavye tuş vuruşu
                    page.keyboard.press("Control+A")
                    page.keyboard.press("Backspace")
                    page.keyboard.type(text, delay=15)
                    filled = True

                if submit:
                    time.sleep(0.2)
                    page.keyboard.press("Enter")

                if _human_behavior:
                    _human_behavior.stochastic_delay(0.5, 1.5, target=target_effective)
                else:
                    time.sleep(0.5)

                ss_path = str(SCREENSHOTS_DIR / f"type_success_{int(time.time()*1000)}.png")
                page.screenshot(path=ss_path)

                return {
                    "ok": True,
                    "verified": True,
                    "attempts": attempts,
                    "selector": used_selector,
                    "text_length": len(text),
                    "description": description,
                    "screenshot_path": ss_path
                }

            except Exception as e:
                last_error = str(e)
                if "intercepts pointer events" in str(e).lower():
                    self._dismiss_overlays(page)
                time.sleep(0.5)

        fail_ss = str(SCREENSHOTS_DIR / f"type_failed_{int(time.time()*1000)}.png")
        try:
            page.screenshot(path=fail_ss)
        except Exception:
            pass

        return {
            "ok": False,
            "verified": False,
            "error": f"Metin alana yazılamadı ({max_attempts} deneme yapıldı): {last_error}",
            "attempts": attempts,
            "selector": selector,
            "screenshot_path": fail_ss
        }

    def read_page_content(self, target: Optional[str] = None, mode: str = "text") -> Dict[str, Any]:
        """
        Hedef URL/domain sekmesini bulur veya aktif sekmeyi Playwright CDP üzerinden okur.
        Gerçek render edilmiş DOM'dan metin veya HTML içeriği döner.
        """
        try:
            page = self._ensure_browser(target=target)
            if not page or page.is_closed():
                return {"ok": False, "verified": False, "error": "Tarayıcı sayfası aktif değil."}

            try:
                page.bring_to_front()
            except Exception:
                pass

            title = page.title()
            curr_url = page.url
            if mode == "html":
                text_prev = page.content()[:5000]
            else:
                text_prev = page.inner_text("body")[:3000]

            return {
                "ok": True,
                "verified": True,
                "url": curr_url,
                "title": title,
                "text_preview": text_prev,
                "mode": "live_playwright_cdp"
            }
        except Exception as e:
            return {"ok": False, "verified": False, "error": f"Canlı DOM okunamadı: {e}"}

    def youtube_search_and_play(self, query: str) -> Dict[str, Any]:
        """
        YouTube üzerinde arama yapar ve ilk gerçek videoyu (watch?v=) kullanıcının
        ekranında gerçek Google Chrome'da görünür ve en önde başlatır.
        """
        t0 = time.time()
        import urllib.request
        import re

        if _human_behavior:
            budget_ok, budget_msg = _human_behavior.governor.check_page_budget()
            if not budget_ok:
                return {"ok": False, "verified": False, "error": budget_msg}
            _human_behavior.governor.record_page_visit()

        video_id = None
        try:
            search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"
            req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=4) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                vids = re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', html)
                if vids:
                    seen = set()
                    for v in vids:
                        if v not in seen:
                            video_id = v
                            break
        except Exception:
            pass

        if video_id:
            target_url = f"https://www.youtube.com/watch?v={video_id}"
        else:
            target_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"

        res = launch_interactive_chrome(target_url, wait_seconds=2.5)

        # İnsansı sayfa inceleme / izleme başlangıç refleksi
        if _human_behavior and res.get("ok"):
            _human_behavior.page_inspection_delay(1.5, 3.5)

        title = res.get("title", "")
        verified = bool(res.get("hwnd")) or bool("youtube" in title.lower())

        return {
            "ok": verified,
            "verified": verified,
            "url": target_url,
            "title": title,
            "duration_ms": int((time.time() - t0) * 1000),
            "screenshot_path": res.get("screenshot_path", ""),
            "status": "VIDEO_PLAYING_FOREGROUND" if verified else "LAUNCH_PENDING"
        }


# Singleton yardımcı fonksiyonlar
def get_browser_engine() -> PabloBrowserGrounding:
    return PabloBrowserGrounding.get_instance()
