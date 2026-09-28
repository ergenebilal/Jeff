"""Pablo's authenticated Bridge worker headers."""


def bridge_worker_headers(config):
    worker_key = config.get('task_worker_key')
    bridge_key = config.get('auth_token')
    worker_id = config.get('node_id')
    if not worker_key or not bridge_key or worker_key == bridge_key or not worker_id:
        raise RuntimeError('Separate Bridge and worker credentials plus node ID are required')
    return {'X-Bridge-Key': bridge_key, 'X-Task-Worker-Key': worker_key,
            'X-Worker-ID': worker_id}


def validate_bridge_result_ack(payload, response):
    if response.get('status') == 'quarantined':
        raise RuntimeError('Bridge quarantined result')
    if payload.get('status') == 'APPROVAL_REQUIRED':
        if response.get('status') != 'approval_required' or response.get('handoff') != 'stored':
            raise RuntimeError('Bridge did not persist approval handoff')
    elif response.get('status') != 'unverified':
        raise RuntimeError('Bridge did not acknowledge result')
    return True
