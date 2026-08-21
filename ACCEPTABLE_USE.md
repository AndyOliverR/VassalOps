# VassalOps Acceptable Use

VassalOps is a **local Windows workday agent**: teach duties, Approve, run locally.
It must not be used for crime, terrorism, exploitation, or sabotage.

## Forbidden uses (non-exhaustive)

VassalOps will **refuse**, **warn**, and **shut down** when it detects intent to:

1. **Child sexual exploitation / CSAM** — any sexual content or automation involving minors
2. **Terrorism or mass violence** — planning or assisting attacks, bombs, mass shootings, assassinations
3. **Fraud & theft** — phishing, credential stuffing/theft, ransomware, stealing OTPs/cards
4. **Non-consensual sexual abuse** — revenge porn, hidden-camera voyeurism, non-consensual deepfake porn
5. **Critical sabotage / espionage tooling** — attacking power/water/hospital/SCADA systems, exfiltrating classified secrets via this agent

## Allowed (examples)

- Teaching and replaying **your own** legitimate workday duties on machines you are authorized to use
- Demo packs (Notepad / Calculator) and local productivity automation after **Approve**
- Workspace-bounded file tools inside the VassalOps folder after Approve where required

## How enforcement works

- Chat goals and teach/run requests are scanned by a local **intent guard** before planning/Approve
- On a high-severity match: on-screen warning → refusal logged under `storage/runs/refusal-*.json` → app exits
- The action firewall still blocks unrestricted shell and dangerous hotkeys

## Limits (honest)

This is **best-effort** software policy on a local app. It cannot stop someone who modifies the code, runs without the guard, or uses other tools. It does **not** replace law enforcement. Report real-world threats to appropriate authorities.

## Contact

Security issues: see [SECURITY.md](SECURITY.md).

By using VassalOps you agree not to use it for the forbidden purposes above.
