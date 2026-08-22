"""ICM-inspired staged duty packs: folder stages + Approve gates (local only).

Stages are scoped context folders (CONTEXT.md + duty JSON), not multi-agent swarms.
Human sits between stages via Spice pending_replan / second Approve — never silent overnight desktop.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from src.execution.duty_library import VassalOpsDutyLibrary, _slugify


PACKS_SUBDIR = "packs"


def packs_root(duties_dir: str) -> str:
    return os.path.join(duties_dir, PACKS_SUBDIR)


def is_staged_pack_dir(path: str) -> bool:
    return os.path.isdir(path) and os.path.isfile(os.path.join(path, "pack.json"))


def load_pack_manifest(pack_dir: str) -> Dict[str, Any]:
    with open(os.path.join(pack_dir, "pack.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
    if not data.get("id"):
        data["id"] = _slugify(os.path.basename(pack_dir))
    data.setdefault("kind", "staged_pack")
    data.setdefault("stages", [])
    return data


def read_stage_context(pack_dir: str, stage_folder: str) -> str:
    path = os.path.join(pack_dir, stage_folder, "CONTEXT.md")
    if not os.path.isfile(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def write_stage_handoff(pack_dir: str, stage_folder: str, text: str) -> str:
    out_dir = os.path.join(pack_dir, stage_folder, "output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "handoff.md")
    body = (
        f"# Stage handoff — {stage_folder}\n\n"
        f"_Written {time.strftime('%Y-%m-%d %H:%M:%S')}_\n\n"
        f"{text.strip()}\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    return path


def list_staged_pack_dirs(duties_dir: str) -> List[str]:
    root = packs_root(duties_dir)
    if not os.path.isdir(root):
        return []
    found = []
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        if is_staged_pack_dir(path):
            found.append(path)
    return found


def import_staged_packs(library: VassalOpsDutyLibrary) -> Dict[str, Any]:
    """
    Import each stage's duty.json into the duty library.
    Returns pack ids + stage duty ids imported.
    """
    imported_duties: List[str] = []
    imported_packs: List[str] = []
    for pack_dir in list_staged_pack_dirs(library.duties_dir):
        try:
            manifest = load_pack_manifest(pack_dir)
        except Exception as exc:
            return {
                "ok": False,
                "imported_duties": imported_duties,
                "imported_packs": imported_packs,
                "error": f"{pack_dir}: {exc}",
            }
        pack_id = manifest["id"]
        for stage in manifest.get("stages") or []:
            folder = stage.get("folder") or stage.get("id")
            if not folder:
                continue
            duty_src = os.path.join(pack_dir, folder, "duty.json")
            if not os.path.isfile(duty_src):
                continue
            with open(duty_src, "r", encoding="utf-8") as f:
                duty = json.load(f)
            duty_id = duty.get("id") or stage.get("duty_id") or f"{pack_id}_{_slugify(folder)}"
            duty["id"] = duty_id
            duty.setdefault("tags", [])
            if "staged" not in duty["tags"]:
                duty["tags"].append("staged")
            if "pack" not in duty["tags"]:
                duty["tags"].append("pack")
            duty["staged_pack_id"] = pack_id
            duty["staged_folder"] = folder
            ctx = read_stage_context(pack_dir, folder)
            if ctx and not duty.get("stage_context"):
                duty["stage_context"] = ctx[:2000]
            dest = library.duty_path(duty_id)
            with open(dest, "w", encoding="utf-8") as f:
                json.dump(duty, f, indent=2)
            imported_duties.append(duty_id)
            stage["duty_id"] = duty_id
        # Persist resolved duty_ids back into pack.json for runners
        with open(os.path.join(pack_dir, "pack.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        imported_packs.append(pack_id)
    return {
        "ok": True,
        "imported_duties": imported_duties,
        "imported_packs": imported_packs,
    }


def resolve_pack_dir(duties_dir: str, pack_id: str) -> Optional[str]:
    safe = _slugify(pack_id)
    for path in list_staged_pack_dirs(duties_dir):
        try:
            mid = load_pack_manifest(path).get("id")
        except Exception:
            mid = None
        if mid == pack_id or mid == safe or _slugify(os.path.basename(path)) == safe:
            return path
    # Direct folder name
    candidate = os.path.join(packs_root(duties_dir), safe)
    if is_staged_pack_dir(candidate):
        return candidate
    return None


def checklist_labels_for_pack(manifest: Dict[str, Any]) -> List[str]:
    labels = []
    for i, stage in enumerate(manifest.get("stages") or [], start=1):
        name = stage.get("name") or stage.get("folder") or stage.get("id") or f"stage_{i}"
        gate = " → Approve gate" if stage.get("approve_after", True) else ""
        labels.append(f"Stage {i}: {name}{gate}")
    return labels


def format_needs_you_brief(*, shipped: str = "", stuck: str = "", needs_you: str = "") -> str:
    """Grockbot-style short brief, local-only (no cloud agents)."""
    return (
        f"Shipped: {(shipped or '—')[:200]}\n"
        f"Stuck: {(stuck or '—')[:200]}\n"
        f"Needs you: {(needs_you or '—')[:300]}"
    )


def run_staged_pack(
    pack_id: str,
    *,
    library: VassalOpsDutyLibrary,
    run_controller,
    ledger=None,
) -> Dict[str, Any]:
    """
    Run pack stages in order. After any stage with approve_after=True (except last),
    pause for second Approve (Spice pending_replan) before continuing.
    """
    pack_dir = resolve_pack_dir(library.duties_dir, pack_id)
    if not pack_dir:
        return {"ok": False, "error": f"Staged pack not found: {pack_id}"}
    manifest = load_pack_manifest(pack_dir)
    stages = list(manifest.get("stages") or [])
    if not stages:
        return {"ok": False, "error": "Pack has no stages."}

    labels = checklist_labels_for_pack(manifest)
    run_controller.reset_for_run(labels, phase="staged_pack")
    run_controller.set_summary(
        format_needs_you_brief(
            shipped="—",
            stuck="—",
            needs_you="Approve already granted for stage 1; later stages pause at gates.",
        )
    )

    results: List[Dict[str, Any]] = []
    for idx, stage in enumerate(stages):
        if run_controller.stop_requested():
            run_controller.finish(False, error="Stopped by user.")
            return {"ok": False, "stopped": True, "results": results, "pack_id": manifest["id"]}

        folder = stage.get("folder") or stage.get("id")
        duty_id = stage.get("duty_id")
        stage_name = stage.get("name") or folder or duty_id
        run_controller.set_progress(idx + 1, f"Stage {idx + 1}: {stage_name}")
        run_controller.set_summary(
            format_needs_you_brief(
                shipped="; ".join(
                    str(r.get("duty_id") or r.get("name") or "ok") for r in results if r.get("ok")
                )
                or "—",
                stuck="—",
                needs_you=f"Running stage {idx + 1}: {stage_name}",
            )
        )

        if ledger:
            ledger.commit_transaction(
                intent=f"staged_pack:{manifest['id']}:{duty_id}",
                status="STARTED",
                device="staged_pack",
                channel="workday",
            )

        outcome = library.run_duty(str(duty_id)) if duty_id else {"ok": False, "error": "Missing duty_id"}
        results.append(outcome)

        handoff = (
            f"**Status:** {'ok' if outcome.get('ok') else 'failed'}\n\n"
            f"**Duty:** `{duty_id}`\n\n"
            f"**Notes:** Human may edit this file before the next stage Approve.\n"
        )
        if folder:
            try:
                write_stage_handoff(pack_dir, folder, handoff)
            except Exception:
                pass

        if ledger:
            ledger.commit_transaction(
                intent=f"staged_pack:{manifest['id']}:{duty_id}",
                status="success_completed" if outcome.get("ok") else "failed",
                device="staged_pack",
                channel="workday",
            )

        if not outcome.get("ok"):
            run_controller.mark_checklist_status(idx, "failed")
            run_controller.set_summary(
                format_needs_you_brief(
                    shipped="; ".join(str(r.get("duty_id")) for r in results[:-1] if r.get("ok")) or "—",
                    stuck=f"Stage {idx + 1} failed: {outcome.get('error') or duty_id}",
                    needs_you="Fix the desktop state, then re-run the pack or teach a replacement duty.",
                )
            )
            run_controller.finish(False, error=str(outcome.get("error") or f"Stage failed: {duty_id}"))
            return {"ok": False, "results": results, "pack_id": manifest["id"], "failed_stage": idx}

        run_controller.mark_checklist_status(idx, "done")

        # Gate: Approve before next stage (ICM human seat) — skip after final stage
        approve_after = bool(stage.get("approve_after", True))
        is_last = idx >= len(stages) - 1
        if approve_after and not is_last:
            next_name = stages[idx + 1].get("name") or stages[idx + 1].get("folder") or "next stage"
            msg = (
                f"Stage {idx + 1} ({stage_name}) finished. "
                f"Review output/{folder}/handoff.md if you want, then Approve to run stage {idx + 2}: {next_name}."
            )
            run_controller.set_summary(
                format_needs_you_brief(
                    shipped=f"Stage {idx + 1}: {stage_name}",
                    stuck="—",
                    needs_you=f"Approve to continue → {next_name}",
                )
            )
            run_controller.set_pending_replan(
                msg,
                steps=[f"Continue to stage {idx + 2}: {next_name}", "Or Stop to end the pack run"],
            )
            decision = run_controller.wait_while_paused()
            if decision == "stop":
                run_controller.finish(False, error="Stopped at stage gate.")
                return {"ok": False, "stopped": True, "results": results, "pack_id": manifest["id"]}
            # continue / skip both proceed to next stage (skip = human chose to proceed without edits)
            run_controller.clear_pending_replan()

    run_controller.set_summary(
        format_needs_you_brief(
            shipped=f"All {len(stages)} stages of {manifest.get('name') or manifest['id']}",
            stuck="—",
            needs_you="None — pack complete. Edit stage output/ files anytime for the next run.",
        )
    )
    run_controller.finish(True)
    return {"ok": True, "results": results, "pack_id": manifest["id"]}
