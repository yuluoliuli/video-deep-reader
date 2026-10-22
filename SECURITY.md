# Security policy

## Supported version

Security fixes are applied to the latest published `0.1.x` release.

## Report a vulnerability

Please use GitHub's **Report a vulnerability** entry on the repository Security tab when it is available. This creates a private security advisory.

Do not include any of the following in a public issue or screenshot:

- `SESSDATA`, browser cookies, tokens, or authorization headers
- private or signed media URLs
- private video, subtitle, or frame files
- credentials in shell history, logs, or screenshots

If private reporting cannot be used, open a minimal issue asking for a private contact path. Do not disclose the full exploit or credential first.

## Security boundary

The repository does not sandbox Agent behavior or guarantee the truth of video statements. It is responsible for keeping credential handling scoped to the HTTPS Bilibili API host and for not copying credentials into generated artifacts. Media processing still depends on the security of Python, FFmpeg, the host Agent, and the user's operating system.

Reports about third-party videos, copyright, paid content, or platform access rules are not security vulnerabilities. Follow the platform's own reporting process.
