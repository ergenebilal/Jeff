"""Periodic expiry with compatibility projection. No approval ever renews itself."""
import asyncio
import logging
from approval_ledger import ApprovalLedger

def sweep(path):
    ledger=ApprovalLedger(path); count=ledger.expire()
    with ledger.connect() as db:
        db.execute("UPDATE task_approvals SET status='expired' WHERE status='pending' AND approval_id IN (SELECT approval_id FROM approval_records WHERE status='expired')")
    return count

async def run(path):
    while True:
        try:await asyncio.to_thread(sweep,path)
        except Exception as exc:logging.getLogger(__name__).error('Approval maintenance unavailable: %s',type(exc).__name__)
        await asyncio.sleep(60)
