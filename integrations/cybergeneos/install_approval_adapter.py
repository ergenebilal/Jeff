"""Produce a reviewed two-line panel patch, idempotently; no implicit deployment."""
from pathlib import Path
import sys

def patch(source):
    if 'install_approval_adapter(sys.modules[__name__])' in source:return source
    old='    store = Store(DATA / "cgos.db")\n'
    route='return act_approval(r[1], r[2], body)'
    if source.count(old)!=1 or source.count(route)!=1:raise RuntimeError('Panel source changed; cannot apply reviewed anchors')
    source=source.replace(old,old+'    from .approval_adapter import install as install_approval_adapter\n    install_approval_adapter(sys.modules[__name__])\n')
    return source.replace(route,'return act_approval(r[1], r[2], body, actor=self.by)')

if __name__=='__main__':
    path=Path(sys.argv[1]);path.write_text(patch(path.read_text()),encoding='utf-8')
