## Summary
<!-- What does this PR change and why? -->

## Checklist (maintainers / contributors)

- [ ] Change is **small and reviewable** (not a drive-by rewrite)
- [ ] Hermetic tests pass: `python -m unittest discover -s tests -p "test_*.py"`
- [ ] No `eval` / `exec` / arbitrary `subprocess` shell / hidden downloads
- [ ] No new network listeners or LAN/WAN binds by default
- [ ] Does **not** weaken Approve, `intent_guard`, action firewall, or ACCEPTABLE_USE
- [ ] No secrets, tokens, or personal duty recordings committed
- [ ] README / SECURITY / ACCEPTABLE_USE claims stay accurate
- [ ] I understand maintainers may reject opaque or untrusted blobs

## Test plan
<!-- How did you verify? -->

## Risk notes
<!-- Desktop automation, install scripts, or security-sensitive paths? -->
