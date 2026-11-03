# Verification status

## 0.1.2 release verification — 2026-11-03

- Acquisition fixes and all 15 offline behavior tests are committed in `8d35024bdcfb974d6d84c96f41cab6345c38c58f`, not an unpublished local patch. [Main-branch tests](https://github.com/yuluoliuli/video-deep-reader/actions/runs/39959096687) passed on Ubuntu / Windows with Python 3.10 / 3.13; [CodeQL](https://github.com/yuluoliuli/video-deep-reader/actions/runs/39959096991) passed for the same commit.
- [PR #3](https://github.com/yuluoliuli/video-deep-reader/pull/3) updates only `actions/setup-python@v6` to `@v7`. Its head `3054e2cbea908dd3e91ea94f66b6a204f91d96a4` passed the [four-job test matrix](https://github.com/yuluoliuli/video-deep-reader/actions/runs/41276253588) and [CodeQL](https://github.com/yuluoliuli/video-deep-reader/actions/runs/41276253590) before merge.
- This release updates documentation and skill metadata to `0.1.2`. The media and DSH acceptance below remains dated 2026-10-22/23; no new live Bilibili acquisition, DSH installation/selection, other-model compatibility, or authenticated Web UI acceptance is claimed.

## Original acceptance snapshot — 2026-10-22

The following table records the original `0.1.1` acceptance, not a current installation check. The 2026-10-23 DSH follow-up below supersedes the pending image-inspection status only for its explicitly invoked local workflow. The 0.1.2 section above supersedes the old unpublished/CI-pending status of the acquisition fixes.

| Item | Status | Evidence |
|---|---|---|
| Published CI | Pass | `test` and `CodeQL` both succeeded for the main branch and `v0.1.1` tag commit. |
| Bilibili BV acquisition | Pass | The acceptance video produced 225 timestamped segments and 99.88% subtitle time coverage. |
| `b23.tv` short link | Pass | `https://b23.tv/BV1toJR6HEVy` resolved to the same video and produced 225 timestamped segments. |
| Local video + supplied subtitles | Pass | Targeted frames were extracted from an existing local video while reusing supplied segments. |
| Missing-subtitle behavior | Pass | A subtitle-free local video returned `partial` / exit code 2, retained two usable frames, and warned that speech must not be inferred from frames. |
| Silent ASR behavior | Pass | The collector did not invoke ASR even though `faster-whisper` is installed. Automatic ASR is outside the current core scope. |
| DSH skill discovery | Pass | The DSH skill backend listed `video-deep-reader`, version `0.1.1`, from the expected shared skill path. |
| DSH UI and image inspection | Partial | The authenticated Web UI and full desktop-window interaction were not accepted in this environment. Backend discovery is verified; end-to-end Agent image inspection remains pending. |
| Social preview asset | Pass | The committed PNG is 1280×640 and valid. |
| GitHub Social preview setting | Pending | GitHub's settings upload component did not show a saved image. The asset is available for manual upload from repository Settings. |

This matrix records observed checks, not a promise that every video, account permission, region, browser, or host Agent will behave identically.

## Local checks — 2026-10-23 (subsequently committed for 0.1.2)

- All 15 offline behavior tests pass on Windows / Python 3.14. The seven added checks cover focus URLs in subtitle-only mode, malformed/nontext subtitle rows, explicit partial status, frame timeout retention, invalid CLI timestamps, and credential error redaction.
- A generated six-second local clip with SRT captions produced three representative frames at 1, 3, and 5 seconds. Follow-up frames at 0.5, 2.5, and 5.5 seconds also succeeded; actual images at 1 and 5.5 seconds were inspected.
- Missing captions retained frames and returned partial / exit 2 without ASR. Damaged JSON captions retained valid words and reported skipped rows as partial. An existing output directory was rejected without changing its manifest.
- CLI help and local patch checks passed. At that time no new Bilibili network acceptance, GitHub CI run, published release, or DSH UI acceptance was claimed; subsequent CI evidence is recorded in the 0.1.2 section above.

## DSH desktop conversation follow-up — 2026-10-23

- A user initiated an explicit skill request in the normal DSH desktop conversation. The successful `skill` call loaded the installed shared skill. Manual filesystem discovery preceded invocation, so automatic natural-language skill selection was not accepted.
- With the existing public-video cache (459.603 seconds) and 225 supplied caption segments, the installed collector returned `acquired` / exit 0, four uniform frames plus two requested timestamps, and no warnings. Subtitle time coverage was 99.97% against the local duration; the earlier 99.88% used the platform's rounded 460-second duration. Neither metric measures text accuracy.
- The DSH session recorded 16 successful `read_image` results containing image attachments: 15 in the captioned workflow (six initial frames, two repeated-timestamp follow-ups, five crops, two thumbnails), plus one without captions. All attachment SHA-256 values matched the corresponding local files. The recorded provider/model was `workbuddy-ai` / `deepseek-v4.1-flash`; no cross-model compatibility claim is made.
- A Chinese analysis and visual evidence record identified table columns, a failed-step marker, and a preview error visible in the frames. Review corrected image counts, attribution of on-screen text versus speech, and an unsupported continuous-shot inference. This accepts the evidence workflow, not error-free interpretation or independent validation of the video's claims.
- The subtitle-free run returned `partial` / exit 2 with zero segments, one retained frame, and an explicit missing-transcript warning. The session contained no ASR call. Any comparison to existing captions is a separate supplied-text source, not recovered speech.
- Follow-up extraction initially used a nonexistent output-local video path, then encountered the existing-output protection. Using the original source and a new output directory succeeded. The instructions now point to `manifest.json`'s `video_path`; no collector code change was needed for these invocation errors.
- Raw session logs, media, images, private paths, and generated reports remain outside this repository. This follow-up did not re-run current Bilibili access, CI, authenticated Web UI automation, continuous playback, or external fact checks.
