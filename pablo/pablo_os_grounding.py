import time
import uiautomation as auto
import ctypes
import os

class PabloOSGrounding:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        auto.SetGlobalSearchTimeout(3)  # Küresel arama zaman aşımı 3 saniye

    def find_window(self, title_contains):
        """Pencereyi başlığına göre bulur (kısmi eşleşme destekler)."""
        try:
            desktop = auto.GetRootControl()
            # Masaüstünün direkt altındaki pencereleri (top-level windows) tara
            titles = title_contains.split('|')
            for win in desktop.GetChildren():
                if win.Name:
                    for t in titles:
                        if t.lower() in win.Name.lower():
                            return win
            
            # Eğer yukarıdaki bulunamazsa klasik arama yap (Regex olmadan daha güvenilir)
            for t in titles:
                win = auto.WindowControl(searchDepth=2, RegexName=f"(?i).*{t}.*")
                if win.Exists(1, 1):
                    return win
        except Exception:
            pass
        return None

    def _focus_window(self, win):
        """Pencereyi güvenli bir şekilde en öne getirir."""
        try:
            win.SetActive()
            win.SetTopmost(True)
            time.sleep(0.3)
        except Exception:
            pass

    def _unfocus_window(self, win):
        """Pencerenin topmost (en önde) kalma durumunu iptal eder."""
        try:
            win.SetTopmost(False)
        except Exception:
            pass

    def verify_window(self, title_contains) -> dict:
        """Belirtilen pencerenin açık olduğunu doğrular."""
        win = self.find_window(title_contains)
        if win:
            return {"ok": True, "verified": True, "title": win.Name}
        return {"ok": False, "verified": False, "error": f"Pencere bulunamadı: {title_contains}"}

    def click_element(self, window_title, control_name=None, control_type=None, depth=5) -> dict:
        """
        Belirtilen pencere içerisindeki spesifik bir UI elemanına (buton, link vb.) tıklar.
        """
        win = self.find_window(window_title)
        if not win:
            return {"ok": False, "verified": False, "error": f"Pencere bulunamadı: {window_title}"}
        
        self._focus_window(win)

        try:
            search_args = {"searchDepth": depth}
            if control_name:
                search_args["Name"] = control_name
            if control_type:
                # auto.ControlType (örn: ButtonControl)
                search_args["ControlType"] = control_type

            # Eğer sadece name verilmişse herhangi bir kontrol tipinde arar
            control = win.Control(**search_args)
            if control.Exists(3, 1):
                control.Click(waitTime=0.5)
                self._unfocus_window(win)
                return {"ok": True, "verified": True, "result": f"Element tıklandı: {control_name or control_type}"}
            else:
                self._unfocus_window(win)
                return {"ok": False, "verified": False, "error": f"Element bulunamadı: {control_name or control_type}"}
        except Exception as e:
            self._unfocus_window(win)
            return {"ok": False, "verified": False, "error": f"OS Tıklama hatası: {e}"}

    def type_text(self, window_title, text, control_name=None, clear_first=False) -> dict:
        """
        Belirtilen pencerede veya spesifik bir metin kutusunda metin yazar.
        """
        win = self.find_window(window_title)
        if not win:
            return {"ok": False, "verified": False, "error": f"Pencere bulunamadı: {window_title}"}
        
        self._focus_window(win)

        try:
            if control_name:
                control = win.EditControl(searchDepth=7, Name=control_name)
                if control.Exists(3, 1):
                    control.Click(waitTime=0.2)
                    if clear_first:
                        control.SendKeys('{Ctrl}a{Delete}')
                    control.SendKeys(text, waitTime=0.5)
                    self._unfocus_window(win)
                    return {"ok": True, "verified": True, "result": f"Metin '{control_name}' kutusuna yazıldı."}
            
            # Spesifik alan yoksa, pencereye odaklanıp doğrudan gönder (Notepad ana alanı gibi)
            if clear_first:
                win.SendKeys('{Ctrl}a{Delete}')
            win.SendKeys(text, waitTime=0.5)
            self._unfocus_window(win)
            return {"ok": True, "verified": True, "result": "Metin aktif pencereye yazıldı."}
        except Exception as e:
            self._unfocus_window(win)
            return {"ok": False, "verified": False, "error": f"OS Yazma hatası: {e}"}

    def window_exists(self, title_contains):
        return self.find_window(title_contains) is not None

# Test bloğu (Doğrudan çalıştırıldığında)
if __name__ == "__main__":
    engine = PabloOSGrounding.get_instance()
    
    print("Notepad test ediliyor...")
    os.system("start notepad.exe")
    time.sleep(2)
    
    # Notepad "Adsız" (Untitled) başlığıyla açılır
    res = engine.type_text("Notepad", "Pablo OS Grounding Testi Basarili!")
    print(f"Yazma sonucu: {res}")
    
    # Notepad kapatma işlemi
    print("Notepad kapatılıyor (Kaydetmeden çıkılacak)...")
    os.system("taskkill /f /im notepad.exe")
