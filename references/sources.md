# 来源与实现边界

核对日期：2026-10-22。

- https://github.com/yichen11818/bilibili-video-reader ：借鉴字幕优先、帧与字幕联合阅读、按时间点聚焦的思路。审查了 SKILL.md 与 scripts/read_bilibili_video.py；未在根目录 LICENSE 路径获得许可证，故未复制或改写其源码。它的自动清理、OpenAI调用和yt-dlp依赖不纳入本实现。
- https://github.com/coocA-Alex/video-digest-skill ：借鉴分类分析、画面核验、事实/观点区分和覆盖率提示。MIT，Copyright (c) 2026 coocA-Alex。未复制源代码；为保留上游归属随附其许可证文本。追更、归档及外部模型配置不纳入本技能。

本技能采集脚本为独立实现，使用 Python 标准库和 FFmpeg。上游公开文档是设计参考，不能当成这份实现的测试证明。B站接口会变化；登录或下载失败应按 manifest 处理，不伪装成功。
