"""Validate the published task JSON schema against the real ledger response."""
import json
from pathlib import Path
import sys
import tempfile

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'jeff2' / 'bridge'))
from task_contract import TaskConflict, TaskCreate, TaskLedger, TRANSITIONS


def main():
    schema = json.loads((ROOT / 'schemas' / 'task-contract.schema.json').read_text(encoding='utf-8'))
    Draft202012Validator.check_schema(schema)
    statuses = set(schema['properties']['status']['enum'])
    if statuses != set(TRANSITIONS):
        raise AssertionError('Schema and state machine statuses differ')
    with tempfile.TemporaryDirectory() as temporary:
        ledger = TaskLedger(Path(temporary) / 'tasks.db')
        ledger.initialize()
        body = TaskCreate(task_id='schema-smoke', source='schema', goal='Check health',
                          success_criteria=['pablo_health_ok'], risk_level='low',
                          side_effect_class='none', approval_required=False)
        task = ledger.create(body)
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(task)
        if ledger.create(body)['task_id'] != task['task_id']:
            raise AssertionError('Immutable replay changed task identity')
        try:
            ledger.create(body.model_copy(update={'goal': 'Changed goal'}))
        except TaskConflict:
            pass
        else:
            raise AssertionError('Changed digest was not rejected')
    print('TASK_SCHEMA_VALID=1; CHANGED_DIGEST_REJECTED=1')


if __name__ == '__main__':
    main()
