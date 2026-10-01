# CybergeneOS context boundary

The panel belongs to the separate cybergene-web checkout. Copy
`context_boundary.py` into `docs/cybergeneos/server/`. From the panel repository
root, run `git apply --ignore-space-change /path/to/jeff.patch` (supports LF/CRLF).
The inspected original `server/jeff.py` SHA256 was
`5152f8e72a972502845952d0db5bdb160eccac2bd37b24a440420d6453e62e92`.
Check the deployed source before applying; other panel changes may be in flight.

Hermes and fallback requests now keep system instructions static. The real
user's request and untrusted panel data are separate JSON fields in the user
message. Escaping prevents outside content from changing the message structure.
This reduces prompt-injection exposure; it does not prove model obedience or
replace tool authorization. Scan triggers must continue to read the original
user text, not the untrusted context.

Local panel regression: 52 tests passed, including both request backends and a
forged SYSTEM instruction. This repository tests the serializer separately.
The panel source is not copied wholesale because that checkout contains other
ongoing, uncommitted user work.
