#!/usr/bin/env python3
"""Skill audit: scan SKILL.md files for version, changelog, and last-used info."""

import os
import re
import json
import stat
from datetime import datetime, timezone, timedelta

SKILLS_DIR = os.path.expanduser("~/.hermes/skills")
USAGE_JSON = os.path.join(SKILLS_DIR, ".usage.json")

THIRTY_DAYS = timedelta(days=30)
NOW = datetime.now(timezone.utc)

YAML_VERSION_RE = re.compile(r"^version:\s*(.+)$", re.MULTILINE)
CHANGELOG_HEADING_RE = re.compile(r"^##\s+Changelog", re.MULTILINE)


def load_usage():
    if not os.path.isfile(USAGE_JSON):
        return {}
    with open(USAGE_JSON) as f:
        return json.load(f)


def get_skill_name(skill_dir):
    rel = os.path.relpath(skill_dir, SKILLS_DIR)
    return rel


def parse_skill_md(skill_md_path):
    with open(skill_md_path, encoding="utf-8", errors="replace") as f:
        content = f.read()

    version_match = YAML_VERSION_RE.search(content)
    version = version_match.group(1).strip() if version_match else None

    has_changelog_heading = bool(CHANGELOG_HEADING_RE.search(content))
    return version, has_changelog_heading


def has_changelog_file(skill_dir):
    return os.path.isfile(os.path.join(skill_dir, "CHANGELOG.md"))


def get_last_used(skill_dir, usage_data):
    rel = get_skill_name(skill_dir)
    entry = usage_data.get(rel, {})
    last_used_str = entry.get("last_used_at")
    if last_used_str:
        try:
            return datetime.fromisoformat(last_used_str)
        except (ValueError, TypeError):
            pass

    mtime = os.path.getmtime(os.path.join(skill_dir, "SKILL.md"))
    return datetime.fromtimestamp(mtime, tz=timezone.utc)


def main():
    usage_data = load_usage()

    skill_dirs = []
    for root, dirs, files in os.walk(SKILLS_DIR):
        if "SKILL.md" in files:
            skill_dirs.append(root)

    skill_dirs.sort()

    total = len(skill_dirs)
    version_count = 0
    unused_count = 0

    header = f"{'Skill Adi':<50} {'Version':<12} {'Changelog':<12} {'Son Kullanim':<22} {'Durum'}"
    sep = "-" * len(header)
    print(header)
    print(sep)

    for sd in skill_dirs:
        skill_name = get_skill_name(sd)
        skill_md = os.path.join(sd, "SKILL.md")

        version, has_cl_heading = parse_skill_md(skill_md)
        has_cl_file = has_changelog_file(sd)
        has_changelog = has_cl_heading or has_cl_file

        last_used = get_last_used(sd, usage_data)
        last_used_str = last_used.strftime("%Y-%m-%d %H:%M")

        age = NOW - last_used
        durum = "KULLANILMIYOR" if age > THIRTY_DAYS else "AKTIF"

        v_display = version if version else "-"
        cl_display = "VAR" if has_changelog else "YOK"

        if version:
            version_count += 1
        if age > THIRTY_DAYS:
            unused_count += 1

        print(f"{skill_name:<50} {v_display:<12} {cl_display:<12} {last_used_str:<22} {durum}")

    print()
    print(f"{version_count}/{total} skill'de version var, {unused_count} tanesi kullanilmiyor.")


if __name__ == "__main__":
    main()
