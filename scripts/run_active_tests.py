"""Run the active unittest suites from the repository root with one command."""
import argparse
import os
from pathlib import Path
import shlex
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_TESTS = [
    'scripts.test_server_ip',
    'scripts.test_executive_briefing',
    'scripts.test_ci_secret_scan',
    'scripts.test_system_watchdog',
    'scripts.test_morning_report',
    'scripts.test_lead_alert',
    'scripts.test_jeff_status',
    'scripts.test_jeff_backup',
    'scripts.test_model_health',
    'scripts.test_pablo_drift',
    'jeff2.bridge.test_task_contract',
    'jeff2.bridge.test_task_http',
    'jeff2.bridge.test_bridge_security',
    'jeff2.bridge.test_coding_bridge',
    'test_pablo_brain',
    'test_clinic_pitch',
    'test_marketing_callback_guard',
]
CONTRACT_TESTS = [
    'jeff2.bridge.contract_tests.test_cybergene_contract',
]


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--group', choices=('all', 'bridge', 'contract'), default='all')
    args = parser.parse_args(argv)
    env = os.environ.copy()
    extra = [ROOT, ROOT / 'jeff2' / 'bridge', ROOT / 'pablo',
             ROOT / 'jeff2' / 'bridge' / 'contract_tests']
    env['PYTHONPATH'] = os.pathsep.join(str(path) for path in extra)
    groups = ([('bridge', BRIDGE_TESTS), ('contract', CONTRACT_TESTS)]
              if args.group == 'all' else
              [(args.group, BRIDGE_TESTS if args.group == 'bridge' else CONTRACT_TESTS)])
    for name, modules in groups:
        print(f'Running {name} unittest suite', flush=True)
        if name == 'contract' and sys.platform == 'win32':
            linux_root = '/mnt/' + ROOT.drive[0].lower() + ROOT.as_posix()[2:]
            paths = [linux_root, linux_root + '/jeff2/bridge', linux_root + '/pablo',
                     linux_root + '/jeff2/bridge/contract_tests']
            command = ('cd ' + shlex.quote(linux_root) + ' && PYTHONPATH='
                       + shlex.quote(':'.join(paths)) + ' python3 -m unittest -q '
                       + ' '.join(shlex.quote(module) for module in modules))
            result = subprocess.run(['wsl', 'bash', '-lc', command], check=False)
        else:
            result = subprocess.run([sys.executable, '-m', 'unittest', '-q', *modules],
                                    cwd=ROOT, env=env, check=False)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == '__main__':
    sys.exit(main())
