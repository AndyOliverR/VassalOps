# Seed issues (file with `gh` after `gh auth login`)

Ready-to-file good first issues for https://github.com/AndyOliverR/VassalOps

```bash
gh label create "good first issue" --force --color 7057ff --description "Good for newcomers"
gh label create "help wanted" --force --color 008672 --description "Extra attention welcome"

gh issue create --title "Add a second safe demo duty pack (Calculator or Paint)" --label "good first issue,help wanted" --body "$(cat <<'EOF'
## Problem
Only the Notepad demo pack exists under \`storage/duties/packs/\`. A second password-free pack makes demos and CONTRIBUTING on-ramps stronger.

## Acceptance criteria
- New JSON pack under \`storage/duties/packs/\` with metadata + steps (hotkey/type_text/focus_window/wait only)
- Documented in packs README
- Importable via \`import demo pack\`
- No credentials or network URLs required

## Area
\`storage/duties/packs/\`
EOF
)"

gh issue create --title "Improve window-title landmark matching + unit tests" --label "good first issue,help wanted" --body "$(cat <<'EOF'
## Problem
\`landmark_target.focus_window_by_title\` uses simple substring match. Partial titles and multiple matches are fragile.

## Acceptance criteria
- Clearer matching rules documented in code comments
- At least one hermetic unit test with mocked hwnd/title list (or pure helper extracted for test)
- No change to silent autopilot defaults

## Area
\`src/execution/landmark_target.py\`, \`tests/\`
EOF
)"

gh issue create --title "Dashboard: clearer stuck/Approve copy for lay users" --label "good first issue,help wanted" --body "$(cat <<'EOF'
## Problem
Progress / stuck panel and Approve checklist wording can be clearer for non-developers.

## Acceptance criteria
- Short, plain-English strings in \`storage/dashboard/\` for Approve, Stop, Continue, Skip
- No new dependencies
- Still honest about MFA / missing windows

## Area
\`storage/dashboard/client.js\`, \`index.html\`
EOF
)"

gh issue create --title "Docs: add optional demo GIF path under docs/" --label "good first issue,help wanted" --body "$(cat <<'EOF'
## Problem
README describes the 60s Notepad demo but has no visual. A short GIF (or static PNG sequence) helps Show HN / funders.

## Acceptance criteria
- \`docs/\` folder with a demo asset (GIF or PNG) of import demo pack → Approve → Notepad
- README Quick start links the asset
- No binaries unrelated to the demo

## Area
\`docs/\`, \`README.md\`
EOF
)"

gh issue create --title "Dashboard light/dark theme toggle (localStorage)" --label "good first issue,help wanted" --body "$(cat <<'EOF'
## Problem
Dashboard is dark-only. A simple theme toggle helps accessibility and screenshots.

## Acceptance criteria
- Toggle in Settings or top nav
- Preference persisted in \`localStorage\`
- Both themes readable (contrast)

## Area
\`storage/dashboard/\`
EOF
)"
```
