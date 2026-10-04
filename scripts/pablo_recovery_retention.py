"""Keep bounded, independently validated managed recovery capsules only."""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time

NAME = re.compile(r'\d{8}T\d{6}Z-[a-f0-9]{32}')
RECEIPT = '.retention-receipt.json'


def safe_path(path, root):
    """Reject redirects in every ancestor before reading or removing a target."""
    root = Path(root).absolute(); path = Path(path).absolute()
    if not path.is_relative_to(root): raise ValueError('Recovery target escaped storage')
    for part in [path] + list(path.parents):
        info = part.lstat()
        if part.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('Redirected recovery target')
    if not path.resolve().is_relative_to(root.resolve()): raise ValueError('Recovery path escaped storage')
    return path


def digest(path):
    with path.open('rb') as handle: return hashlib.file_digest(handle, 'sha256').hexdigest()


def inventory(base, root):
    safe_path(base, root)
    files = set(); directories = []
    for directory, children, names in os.walk(base, followlinks=False):
        safe_path(directory, root); directories.append(Path(directory))
        for name in children: safe_path(Path(directory)/name, root)
        for name in names:
            path = safe_path(Path(directory)/name, root)
            if not path.is_file(): raise ValueError('Unknown recovery member')
            files.add(path.relative_to(base).as_posix())
    return files, directories


def validate_capsule(base, root, receipt, validate, allow_missing_receipt=False):
    base = safe_path(base, root)
    if not NAME.fullmatch(base.name) or receipt.get('name') != base.name: raise ValueError('Unknown recovery capsule')
    if receipt.get('version') != 1 or receipt.get('managed_by') != 'pablo_recovery_monitor' or receipt.get('remote_manifest_verified') is not True:
        raise ValueError('No managed recovery acceptance')
    timestamp = receipt.get('verified_at')
    if type(timestamp) not in (int, float) or not math.isfinite(timestamp) or not 0 <= timestamp <= time.time():
        raise ValueError('Invalid recovery acceptance time')
    layout = receipt.get('layout')
    if layout not in ('local', 'remote'): raise ValueError('Unknown recovery layout')
    image = base if layout == 'local' else base/'snapshot'
    members, directories = inventory(base, root)
    manifest = validate(image)
    prefix = '' if layout == 'local' else 'snapshot/'
    expected = {prefix+'manifest.json', 'windows-snapshot.zip'} | {prefix+e['path'] for e in manifest['entries']}
    if not allow_missing_receipt or RECEIPT in members: expected.add(RECEIPT)
    if members != expected: raise ValueError('Recovery capsule has unknown or missing files')
    expected_directories = {base}
    for member in expected:
        parent = (base/member).parent
        while parent != base:
            expected_directories.add(parent); parent = parent.parent
    if set(directories) != expected_directories: raise ValueError('Recovery capsule has unknown directories')
    archive = safe_path(base/'windows-snapshot.zip', root)
    if type(receipt.get('archive_bytes')) is not int or archive.stat().st_size != receipt['archive_bytes']:
        raise ValueError('Recovery archive size changed')
    if digest(archive) != receipt.get('archive_sha256') or digest(image/'manifest.json') != receipt.get('manifest_sha256'):
        raise ValueError('Recovery capsule content changed')
    if manifest['source_release'] != receipt.get('source_release'): raise ValueError('Recovery release changed')
    return manifest


def record_verified(base, root, layout, proof, validate):
    """Called only after remote archive hash, complete manifest and DB verification."""
    if proof.get('ok') is not True or proof.get('remote_manifest_verified') is not True:
        raise ValueError('No actual remote recovery proof')
    base = safe_path(base, root)
    image = base if layout == 'local' else base/'snapshot'
    receipt = {key: proof[key] for key in ('archive_bytes', 'archive_sha256', 'source_release')}
    receipt.update(version=1, managed_by='pablo_recovery_monitor', name=base.name, layout=layout,
                   remote_manifest_verified=True, verified_at=time.time(), remote_verified_at=proof['verified_at'],
                   manifest_sha256=digest(image/'manifest.json'))
    validate_capsule(base, root, receipt, validate, allow_missing_receipt=True)
    target = base/RECEIPT
    if target.exists():
        if json.loads(target.read_text()) != receipt: raise ValueError('Existing retention receipt differs')
        return receipt
    with target.open('x', encoding='utf-8') as handle: json.dump(receipt, handle, indent=2)
    if os.name != 'nt': target.chmod(0o600)
    return receipt


def prune(root, current, validate, keep=14):
    if type(keep) is not int or not 1 <= keep <= 30: raise ValueError('Invalid recovery retention limit')
    root = safe_path(root, root); current = safe_path(root/current, root)
    # An invalid current image must never cause an older good image to disappear.
    current_receipt = json.loads(safe_path(current/RECEIPT, root).read_text())
    validate_capsule(current, root, current_receipt, validate)
    candidates = []; preserved = 0
    for base in root.iterdir():
        if not NAME.fullmatch(base.name): continue  # Historical/manual folders are outside management.
        try:
            receipt = json.loads(safe_path(base/RECEIPT, root).read_text())
            validate_capsule(base, root, receipt, validate)
            if receipt['layout'] != current_receipt['layout']: raise ValueError('Mixed recovery layout')
            candidates.append((receipt['verified_at'], base.name, base, receipt))
        except Exception: preserved += 1
    candidates.sort(reverse=True)
    protected = {entry[1] for entry in candidates[:keep]} | {current.name}
    removed = []
    for _, name, base, receipt in candidates:
        if name in protected: continue
        # Validate again directly before removing exact known members. No recursive delete.
        validate_capsule(base, root, receipt, validate)
        files, directories = inventory(base, root)
        for member in sorted(files): safe_path(base/member, root).unlink()
        for directory in sorted(directories, key=lambda p: len(p.parts), reverse=True): safe_path(directory, root).rmdir()
        removed.append(name)
    return {'keep_verified_images': keep, 'removed_verified_images': len(removed),
            'retained_verified_images': len(candidates)-len(removed), 'unmanaged_or_invalid_generated_images_preserved': preserved,
            'current_image_preserved': current.is_dir()}
