# Dependency Graph
# Generated: 2026-08-17T14:15:00+03:00

core_dependencies:
  P0_CRITICAL:
    - hermes_agent (core runtime)
    - jeff_2_0 (executive layer)
    - hmpanel_postgres (database)
    - hmpanel_redis (cache)
    - hmpanel_panel (management UI)
    - hmpanel_nginx (reverse proxy)
    - hermes_config (config.yaml)
    - hermes_memory (memory data)
    - jeff_soul (SOUL.md, CEO.md, EXECUTIVE_KERNEL.md)

  P1_IMPORTANT:
    - n8n (workflow automation)
    - coolify (deployment platform)
    - coolify_redis (cache)
    - coolify_realtime (realtime)
    - ergeneai_landing (landing page)
    - dograh (application)
    - google_workspace_mcp (email/calendar)
    - beszel (monitoring)

  P2_SUPPORT:
    - kits (marketplace files)
    - spec_kit (templates)
    - jarvis_ergeneai (JARVIS integration)
    - ig_posts (Instagram outputs)
    - pipeline (data pipelines)
    - x_tweet_fetcher (Twitter)
    - instagram_mcp (Instagram)
    - hermes_scripts (152 scripts)

  P3_EXPERIMENTAL:
    - ecc_system
    - hermes_agent_self_evolution
    - SalesGPT
    - sentry_mcp
    - taste_skill
    - incus
    - containarium
    - hermes_codex_factory
    - SkillClaw
    - creative_intelligence
    - Money_printer_go_BRRR
    - everything_claude_code

dependency_chains:
  hmpanel_stack:
    - hmpanel-nginx → hmpanel-panel
    - hmpanel-panel → hmpanel-postgres
    - hmpanel-panel → hmpanel-redis
    - hmpanel-host-agent → hmpanel-panel (monitors)

  coolify_stack:
    - coolify → coolify-redis
    - coolify → coolify-realtime
    - coolify → ergeneai-landing (deployed app)

  hermes_stack:
    - hermes-agent → hermes-config
    - hermes-agent → hermes-memory
    - hermes-agent → jeff-soul
    - hermes-agent → all MCP servers
    - hermes-agent → all skills
    - hermes-agent → all plugins

  monitoring_stack:
    - beszel → beszel-agent
    - beszel-agent → docker socket (for container metrics)

single_points_of_failure:
  - hmpanel-postgres (all HM Panel data)
  - hmpanel-redis (HM Panel cache)
  - coolify-redis (Coolify cache)
  - n8n (all workflow automation)
  - hermes_config (all Hermes configuration)

circular_dependencies: none_detected
