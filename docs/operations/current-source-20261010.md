# Current source snapshot — 10 October 2026

This branch includes the server source at the existing main revision plus five previously uncommitted source additions/updates. It is a publication snapshot, not a new deployment. Production files, processes, model settings and private runtime data were not changed.

The taxpayer-specific adviser context remains private on the server; the published template obtains taxpayer facts from the existing request context. The notification recipient is configured with TELEGRAM_OWNER_CHAT_ID (or TELEGRAM_CHAT_ID), rather than a literal personal account identifier. Configure these before deploying this snapshot. No production secrets, private notes, runtime databases, screenshots or backup copies were added. SOUL.md private edits and uninstalled experimental work are excluded.

The latest architecture tests do not establish broad daily-use Jarvis acceptance. This publication does not change that status.
