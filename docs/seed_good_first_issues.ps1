# File the seeded good-first issues (run after: gh auth login)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))

gh label create "good first issue" --force --color "7057ff" --description "Good for newcomers" 2>$null
gh label create "help wanted" --force --color "008672" --description "Extra attention welcome" 2>$null

$issues = @(
  @{
    Title = "Add a second safe demo duty pack (Calculator or Paint)"
    Body = @"
## Problem
Only the Notepad demo pack exists under ``storage/duties/packs/``. A second password-free pack makes demos and CONTRIBUTING on-ramps stronger.

## Acceptance criteria
- New JSON pack under ``storage/duties/packs/`` with metadata + steps (hotkey/type_text/focus_window/wait only)
- Documented in packs README
- Importable via ``import demo pack``
- No credentials or network URLs required

## Area
``storage/duties/packs/``
"@
  },
  @{
    Title = "Improve window-title landmark matching + unit tests"
    Body = @"
## Problem
``landmark_target.focus_window_by_title`` uses simple substring match. Partial titles and multiple matches are fragile.

## Acceptance criteria
- Clearer matching rules documented in code comments
- At least one hermetic unit test with a pure helper or mocked title list
- No change to silent autopilot defaults

## Area
``src/execution/landmark_target.py``, ``tests/``
"@
  },
  @{
    Title = "Dashboard: clearer stuck/Approve copy for lay users"
    Body = @"
## Problem
Progress / stuck panel and Approve checklist wording can be clearer for non-developers.

## Acceptance criteria
- Short, plain-English strings in ``storage/dashboard/`` for Approve, Stop, Continue, Skip
- No new dependencies
- Still honest about MFA / missing windows

## Area
``storage/dashboard/client.js``, ``index.html``
"@
  },
  @{
    Title = "Docs: add optional demo GIF path under docs/"
    Body = @"
## Problem
README describes the 60s Notepad demo but has no visual. A short GIF helps Show HN / funders.

## Acceptance criteria
- ``docs/`` folder with a demo asset (GIF or PNG) of import demo pack to Approve to Notepad
- README Quick start links the asset
- No unrelated binaries

## Area
``docs/``, ``README.md``
"@
  },
  @{
    Title = "Dashboard light/dark theme toggle (localStorage)"
    Body = @"
## Problem
Dashboard is dark-only. A simple theme toggle helps accessibility and screenshots.

## Acceptance criteria
- Toggle in Settings or top nav
- Preference persisted in ``localStorage``
- Both themes readable (contrast)

## Area
``storage/dashboard/``
"@
  }
)

foreach ($i in $issues) {
  gh issue create --title $i.Title --label "good first issue,help wanted" --body $i.Body
}

Write-Host "Done. Open https://github.com/AndyOliverR/VassalOps/issues"
