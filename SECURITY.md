# Security Policy

VassalOps is a **local Windows desktop agent**. Approved actions can click and type as your logged-in user. Read this before teaching duties or exposing the optional broker.

Security writing for personal/local agents is inspired by community practices (including documentation from projects such as [OpenClaw](https://github.com/openclaw/openclaw) on untrusted input and host-side tools). VassalOps focuses on **Approve-gated desktop automation** and workday duties.

## Supported versions

| Version | Supported |
|---------|-----------|
| `main` branch | Yes — please report issues against current `main` |
| Older commits / forks | Best-effort only |

## Reporting a vulnerability

**Please do not open a public GitHub Issue for security vulnerabilities.**

1. Prefer [GitHub private vulnerability reporting](https://github.com/AndyOliverR/VassalOps/security/advisories/new) if enabled on the repository.
2. Or email the maintainer associated with GitHub user **AndyOliverR** (see profile / Sponsors) with:
   - Description of the issue
   - Steps to reproduce
   - Impact (e.g. bypass Approve, token leak, remote bind)
   - Suggested fix if you have one

We will acknowledge reports as soon as practical and coordinate disclosure.

## Threat model (honest)

- **Privilege:** Automation runs with your Windows user rights. There is no OS jail or container. A subprocess “sandbox” is timeout-only, not isolation.
- **Trust boundary:** The human **Approve / Reject** gate (and playlist Confirm) is the primary control before mouse/keyboard macros.
- **Local LLM:** Prompts may include OCR/clipboard context; secrets are redacted where the redactor runs — still treat screen content as sensitive.
- **Network:** Optional WebSocket broker defaults to **off**. When used, it must bind to `127.0.0.1` and require `broker_auth_token` from `config.json`. Do not expose it to LAN/WAN without additional hardening you own.
- **Teach mode:** `pynput` records keystrokes and clicks. Passwords typed during teach can be stored in duty/macro JSON under `storage/`. Prefer click-only flows for logins; delete sensitive duty files if recorded by mistake.
- **Replay:** Coordinate clicks are fragile; window-title / OCR landmarks help but can fail. Stuck detection pauses and asks the human to Continue — do not treat Continue as a security boundary for malicious plans you already Approved.
- **Public contributions:** Treat every PR as untrusted until reviewed. See [docs/SUPPLY_CHAIN.md](docs/SUPPLY_CHAIN.md). Protect `main` with required reviews / Code Owners. Do not run unreviewed contributor code on a machine with secrets.
- **Acceptable use:** High-severity harmful goals are refused at runtime — see [ACCEPTABLE_USE.md](ACCEPTABLE_USE.md).
- **Local PIN gate:** Chat/Approve/duties require an unlocked local account (email + PIN + secret Q/A for reset). Profile lives under `storage/auth/` (gitignored); PIN and secret answer are PBKDF2-hashed, never plaintext. This is a soft gate against casual use of an unlocked session — it is not OS-level access control (someone with disk access can still delete the profile or patch the app).
- **Installer email / GitHub notepad:** Public GitHub clones do not provide downloader emails. **Release zips** inject a scoped Issues-write PAT into `config.local.json` at publish time (Actions secret `VASSALOPS_INSTALLS_PAT`; never committed). Git clones still use gitignored `config.local.json` (see `config.local.json.example`). First signup creates a private-repo Issue (`install: email` + JSON body). Bootstrap and unlock also retry once if signup was offline. Alternate: generic `registration_endpoint` HTTPS POST. Rotate the PAT if abused.
- **Lab-rat handshake:** After the local PIN account exists, launch and close automatically use HTTPS to GitHub. **Inbound:** GitHub Releases zip (duties + `config.json` + existing `config.local.json` preserved). **Outbound:** a sanitized skill distillate (duty step *types*, generic app families, redacted lessons). Never screenshots, OCR, clipboard, file contents, coordinates, typed keystrokes, or **company inventory** (Excel/Word/PDF/CSV under `storage/internal_data` and Google Sheet grids). Set `VASSALOPS_SKIP_HANDSHAKE=1` to disable. Sponsor/star in the top bar are optional.
- **Internal catalog:** Booking/availability lookup crawls files on this PC only. Optional Google Sheet read uses the employee’s **already signed-in** Chrome/Edge after **Approve** (open URL + copy grid). No Google API, no password capture. Sheet URLs may live in `config.json` (`internal_sheets`); secrets do not.

## AI-era risks

Screen OCR, clipboard, and chat goals are **untrusted input** (prompt-injection surface). The local model may propose a plan; secrets are redacted where the redactor runs, but you still treat the plan as untrusted until you read it. **Approve** is the human judgement gate — AI can investigate and draft; you decide what runs. Same lesson as the [GitHub Secure Open Source Fund Session 4 write-up](https://github.blog/open-source/maintainers/what-50-open-source-projects-taught-us-about-security-in-the-ai-era/) (we are not a Fund participant).

## What we will not do by default

- Silent full-day autopilot without Approve
- Auto-start the broker on install
- Ship unsigned EXE as the primary lay-user install path (prefer `bootstrap_and_run.bat`)

## Antivirus false positives

Teach/replay and PyInstaller-packed launchers are commonly flagged as keylogger/RAT heuristics (e.g. K7, Windows Defender). See README. Restore only paths under your VassalOps install tree after verifying; add a folder exclusion rather than disabling AV globally.

## Safe operating checklist

1. Read every proposed plan before Approve.
2. Do not Approve teach/run while entering passwords you cannot rotate.
3. Keep `config.json` broker tokens private; never commit real tokens to public forks.
4. Stop (UI) or pyautogui failsafe (mouse to top-left corner) if automation misbehaves.

## Scope of this policy

Product limitations (UI drift, MFA, CAPTCHA) are expected; they are not vulnerabilities by themselves. Bypass of Approve, remote code without auth, or leakage of broker tokens are in scope.
