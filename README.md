# Video Deep Reader · 视频深度解读

**Experimental v0.1.0** — An Agent Skill for evidence-grounded reading of Bilibili and local videos. Collect timestamped captions and frames, inspect the actual images, then let your host agent answer with traceable evidence.

面向 Codex 等能运行 Python、查看图片的 Agent。不是把字幕扩写成文章：先取字幕与代表帧，再针对问题补帧，区分作者观点、画面证据、推断和外部核实。

## 能力

- B站 BV / 视频链接 / 指定单个分P；本地视频配 JSON、SRT、VTT 字幕。
- 平台字幕优先，默认12张全片代表帧；支持指定时间补帧。
- 原始字幕保持不变，输出来源、时间覆盖率和素材缺失状态。
- 当前Agent完成解读，不要求额外LLM API；无追更、定时任务或自动清理。

## 安装

需要 Python 3.10+、PATH 中的 FFmpeg 和 ffprobe；采集脚本仅使用标准库。

```sh
git clone https://github.com/yuluoliuli/video-deep-reader.git
```

将仓库放入你的Agent技能目录并保留目录名 `video-deep-reader`。Codex可使用 `~/.agents/skills/video-deep-reader` 或 `~/.codex/skills/video-deep-reader`。已有同名目录时不要覆盖。其他宿主需支持读取SKILL.md、执行Python、查看图片；DSH兼容性尚未完成界面验收。

向Agent发送：

> 用 video-deep-reader 解读这个B站视频，重点检查作者的结论有没有画面证据：视频链接

## 手动采集

在仓库目录运行；Windows PowerShell也适用：

```sh
python -X utf8 scripts/read_video.py BV1toJR6HEVy --out ./runs/example
python -X utf8 scripts/read_video.py "https://www.bilibili.com/video/BV1toJR6HEVy/?p=1" --cookie-file /path/to/private-cookie.txt --out ./runs/authenticated
python -X utf8 scripts/read_video.py /path/to/video.mp4 --subtitle /path/to/captions.srt --out ./runs/local
python -X utf8 scripts/read_video.py ./runs/example/video-only.mp4 --frames-only --frames 0 --times "02:42,03:11" --subtitle ./runs/example/segments.json --out ./runs/focus
```

输出目录必须是新的，避免覆盖。`--frames 0`仅取字幕；`--max-mb`设定下载上限（默认500MB）。`--times`追加指定秒数或HH:MM:SS；`--page`优先于URL里的p。b23.tv短链有实现但尚未真实验收。

平台字幕可能需要授权的SESSDATA，可用当前进程环境变量 `BILIBILI_SESSDATA` 或 `--cookie-file`传入。不要提交凭据，不要粘贴到issue。Cookie只在HTTPS B站API请求中发送，重定向会剥离凭据头。

## 输出与状态

`metadata.json`、`segments.json`、`transcript.txt`、`frames.json`、`frames/`、`manifest.json`，以及抽帧用的 `video-only.mp4`（**无音轨**）。

| 退出码 | 状态 | 含义 |
|---|---|---|
| 0 | acquired | 素材获取完成，仍需Agent读字幕、看图并分析 |
| 2 | partial | 有缺失；查看warnings，不声称完整核验 |
| 1 | failed | 失败；错误脱敏，已有素材保留 |

最终 `analysis.md` 和 `visual-evidence.md` 由宿主Agent按技能指令创建，采集脚本本身不生成结论。输出不是已验证真相；字幕时间覆盖率不代表文字准确率。

## 验证与限制

```sh
python -X utf8 scripts/test_read_video.py
```

8项离线测试覆盖字幕区间、异常片段、时间采样、分P选择、主机校验和凭据重定向。Windows/Python3.14/FFmpeg及一个7分40秒B站视频已实测：225段字幕、99.88%时间覆盖、13张实际查看的代表/补充帧。本地补帧已实测。未承诺跨平台、全部B站视频或所有宿主可用。

无字幕时不会自动转写或下载模型；可提供外挂字幕，或由Agent在获得授权后调用现有ASR工具。视频下载失败可通过用户授权浏览器查看关键位置。本技能不绕过登录、付费、地区或版权限制。稀疏帧不能证明连续操作、完整剪辑节奏或测试覆盖。

全部产物及失败残片保留，不自动删除。媒体及私人字幕不应提交到GitHub；只处理有权访问的内容。

## 来源与许可

原创实现以MIT发布，详见LICENSE。设计参考 [bilibili-video-reader](https://github.com/yichen11818/bilibili-video-reader) 与 [video-digest-skill](https://github.com/coocA-Alex/video-digest-skill)。未复制前者源码；后者MIT归属与许可证保留在references。详见 [来源说明](references/sources.md)。
