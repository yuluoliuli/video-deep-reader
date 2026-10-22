# Verification status

Last checked: 2026-10-22, skill metadata `0.1.1`.

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
