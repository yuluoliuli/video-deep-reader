<p align="right">
  <a href="./README.md">简体中文</a> · <strong>English</strong>
</p>

<p align="center">
  <img src="./assets/banner.svg" width="100%" alt="Video Deep Reader — captions, actual frames and traceable evidence">
</p>

<p align="center">
  <a href="https://github.com/yuluoliuli/video-deep-reader/actions/workflows/test.yml"><img alt="tests" src="https://github.com/yuluoliuli/video-deep-reader/actions/workflows/test.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/yuluoliuli/video-deep-reader/releases"><img alt="release" src="https://img.shields.io/github/v/release/yuluoliuli/video-deep-reader?include_prereleases"></a>
  <img alt="python 3.10+" src="https://img.shields.io/badge/python-3.10%2B-3776AB">
  <a href="./LICENSE"><img alt="MIT license" src="https://img.shields.io/github/license/yuluoliuli/video-deep-reader"></a>
</p>

<p align="center">
  <strong>Read the video. Check the evidence. Keep the receipts.</strong><br>
  An Agent Skill for turning Bilibili and local videos into timestamped captions, inspected frames, and evidence-grounded analysis.
</p>

> [!IMPORTANT]
> **Experimental v0.1.1.** Successful acquisition does not mean the video's claims are verified. The report must state what captions and images were actually inspected and what remains unverified.

## Why not another video summarizer

| Transcript-only summary | Video Deep Reader |
|---|---|
| Reads the narration only | Reads captions together with frames |
| Misses charts, demos, and result screens | Samples the whole runtime, then follows up on specific evidence |
| Treats the creator's claim as the conclusion | Separates creator claims, observed frames, model inference, and external checks |
| Stops at a completeness score | Records time coverage, missing artifacts, and unresolved limits |
| Cleans up temporary media automatically | Keeps all artifacts and partial failures by default |

It is useful for checking whether a review demonstrates a controlled comparison, whether a tutorial actually shows a successful result, whether automatic captions misspelled a product name, or what a "100% complete" title card really proves.

![Four-stage workflow: acquire, inspect, follow up, report](./assets/workflow.svg)

## Features

- Bilibili BV IDs, video URLs, a selected page, and local videos with JSON / SRT / VTT captions.
- Platform captions first, with 12 representative frames by default and targeted follow-up at `HH:MM:SS`.
- Reproducible artifacts for captions, metadata, frame inventory, time coverage, and acquisition status.
- The host Agent performs the analysis; no extra LLM API is required.
- No login, paid-content, region, or copyright bypass. No subscriptions, schedules, background services, or automatic deletion.

## Quick start

### Install

Requires Python 3.10+, plus FFmpeg and ffprobe on `PATH`. The collector uses only the Python standard library.

```sh
git clone https://github.com/yuluoliuli/video-deep-reader.git \
  ~/.agents/skills/video-deep-reader
```

Codex can also use `~/.codex/skills/video-deep-reader`. Other hosts must be able to read `SKILL.md`, run Python, and inspect images. DSH integration has not passed an interface-level acceptance test yet.

### Ask for evidence-backed analysis

```text
Use video-deep-reader to analyze this video.
Check whether the creator's claims about speed and token savings have a controlled comparison.
List the frames and timestamps you actually inspected, plus what those artifacts cannot prove.
URL: <video-url>
```

### Or collect artifacts directly

```sh
python -X utf8 scripts/read_video.py BV1toJR6HEVy --out ./runs/example
python -X utf8 scripts/read_video.py "https://www.bilibili.com/video/BV1toJR6HEVy/?p=1" --out ./runs/page-one
python -X utf8 scripts/read_video.py ./video.mp4 --subtitle ./captions.srt --out ./runs/local
```

<details>
<summary>Extract targeted follow-up frames from existing media</summary>

```sh
python -X utf8 scripts/read_video.py ./runs/example/video-only.mp4 \
  --frames-only --frames 0 \
  --times "02:42,03:11" \
  --subtitle ./runs/example/segments.json \
  --out ./runs/focus
```

</details>

<details>
<summary>Common options</summary>

| Option | Purpose |
|---|---|
| `--page N` | Select a video part; overrides `p` in the URL |
| `--frames N` | Number of representative frames; default 12, maximum 48; `0` disables extraction |
| `--times "00:30,02:42"` | Add specific timestamps |
| `--subtitle PATH` | Use an existing JSON / SRT / VTT caption file |
| `--cookie-file PATH` | Use an existing, authorized Bilibili credential file |
| `--max-mb N` | Download limit; default 500 MB |
| `--frames-only` | Extract supplemental frames from an existing local video |

</details>

## Output contract

```text
runs/example/
├── metadata.json       # source, title, creator, part, duration
├── segments.json       # normalized caption segments
├── transcript.txt      # readable timestamped transcript
├── frames.json         # timestamps, paths, nearby captions, review state
├── frames/*.jpg        # inspected and supplemental frames
├── video-only.mp4      # video-only stream used for frames; no audio
└── manifest.json       # status, coverage, warnings, failures
```

| Status | Exit code | Meaning |
|---|---:|---|
| `acquired` | 0 | Acquisition finished; the Agent must still inspect captions, inspect images, and write the analysis |
| `partial` | 2 | Artifacts are missing; answer what is possible and state the limits |
| `failed` | 1 | Acquisition failed; existing artifacts and a redacted error are retained |

The host Agent writes `analysis.md` and `visual-evidence.md` according to the Skill. The collector itself does not generate conclusions.

## What evidence looks like

| Time | Type | Observation | Supports | Does not prove |
|---|---|---|---|---|
| `02:42` | Creator claim | Two tasks are proposed | The demonstration's goal | Both tasks completed |
| `03:11` | Observed frame | A page is being scrolled | The page appeared | Every requested field was collected |
| `04:12` | Observed frame | A results page and table are visible | A result and a missing-data record were produced | The data are correct |
| `06:13` | Model inference | A sample form illustrates handoff | The creator proposed the concept | A real site passed testing |

Caption time coverage measures elapsed time, not text accuracy. There is no "100% video understanding" score.

## Verified and unverified

Verified:

- Local acceptance on Windows with Python 3.14 and FFmpeg.
- One 7-minute 40-second Bilibili video: 225 timestamped segments, 99.88% time coverage, and 13 representative or follow-up frames actually inspected.
- Local-video reuse and targeted frame extraction.
- Eight offline behavior tests and GitHub Actions on Ubuntu / Windows with Python 3.10 / 3.13.
- Credentials are scoped to the HTTPS Bilibili API host; `Cookie` and `Authorization` headers are removed on redirects.

Not yet verified:

- The complete download path for `b23.tv` short links.
- Every Bilibili video, region, account permission, or anti-bot state.
- Automatic activation and image inspection inside the DSH interface.
- Automatic ASR when captions are absent. The current collector expects supplied captions or an explicitly authorized follow-up transcription.

## Security and privacy

- Credentials may be supplied explicitly but are not copied into artifacts, logs, or the repository.
- Videos, captions, frames, and private media remain local by default. Never attach them to a public issue.
- The tool contains no deletion logic and does not clean partial failures automatically.
- Process only content you are authorized to access and use. Do not upload complete copyrighted video files to issues.
- See [SECURITY.md](./SECURITY.md) for reporting.

## Repository layout

```text
.
├── SKILL.md                  # Agent workflow and decision rules
├── scripts/read_video.py     # deterministic, LLM-free acquisition
├── scripts/test_read_video.py
├── references/               # analysis method, sources, upstream license
├── agents/openai.yaml        # Codex Skill metadata
└── .github/                  # CI, CodeQL, and issue forms
```

## Development

```sh
python -X utf8 scripts/test_read_video.py
python -X utf8 scripts/read_video.py --help
```

See [CONTRIBUTING.md](./CONTRIBUTING.md) for contribution requirements and [CHANGELOG.md](./CHANGELOG.md) for version history.

## Sources and license

The original implementation is released under the [MIT License](./LICENSE). The design references [bilibili-video-reader](https://github.com/yichen11818/bilibili-video-reader) and [video-digest-skill](https://github.com/coocA-Alex/video-digest-skill). No source code was copied from the former; the latter's MIT attribution and license are preserved under [references](./references/sources.md).
