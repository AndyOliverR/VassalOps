# Keeping VassalOps clean (supply-chain hygiene)

VassalOps is **public**. Anyone may open a PR. That is fine — **merging or running** untrusted code is the risk, not merely reading a diff on GitHub.

## For maintainers (you)

1. **Never auto-merge** stranger PRs.
2. Enable **branch protection** on `main` (GitHub → Settings → Branches):
   - Require a pull request before merging
   - Require at least 1 approving review
   - Require review from **Code Owners** (see [`.github/CODEOWNERS`](../.github/CODEOWNERS))
   - Require status checks to pass (`CI`)
   - Do not allow force pushes to `main`
3. Review the **Files changed** tab before merge. Red flags:
   - `eval`, `exec`, `os.system`, arbitrary `subprocess` with user input
   - New outbound URLs, crypto miners, obfuscated base64 payloads
   - Changes that weaken [`intent_guard`](../src/execution/intent_guard.py), firewall, Approve, or install/update scripts
   - Large binary blobs or unexplained `.exe` drops
4. Run hermetic tests locally after merge (or trust green CI, then spot-check).
5. Keep [Dependabot](../.github/dependabot.yml) enabled for dependency alerts.

Reading a PR in the browser does **not** infect your PC. Cloning and **executing** unreviewed code can.

## For contributors

- Open a small PR with a clear why (see [CONTRIBUTING.md](../CONTRIBUTING.md)).
- Expect review; security-sensitive paths need owner approval.
- Do not submit malware “as a joke,” credential stealers, or Approve bypasses — they will be closed and may be reported.

## Runtime vs contribution safety

| Layer | Protects against |
|--------|------------------|
| PR review + CODEOWNERS + branch protection | Malicious or sloppy code entering `main` |
| CI on PRs | Broken tests; not a full malware sandbox |
| Dependabot | Known vulnerable dependencies |
| Approve + firewall + intent guard | Harmful *use* of an already-installed build |

None of these replace judgement. Determined attackers can still open bad PRs — you simply **do not merge them**.

## Acceptable use

End-user misuse (crime, terrorism, CSAM, etc.) is covered by [ACCEPTABLE_USE.md](../ACCEPTABLE_USE.md) (warn → refuse → shutdown). That is separate from contribution review.
