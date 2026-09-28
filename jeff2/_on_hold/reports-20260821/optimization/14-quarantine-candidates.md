# Quarantine Candidates
# Generated: 2026-08-17T14:15:00+03:00

# NOT: Hiçbir şey silinmedi. Bu dosya adayları listeler.
# Onay sonrası ACTIVE → CANDIDATE → QUARANTINED → ARCHIVED akışı uygulanır.

quarantine_candidates:
  projects:
    - name: ecc-system
      path: /opt/ecc-system
      reason: Son 60 günde dokunulmamış, P3
      last_activity: 2026-06-19
      size: unknown
      action: QUARANTINECandidate

    - name: hermes-agent-self-evolution
      path: /opt/hermes-agent-self-evolution
      reason: Deneysel proje, pasif
      last_activity: 2026-06-27
      action: QUARANTINECandidate

    - name: SalesGPT
      path: /opt/SalesGPT
      reason: Pasif, kullanılmıyor
      last_activity: 2026-06-19
      action: QUARANTINECandidate

    - name: sentry-mcp
      path: /opt/sentry-mcp
      reason: Pasif, MCP devre dışı olabilir
      last_activity: 2026-06-17
      action: QUARANTINECandidate

    - name: taste-skill
      path: /opt/taste-skill
      reason: Pasif, skill olarak kullanılmıyor
      last_activity: 2026-06-19
      action: QUARANTINECandidate

    - name: incus
      path: /opt/incus
      reason: Pasif, container management denemesi
      last_activity: 2026-06-04
      action: QUARANTINECandidate

    - name: containarium
      path: /opt/containarium
      reason: Pasif, container denemesi
      last_activity: 2026-06-04
      action: QUARANTINECandidate

    - name: hermes-codex-factory
      path: /home/hermes/hermes-codex-factory/
      reason: Pasif, 164 MB
      last_activity: unknown
      size_mb: 164
      action: QUARANTINECandidate

    - name: SkillClaw
      path: /home/hermes/SkillClaw/
      reason: Pasif, 160 MB
      last_activity: unknown
      size_mb: 160
      action: QUARANTINECandidate

    - name: creative-intelligence
      path: /home/hermes/creative-intelligence/
      reason: Pasif, 5.2 MB
      last_activity: unknown
      size_mb: 5.2
      action: QUARANTINECandidate

  archive_candidates:
    - name: notebooklm-mcp.old
      path: /opt/notebooklm-mcp.old
      reason: ".old" eki, eski versiyon
      action: ARCHIVECandidate

    - name: everything-claude-code
      path: /home/hermes/everything-claude-code/
      reason: Claude Code arşivi, 186 MB
      size_mb: 186
      action: ARCHIVECandidate

    - name: Money-printer-go-BRRR
      path: /home/hermes/Money-printer-go-BRRR/
      reason: Deneysel, 2.7 MB
      size_mb: 2.7
      action: ARCHIVECandidate

    - name: _archived (skills)
      path: ~/.hermes/skills/_archived/
      reason: 137 dosya, zaten arşivlenmiş
      files: 137
      action: ARCHIVECandidate

  duplicate_candidates:
    - pair: [ergeneai-core (/opt), ergeneai-core (/home/hermes)]
      reason: Aynı isimde iki kopya
      action: MERGECandidate

    - pair: [consolidate-memory.py, consolidate_memory.py]
      reason: Script naming inconsistency
      action: MERGECandidate

    - pair: [notebooklm-auth-check.sh, notebooklm_auth_check.sh]
      reason: Script naming inconsistency
      action: MERGECandidate

  empty_skills:
    - name: business
      path: ~/.hermes/skills/business/
      reason: Boş klasör (0 dosya)
      action: DELETECandidate

total_quarantine: 10 projects
total_archive: 4 items
total_merge: 3 pairs
total_delete: 1 empty skill
estimated_space_recovery_mb: ~500
