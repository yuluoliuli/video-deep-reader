# Contributing

Keep changes focused on reliable evidence acquisition and reviewable video analysis.

## Before opening a pull request

1. Run `python -X utf8 scripts/test_read_video.py`.
2. Run `python -X utf8 scripts/read_video.py --help`.
3. Check that no media, credentials, private URLs, personal paths, or generated runs are included.
4. Explain the observable behavior and any unresolved limitation.

New behavior should have a meaningful test when it affects parsing, time selection, credential routing, output status, or file safety. Do not add tests that only repeat documentation wording.

For security reports, follow [SECURITY.md](./SECURITY.md).

## Scope

Welcome: bug fixes, Bilibili compatibility fixes, local-video support, evidence-quality improvements, accessibility, and documentation corrections.

Discuss before implementing large features such as automatic ASR, hosted-model integrations, subscription tracking, a desktop UI, or background services. The current skill intentionally leaves those out of the core path.
