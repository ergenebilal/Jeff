# CyberWorker Service - Injected Fault
import sys

def process_payload(data: dict):
    # Intentional bug: 'retrun' typo instead of 'return'
    return {'status': 'processed', 'data': data}
