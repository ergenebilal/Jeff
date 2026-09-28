#!/usr/bin/env python3
"""
JEFF Completion Protocol v1.0
Komut bekleme sorununu kalıcı çözen motor.
Her işe başlamadan önce tüm adımları planla, tek seansta bitir.
"""

import os
import json
import sys
from datetime import datetime

class CompletionProtocol:
    """
    Kullanım: 
    cp = CompletionProtocol(task="Ne yapılacak")
    cp.add_step("Adım 1", tools=["web_search", "read_file"])
    cp.add_step("Adım 2", tools=["terminal"])
    cp.execute()  # Tüm adımları sırayla çalıştırır, durmaz
    """
    
    def __init__(self, task: str, context: str = ""):
        self.task = task
        self.context = context
        self.steps = []
        self.current_step = 0
        self.log = []
        
    def add_step(self, description: str, depends_on=None, requires_approval=False):
        """İş adımı ekle. depends_on: önceki adımın sonucu gerekli mi?"""
        step = {
            "id": len(self.steps) + 1,
            "description": description,
            "depends_on": depends_on,
            "requires_approval": requires_approval,
            "status": "pending"
        }
        self.steps.append(step)
        return step["id"]
    
    def plan(self):
        """Tüm planı göster"""
        print(f"\n{'='*50}")
        print(f"📋 JEFF COMPLETION PROTOCOL")
        print(f"{'='*50}")
        print(f"Görev: {self.task}")
        if self.context:
            print(f"Bağlam: {self.context[:100]}...")
        print(f"\nAdımlar ({len(self.steps)}):")
        for s in self.steps:
            status_icon = "⏳" if s["status"] == "pending" else "✅" if s["status"] == "done" else "❌"
            approval = " 🛑 ONAY GEREK" if s["requires_approval"] else ""
            dep = f" → depends: {s['depends_on']}" if s.get("depends_on") else ""
            print(f"  {status_icon} {s['id']}. {s['description']}{approval}{dep}")
        print(f"{'='*50}\n")
    
    def execute(self):
        """Planı uygula - HER ŞEYİ TEK SEANSTA BİTİR"""
        self.plan()
        
        for step in self.steps:
            if step["status"] == "done":
                continue
                
            if step["requires_approval"]:
                print(f"\n⏸️  ADIM {step['id']} ONAY BEKLİYOR: {step['description']}")
                print("⚠️  Bu adım kullanıcı onayı gerektiriyor — durduruldu.")
                return False
                
            step["status"] = "in_progress"
            self.current_step = step["id"]
            self.log.append(f"[{datetime.now().isoformat()}] 📍 Adım {step['id']}: {step['description']}")
            
            # Adım simüle edilmez, Hermes tool çağrıları ile yapılır
            # Bu sadece planlama ve takip için
            print(f"  ▶️  Adım {step['id']}: {step['description']}")
            
        print(f"\n✅ PLAN TAMAM — {len(self.steps)} adım")
        return True

if __name__ == "__main__":
    # Test modu
    cp = CompletionProtocol("Test görevi")
    cp.add_step("Web'den veri topla")
    cp.add_step("Dosyaya yaz")
    cp.plan()
