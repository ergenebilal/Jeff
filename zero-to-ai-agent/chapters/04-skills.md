# Chapter 4: Building Skills — Your Agent's Playbook

## Concept

A **skill** is a reusable instruction set for your agent. Think of it as a function in programming — instead of re-explaining how to do something, you just say "use the X skill."

Skills make your agent:
- **Faster** — No need to re-explain context
- **Consistent** — Always follows the same process
- **More capable** — Each skill adds a "muscle"

I have 37 active skills. This chapter covers how to build the most essential ones.

## Essential Skills

### Skill 1: Code Review

```bash
mkdir -p ~/.hermes/skills/code-review
cat > ~/.hermes/skills/code-review/SKILL.md << 'SKILLEOF'
---
name: code-review
version: 1.0
---

## Trigger
When the user says "review this code", "check my PR", or "audit this function".

## Process
1. Read the entire file
2. Check for: security issues, performance bottlenecks, error handling, edge cases
3. Rate each issue as CRITICAL / MAJOR / MINOR
4. Report in this format:
   ```
   ## CRITICAL (fix immediately)
   - [line:N] Description
   
   ## MAJOR (fix before deploy)
   - [line:N] Description
   
   ## MINOR (nice to have)
   - [line:N] Description
   ```
5. Do NOT rewrite the code unless asked
SKILLEOF
```

### Skill 2: Morning Briefing

```bash
cat > ~/.hermes/skills/morning-briefing/SKILL.md << 'SKILLEOF'
---
name: morning-briefing
version: 1.0
---

## Trigger
Daily at 07:00 (cron job) or when user says "günaydın" / "morning"

## Process
1. Check current date/time
2. Check server health (disk, RAM, uptime)
3. Check cron job status
4. Report in format:
   ```
   🟢 All systems nominal
   📊 Disk: XX% used | RAM: XX% | Uptime: X days
   ⏰ Scheduled tasks: X active
   🚨 Issues: [none or list]
   ```
SKILLEOF
```

### Skill 3: Opportunity Scanner

This is the money-making skill — it finds business opportunities:

```bash
cat > ~/.hermes/skills/opportunity-scan/SKILL.md << 'SKILLEOF'
---
name: opportunity-scan
version: 1.0
---

## Trigger
Daily scan or "check for opportunities" / "find leads"

## Data Sources
1. **Twitter/X**: Search for "I need an AI agent", "looking for automation", "need a chatbot"
2. **Reddit**: r/entrepreneur, r/smallbusiness — "automation" posts
3. **GitHub**: Trending AI repos
4. **Web**: Industry news

## Output Format
```
🎯 Opportunities Found: [N]
━━━━━━━━━━━━━━━━━━━

1. **[Title]** — [Brief description]
   Source: X/Reddit/GitHub | Priority: HIGH/MED/LOW
   
2. **[Title]** — [Brief description]
   Source: X/Reddit/GitHub | Priority: HIGH/MED/LOW
```
SKILLEOF
```

## How Skills Work

Your agent loads skills based on context. When you say "review this code", Hermes checks if a matching skill exists. If yes, it follows those instructions.

Skills live in `~/.hermes/skills/<skill-name>/SKILL.md`. You can also attach supporting files:

```
~/.hermes/skills/my-skill/
├── SKILL.md          # Instructions (mandatory)
├── templates/        # Reusable templates
├── references/       # API docs, guides
└── scripts/          # Python/bash scripts
```

## Verification

```bash
hermes skills list
# Should show: code-review, morning-briefing, opportunity-scan

# Test a skill:
hermes run "use code-review skill to check ~/.hermes/config.yaml"
```

## Your First Weekly Routine

Create an `agent-improvement` skill:

```bash
cat > ~/.hermes/skills/self-improve/SKILL.md << 'SKILLEOF'
---
name: self-improve
version: 1.0
---

## Trigger
Every Sunday at 09:00

## Process
1. Review code quality: scan for issues, check tests pass
2. Update dependencies: pip list --outdated
3. Clean caches: disk usage > 70% means deep clean
4. Report to user: what was improved, what needs attention
SKILLEOF
```

## Pro Tips

1. **Start small**: Don't write 10 skills at once. Write one, use it for a week, refine it.
2. **Category matters**: Organize by domain: `security/`, `devops/`, `research/`
3. **Versioning**: Add a version to each skill so you know when it's stale
4. **Kill what you don't use**: I started with 172 skills. Now I have 37. Quality > quantity.

## Next Steps

With skills in place, your agent is a specialist. In Chapter 5, we'll connect it to n8n for real workflow automation.
