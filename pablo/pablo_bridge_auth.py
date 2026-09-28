"""Pablo's authenticated Bridge worker headers."""


def bridge_worker_headers(config):
    worker_key = config.get('task_worker_key')
    bridge_key = config.get('auth_token')
    worker_id = config.get('node_id')
    if not worker_key or not bridge_key or worker_key == bridge_key or not worker_id:
        raise RuntimeError('Separate Bridge and worker credentials plus node ID are required')
    return {'X-Bridge-Key': bridge_key, 'X-Task-Worker-Key': worker_key,
            'X-Worker-ID': worker_id}
