# Changelog

## Unreleased

- Keep `--frames 0` subtitle-only even when a URL contains a focus timestamp.
- Retain valid subtitle rows when others are malformed, report skipped evidence as partial, and reject nontext content instead of inventing words.
- Preserve successful frame records when another frame times out or its decoder cannot start.
- Reject malformed timestamps through the CLI parser and reject control characters in credential headers without echoing their values.
- Expanded local regression coverage to 15 tests; new changes have not been pushed or validated by CI.
- Verified `b23.tv` short-link resolution end to end.
- Verified graceful subtitle-free behavior, explicit exit status, and no silent ASR invocation.
- Verified an explicitly invoked local-video workflow in a DSH desktop conversation: skill loading, acquisition, image attachments, timestamped Chinese analysis, and missing-subtitle handling. Automatic selection, other models, and Web UI automation remain unverified; report review found and corrected counting and evidence wording.
- Clarified that follow-up extraction uses `manifest.json`'s `video_path`; local videos are not copied into the output directory, and retries require a new output directory.

## 0.1.1 — 2026-10-22

- Expanded the repository landing page with a visual overview, workflow diagram, quick start, evidence model, output contract, compatibility matrix, and security boundaries.
- Added a full English README alongside the Simplified Chinese landing page.
- Added contribution and security policies, structured issue forms, CodeQL analysis, and Dependabot updates for GitHub Actions.
- Added a 1280×640 social preview and repository artwork.

## 0.1.0 — 2026-10-22

- Initial public release of the `video-deep-reader` Agent Skill.
- Added Bilibili single-video / selected-part evidence collection and local-video frame extraction.
- Added timestamped subtitle normalization, representative frames, focused follow-up frames, and explicit acquisition status.
- Added credential host scoping and redirect-header removal.
- Added eight offline tests and Windows/Linux CI.

[0.1.0]: https://github.com/yuluoliuli/video-deep-reader/releases/tag/v0.1.0
