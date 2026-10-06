# Continuous voice protocol reference — P50, 2026-10-06

This patch adapts protocol and conversation-lifecycle patterns. It does not install
LiveKit or Pipecat, replace Hermes Jeff, change business tools, or widen permissions.

## Primary references

- [Pipecat Gemini Live adapter, reviewed revision f612c0e](https://github.com/pipecat-ai/pipecat/blob/f612c0e2a3623bed9e29bd8c8751327095f24cff/src/pipecat/services/google/gemini_live/llm.py):
  one completed tool result per call; scheduling is inside the `response` object;
  content fields are processed before turn completion; tool execution and playback
  interruption have separate lifecycles. Pipecat is BSD-2-Clause licensed.
- [Google Live tool protocol](https://ai.google.dev/gemini-api/docs/live-api/tools):
  match each function response to its call ID/name and put asynchronous scheduling
  in its response payload. SSE sentence boundaries do not create new tool calls.
- [LiveKit function tool lifecycle](https://docs.livekit.io/agents/logic/tools/definition/):
  interruption of speech does not, by itself, cancel work or authorize its replay.

## Applied boundary

1. A consultation is admitted and completed in the existing durable server journal.
   Accepted/progress and partial text are not submitted as completed function results.
2. The audio provider receives one full canonical answer with `SILENT` scheduling.
   It no longer receives a progress completion, sentence completions and an empty
   final completion for the same ID. Legacy outer `willContinue`/`scheduling` fields
   are not sent.
3. Completed ID replay receives a cached `SILENT` result. An exact same-question
   provider retry within the same user utterance cannot re-execute an unknown result.
   A real subsequent user utterance resets this per-utterance protection.
4. The next question cannot inherit speaking permission from the previous answer.
   Provider input is checked even when local microphone activity was missed.
5. The context bridge records the canonical Hermes answer once. Voice paraphrases,
   progress and interrupted playback are not substituted for that answer.
6. Native speech-model tool selection is not request admission. Each completed
   Turkish input transcript is submitted once to the existing Jeff journal even
   if the audio model never calls a tool. Native tool arguments cannot rewrite the
   human request or drop a restriction such as “do not start work”. Native IDs
   bind to that request and only receive cached completion responses.
7. Native generated speech and its paraphrased output transcript are discarded.
   The existing streaming speech endpoint reads the canonical Jeff answer directly.
   Unknown outcomes are stated literally and never converted to cached factual
   speech. Continuous microphone capture and immediate local playback interruption
   remain in place; interruption does not resubmit the job.
8. General Jeff consultations are queued. Context is captured when a queued
   question starts, after the preceding answer, rather than before it is available.
   Ending the call prevents queued questions from being submitted later.

## Limits

This is a protocol/lifecycle correction, not a complete transport migration.
Provider failures, slow Hermes inference, physical microphone acoustics and mobile
network changes still require separate evidence. Identical text deduplication is
not a semantic proof that different wording describes a different real-world action;
business authorization and durable operation identity remain server responsibilities.

Tests in `test_live_protocol.cjs` reproduce the old defects against the exact previous
asset and exercise repeated turns, late transcription, cache replay, permission
isolation and unknown-result replay protection. Existing continuous-call recovery,
interruption, owner scope and actual microphone frame tests remain in the suite.
This does not establish ChatGPT-equivalent latency or physical phone acceptance.
The speech recognizer and canonical TTS still depend on the existing Google service;
the actual Hermes model can time out independently. Synthetic browser acceptance
must distinguish a native generated transcript from audio actually scheduled by
the canonical speech path.
