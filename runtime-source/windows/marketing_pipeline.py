#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CYBERGENE MARKETING PIPELINE DATABASE & DATA ACCESS LAYER
---------------------------------------------------------
7/24 Otonom B2B Pazarlama Süreç Yönetimi:
- Leads: Müşteri adayları (doğrulanmış şirket bilgileri, makine parkı, iletişim kanalları)
- Campaigns: Kişiselleştirilmiş temas taslakları ve onay akışları (DRAFTED -> PENDING_APPROVAL -> APPROVED -> SENT)
- ExecutionLogs: Playbook icra logları, süreler ve kanıt ekran görüntüleri
"""

import sqlite3
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

DB_PATH = Path(r"C:\CyberGene\Marketing\marketing_pipeline.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

from contextlib import contextmanager

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(str(DB_PATH), timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    try:
        yield conn
    finally:
        conn.close()

def init_marketing_db():
    """Veritabanı tablolarını ve indekslerini oluşturur."""
    with get_db_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL UNIQUE,
            website TEXT NOT NULL,
            industry TEXT,
            location TEXT,
            verified_phone TEXT,
            verified_email TEXT,
            verified_whatsapp TEXT,
            capacity_notes TEXT,
            facts_verified TEXT,      -- Doğrulanan somut gerçekler (JSON array)
            assumptions TEXT,         -- İspatlanmamış sektörel varsayımlar (JSON array)
            fact_check_status TEXT DEFAULT 'VERIFIED', -- 'PENDING', 'VERIFIED', 'FLAGGED'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS outreach_campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            channel TEXT NOT NULL,     -- 'email', 'web_form', 'instagram', 'linkedin'
            recipient_target TEXT,     -- e-posta adresi, profil URL'i veya form URL'i
            subject TEXT,
            message_body TEXT NOT NULL,
            value_prop TEXT,
            status TEXT DEFAULT 'DRAFTED', -- 'DRAFTED', 'PENDING_APPROVAL', 'APPROVED', 'SENT', 'REJECTED', 'FAILED'
            approval_requested_at TIMESTAMP,
            approved_at TIMESTAMP,
            approved_by TEXT,
            sent_at TIMESTAMP,
            screenshot_proof TEXT,
            error_log TEXT,
            retry_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES leads (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS playbook_execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER,
            playbook_name TEXT NOT NULL,
            action_type TEXT NOT NULL,
            duration_ms INTEGER,
            status TEXT NOT NULL,       -- 'SUCCESS', 'FAILED', 'VERIFIED'
            evidence_screenshot TEXT,
            details TEXT,               -- JSON details
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (campaign_id) REFERENCES outreach_campaigns (id) ON DELETE SET NULL
        );

        -- Instagram içerik öneri kuyruğu (yalnız METİN katmanı: konu/brief/caption taslağı).
        -- Gerçek görsel üretim ve yayın bu tabloya dahil DEĞİLDİR; bkz.
        -- docs/cybergene-instagram-playbook-v1.0.md §7 otomasyon sınır matrisi.
        CREATE TABLE IF NOT EXISTS instagram_content_ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id TEXT,                 -- örn. 'P06'
            visual_family TEXT,              -- Dönüşüm / Görev sınırı / Karar sayfası / İş dosyası / İz sürme
            site_pillar TEXT,                -- cybergene_site_taxonomy.py: SITE_PILLARS
            target_reader TEXT,
            problem TEXT,
            single_takeaway TEXT,
            mechanism TEXT,
            human_control_note TEXT,
            evidence_type TEXT,              -- master-v0.1.md §5 kanıt türleri
            evidence_source TEXT,
            hook_text TEXT,                  -- kapak metni
            caption_draft TEXT,
            proposed_by TEXT,                -- kim önerdi (ör. 'jeff_llm', 'claude_session', 'manual')
            gate_status TEXT DEFAULT 'PENDING_GATE',  -- PENDING_GATE, GATE_PASSED, GATE_REJECTED
            gate_notes TEXT,                 -- JSON: run_editorial_gate() gerekçeleri
            status TEXT DEFAULT 'DRAFTED',   -- DRAFTED, PENDING_APPROVAL, APPROVED_FOR_ART_DIRECTION, REJECTED
            approval_requested_at TIMESTAMP,
            approved_at TIMESTAMP,
            approved_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_leads_company ON leads (company_name);
        CREATE INDEX IF NOT EXISTS idx_campaigns_status ON outreach_campaigns (status);
        CREATE INDEX IF NOT EXISTS idx_campaigns_lead ON outreach_campaigns (lead_id);
        CREATE INDEX IF NOT EXISTS idx_content_ideas_status ON instagram_content_ideas (status);
        """)
        conn.commit()

        # Basit idempotent migrasyon: instagram_content_ideas tablosu bu sütun
        # eklenmeden önce oluşturulmuş olabilir (CREATE TABLE IF NOT EXISTS mevcut
        # tabloyu değiştirmez).
        existing_cols = {row["name"] for row in conn.execute("PRAGMA table_info(instagram_content_ideas)")}
        if "site_pillar" not in existing_cols:
            conn.execute("ALTER TABLE instagram_content_ideas ADD COLUMN site_pillar TEXT")
            conn.commit()

class MarketingPipeline:

    @staticmethod
    def review_message(message: str, company_name: str = '') -> Dict[str, Any]:
        import urllib.request
        started=time.perf_counter()
        try:
            config=json.loads((Path(__file__).parent/'config.json').read_text(encoding='utf-8'))
            req=urllib.request.Request(config['jeff_bridge_api_url'].rstrip('/')+'/ade/outreach-review',
                data=json.dumps({'message':message,'company_name':company_name},ensure_ascii=False).encode(),
                headers={'Content-Type':'application/json','X-Bridge-Key':config['auth_token']})
            with urllib.request.urlopen(req,timeout=2.8) as response:result=json.load(response)
            if not isinstance(result,dict) or result.get('status') not in ('READY_FOR_FOUNDER_REVIEW','REVISION_REQUIRED','UNAVAILABLE'):raise ValueError()
            elapsed=round((time.perf_counter()-started)*1000,3);result['end_to_end_latency_ms']=elapsed
            if elapsed>=3000:result.update(status='UNAVAILABLE',ready_for_founder_review=False,reason='Müşteri süzgeci süre sınırını aştı.')
            return result
        except (OSError,ValueError,KeyError,TypeError):
            return {'status':'UNAVAILABLE','ready_for_founder_review':False,'ready_for_send':False,
                    'founder_inner_approval':None,'reason':'Gerçek müşteri kontrolü tamamlanamadı.',
                    'end_to_end_latency_ms':round((time.perf_counter()-started)*1000,3)}

    @staticmethod
    def record_contact_event(lead_id: int, kind: str, source: str, request_id: str, detail: str = '') -> int:
        """Node always requires input-bound owner approval for this action."""
        if kind not in ('positive_reply','meeting_confirmed') or not source.strip() or not request_id:
            raise ValueError('Owner-confirmed contact source required')
        if MarketingPipeline.get_lead(lead_id) is None:raise ValueError('Unknown lead')
        return MarketingPipeline.log_execution('lead_stage',kind,'OWNER_CONFIRMED',details={
            'lead_id':lead_id,'source':source[:500],'request_id':request_id,'detail':detail[:2000],
            'recorded_at':time.time(),'not_a_customer_outcome':True})

    @staticmethod
    def deep_analysis_gate(lead_id: int) -> Dict[str, Any]:
        from contextlib import closing
        with get_db_connection() as conn:
            rows=conn.execute("SELECT action_type,details FROM playbook_execution_logs WHERE playbook_name='lead_stage' AND status='OWNER_CONFIRMED' AND action_type IN ('positive_reply','meeting_confirmed') ORDER BY id DESC").fetchall()
        journal=Path(__file__).parent/'task-journal.sqlite3'
        for row in rows:
            try:
                details=json.loads(row['details'])
                if details.get('lead_id')!=lead_id:continue
                with closing(sqlite3.connect(journal.resolve().as_uri()+'?mode=ro',uri=True,timeout=2)) as db:
                    bound=db.execute('SELECT action,consumed,canonical_claim,status FROM requests WHERE id=?',(details['request_id'],)).fetchone()
                if bound and bound[0]=='marketing_contact_event' and bound[1]==1 and bound[2] and bound[3] in ('SUCCESS','EXECUTION_SUCCEEDED'):
                    return {'eligible':True,'reason':row['action_type'],'source':details['source'],'contact_request_id':details['request_id']}
            except (OSError,ValueError,KeyError,sqlite3.Error):continue
        return {'eligible':False,'reason':'No owner-confirmed positive reply or meeting; radar only.'}

    @staticmethod
    def prepare_deep_analysis(lead_id: int) -> Dict[str, Any]:
        gate=MarketingPipeline.deep_analysis_gate(lead_id)
        if not gate['eligible']:return {'ok':False,'status':'RADAR_ONLY','gate':gate,'model_calls':0}
        lead=MarketingPipeline.get_lead(lead_id)
        return {'ok':True,'status':'DEEP_ANALYSIS_ELIGIBLE','gate':gate,'lead':lead,
                'source_requirements':['authorized Google review source','source-backed blind spots','owner-supplied appointment loss data'],
                'appointment_loss_verified':False,'model_calls':0,
                'reason':'Derin kaynakları topla; eksik veri veya kayıp sayısı uydurma.'}

    @staticmethod
    def analyze_eligible_lead(lead_id: int, sources: List[Dict[str, Any]], appointment_records: List[Dict[str, Any]], request_id: str) -> Dict[str, Any]:
        """Analyze owner-approved source material, not scraped reviews or invented losses."""
        import re
        from contextlib import closing
        gate=MarketingPipeline.deep_analysis_gate(lead_id)
        if not gate['eligible']:return {'ok':False,'status':'RADAR_ONLY','gate':gate,'model_calls':0}
        with closing(sqlite3.connect((Path(__file__).parent/'task-journal.sqlite3').resolve().as_uri()+'?mode=ro',uri=True,timeout=2)) as db:
            claim=db.execute('SELECT action,consumed,canonical_claim,status FROM requests WHERE id=?',(request_id,)).fetchone()
        if not claim or claim[0]!='marketing_deep_analyze' or claim[1]!=1 or not claim[2] or claim[3] not in ('IN_PROGRESS','SUCCESS','EXECUTION_SUCCEEDED'):
            return {'ok':False,'status':'OWNER_SOURCE_AUTHORIZATION_REQUIRED','model_calls':0}
        if not isinstance(sources,list) or len(sources)>30 or not isinstance(appointment_records,list) or len(appointment_records)>1000:
            raise ValueError('Bounded authorized source material required')
        observations=[];themes={};missing=[]
        for item in sources:
            if not isinstance(item,dict) or item.get('kind') not in ('google_reviews_owner_export','google_reviews_official_api','business_owner_note'):
                raise ValueError('Use authorized Google material or business owner notes')
            source=str(item.get('source','')).strip();excerpt=str(item.get('excerpt','')).strip()
            if not source or not excerpt or len(excerpt)>2000 or len(source)>500:raise ValueError('Source reference and bounded anonymized excerpt required')
            text=excerpt.casefold().replace('i̇','i')
            matched=[label for label,pattern in [('response','yanıt|cevap|dönüş'),('appointment','randevu|rezervasyon'),('waiting','bekle|gecik'),('communication','iletişim|telefon|mesaj')] if re.search(pattern,text)]
            for label in matched:themes[label]=themes.get(label,0)+1
            observations.append({'source':source,'kind':item['kind'],'excerpt':excerpt,'themes':matched,
                'evidence_level':'OWNER_SUPPLIED','independently_verified':False})
        reported_missed=[x for x in appointment_records if isinstance(x,dict) and x.get('status')=='missed' and x.get('source')]
        if not sources:missing.append('Yetkili yorum veya işletme notu yok; yorum analizi yapılmadı.')
        if not appointment_records:missing.append('Gerçek randevu kayıtları yok; kayıp sayısı hesaplanmadı.')
        hypotheses=[{'hypothesis':'Randevu mesajlarının geri dönüş süreci görüşmede sorulmalı.',
            'basis':[o['source'] for o in observations if 'response' in o['themes'] or 'appointment' in o['themes']],
            'level':'HYPOTHESIS','verified_business_problem':False}] if themes.get('response') or themes.get('appointment') else []
        report={'ok':True,'status':'SOURCE_ANALYSIS_RECORDED','lead_id':lead_id,'gate':gate,
            'observations':observations,'review_theme_counts':themes,'counts_scope':'Only supplied excerpts; not all Google reviews.',
            'blind_spot_hypotheses':hypotheses,'owner_reported_missed_appointments':len(reported_missed) if appointment_records else None,
            'appointment_loss_verified':False,'revenue_loss':None,'missing':missing,'model_calls':0,
            'method':'Bounded source extraction and keyword themes; not semantic model assessment.','ready_for_send':False}
        report['record_id']=MarketingPipeline.log_execution('lead_stage','deep_analysis','SOURCE_ANALYSIS_RECORDED',details={
            'request_id':request_id,'lead_id':lead_id,'report':report})
        return report

    @staticmethod
    def add_or_update_lead(
        company_name: str,
        website: str,
        industry: str = "",
        location: str = "",
        verified_phone: str = "",
        verified_email: str = "",
        verified_whatsapp: str = "",
        capacity_notes: str = "",
        facts_verified: List[str] = None,
        assumptions: List[str] = None,
        fact_check_status: str = "VERIFIED"
    ) -> int:
        facts_json = json.dumps(facts_verified or [], ensure_ascii=False)
        assump_json = json.dumps(assumptions or [], ensure_ascii=False)
        with get_db_connection() as conn:
            cur = conn.execute("""
            INSERT INTO leads (
                company_name, website, industry, location,
                verified_phone, verified_email, verified_whatsapp,
                capacity_notes, facts_verified, assumptions, fact_check_status, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(company_name) DO UPDATE SET
                website=excluded.website,
                industry=excluded.industry,
                location=excluded.location,
                verified_phone=excluded.verified_phone,
                verified_email=excluded.verified_email,
                verified_whatsapp=excluded.verified_whatsapp,
                capacity_notes=excluded.capacity_notes,
                facts_verified=excluded.facts_verified,
                assumptions=excluded.assumptions,
                fact_check_status=excluded.fact_check_status,
                updated_at=CURRENT_TIMESTAMP
            """, (company_name, website, industry, location, verified_phone, verified_email, verified_whatsapp, capacity_notes, facts_json, assump_json, fact_check_status))
            conn.commit()
            row = conn.execute("SELECT id FROM leads WHERE company_name = ?", (company_name,)).fetchone()
            return row["id"]

    @staticmethod
    def get_lead(lead_id: int) -> Optional[Dict[str, Any]]:
        with get_db_connection() as conn:
            row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def list_leads() -> List[Dict[str, Any]]:
        with get_db_connection() as conn:
            rows = conn.execute("SELECT * FROM leads ORDER BY id DESC").fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def create_campaign(
        lead_id: int,
        channel: str,
        recipient_target: str,
        subject: str,
        message_body: str,
        value_prop: str = "",
        status: str = "DRAFTED"
    ) -> int:
        lead=MarketingPipeline.get_lead(lead_id)
        if lead is None:raise ValueError('Unknown lead')
        review=MarketingPipeline.review_message(message_body,lead['company_name'])
        raw_body=message_body
        if review.get('ready_for_founder_review') is True:
            message_body=review.get('suggested_body',message_body)
            if status not in ('DRAFTED','PENDING_APPROVAL'):raise ValueError('A draft does not grant publication')
        else:status='REVIEW_BLOCKED'
        with get_db_connection() as conn:
            cur = conn.execute("""
            INSERT INTO outreach_campaigns (
                lead_id, channel, recipient_target, subject, message_body, value_prop, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (lead_id, channel, recipient_target, subject, message_body, value_prop, status))
            campaign_id=cur.lastrowid
            conn.execute('INSERT INTO playbook_execution_logs(campaign_id,playbook_name,action_type,duration_ms,status,details) VALUES(?,?,?,?,?,?)',
                (campaign_id,'customer_filter','draft_review',int(review.get('end_to_end_latency_ms',0)),review['status'],json.dumps({'raw_body':raw_body,'final_body':message_body,'ADE':review,'founder_approval':None},ensure_ascii=False)))
            conn.commit()
            return campaign_id

    @staticmethod
    def get_campaign(campaign_id: int) -> Optional[Dict[str, Any]]:
        with get_db_connection() as conn:
            row = conn.execute("""
            SELECT c.*, l.company_name, l.website, l.industry, l.location, l.verified_phone, l.verified_email
            FROM outreach_campaigns c
            JOIN leads l ON c.lead_id = l.id
            WHERE c.id = ?
            """, (campaign_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def list_campaigns(status: Optional[str] = None) -> List[Dict[str, Any]]:
        with get_db_connection() as conn:
            if status:
                rows = conn.execute("""
                SELECT c.*, l.company_name, l.website
                FROM outreach_campaigns c
                JOIN leads l ON c.lead_id = l.id
                WHERE c.status = ?
                ORDER BY c.id DESC
                """, (status,)).fetchall()
            else:
                rows = conn.execute("""
                SELECT c.*, l.company_name, l.website
                FROM outreach_campaigns c
                JOIN leads l ON c.lead_id = l.id
                ORDER BY c.id DESC
                """).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def update_campaign_status(
        campaign_id: int,
        status: str,
        approved_by: Optional[str] = None,
        screenshot_proof: Optional[str] = None,
        error_log: Optional[str] = None
    ):
        with get_db_connection() as conn:
            now = time.strftime("%Y-%m-%d %H:%M:%S")
            if status == "PENDING_APPROVAL":
                conn.execute("UPDATE outreach_campaigns SET status = ?, approval_requested_at = ? WHERE id = ?", (status, now, campaign_id))
            elif status == "APPROVED":
                row=conn.execute('SELECT c.message_body,l.company_name FROM outreach_campaigns c JOIN leads l ON l.id=c.lead_id WHERE c.id=?',(campaign_id,)).fetchone()
                if row is None or MarketingPipeline.review_message(row['message_body'],row['company_name']).get('ready_for_founder_review') is not True:
                    raise ValueError('Current customer filter unavailable or unresolved')
                conn.execute("UPDATE outreach_campaigns SET status = ?, approved_at = ?, approved_by = ? WHERE id = ?", (status, now, approved_by or "bilal_telegram", campaign_id))
            elif status == "SENT":
                conn.execute("UPDATE outreach_campaigns SET status = ?, sent_at = ?, screenshot_proof = ? WHERE id = ?", (status, now, screenshot_proof, campaign_id))
            elif status in ("REJECTED", "FAILED"):
                conn.execute("UPDATE outreach_campaigns SET status = ?, error_log = ? WHERE id = ?", (status, error_log, campaign_id))
            else:
                conn.execute("UPDATE outreach_campaigns SET status = ? WHERE id = ?", (status, campaign_id))
            conn.commit()

    @staticmethod
    def log_execution(
        playbook_name: str,
        action_type: str,
        status: str,
        campaign_id: Optional[int] = None,
        duration_ms: int = 0,
        evidence_screenshot: str = "",
        details: Dict[str, Any] = None
    ) -> int:
        details_json = json.dumps(details or {}, ensure_ascii=False)
        with get_db_connection() as conn:
            cur = conn.execute("""
            INSERT INTO playbook_execution_logs (
                campaign_id, playbook_name, action_type, duration_ms, status, evidence_screenshot, details
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (campaign_id, playbook_name, action_type, duration_ms, status, evidence_screenshot, details_json))
            conn.commit()
            return cur.lastrowid

    # ------------------------------------------------------------------
    # Instagram içerik öneri kuyruğu (metin katmanı)
    # ------------------------------------------------------------------
    @staticmethod
    def create_content_idea(
        content_id: str,
        visual_family: str,
        site_pillar: str,
        target_reader: str,
        problem: str,
        single_takeaway: str,
        mechanism: str,
        human_control_note: str,
        evidence_type: str,
        hook_text: str,
        caption_draft: str,
        evidence_source: str = "",
        proposed_by: str = "manual",
        gate_status: str = "PENDING_GATE",
        gate_notes: Optional[List[str]] = None,
        status: str = "DRAFTED",
    ) -> int:
        with get_db_connection() as conn:
            cur = conn.execute("""
            INSERT INTO instagram_content_ideas (
                content_id, visual_family, site_pillar, target_reader, problem, single_takeaway,
                mechanism, human_control_note, evidence_type, evidence_source,
                hook_text, caption_draft, proposed_by, gate_status, gate_notes, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                content_id, visual_family, site_pillar, target_reader, problem, single_takeaway,
                mechanism, human_control_note, evidence_type, evidence_source,
                hook_text, caption_draft, proposed_by, gate_status,
                json.dumps(gate_notes or [], ensure_ascii=False), status,
            ))
            conn.commit()
            return cur.lastrowid

    @staticmethod
    def get_content_idea(idea_id: int) -> Optional[Dict[str, Any]]:
        with get_db_connection() as conn:
            row = conn.execute("SELECT * FROM instagram_content_ideas WHERE id = ?", (idea_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def list_content_ideas(status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        with get_db_connection() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM instagram_content_ideas WHERE status = ? ORDER BY id DESC LIMIT ?",
                    (status, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM instagram_content_ideas ORDER BY id DESC LIMIT ?", (limit,)
                ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def update_content_idea_status(
        idea_id: int,
        status: str,
        approved_by: Optional[str] = None,
    ):
        with get_db_connection() as conn:
            now = time.strftime("%Y-%m-%d %H:%M:%S")
            if status == "PENDING_APPROVAL":
                conn.execute(
                    "UPDATE instagram_content_ideas SET status = ?, approval_requested_at = ? WHERE id = ?",
                    (status, now, idea_id),
                )
            elif status == "APPROVED_FOR_ART_DIRECTION":
                conn.execute(
                    "UPDATE instagram_content_ideas SET status = ?, approved_at = ?, approved_by = ? WHERE id = ?",
                    (status, now, approved_by or "bilal_telegram", idea_id),
                )
            else:
                conn.execute("UPDATE instagram_content_ideas SET status = ? WHERE id = ?", (status, idea_id))
            conn.commit()

if __name__ == "__main__":
    init_marketing_db()
    print("Marketing database initialized at:", DB_PATH)
