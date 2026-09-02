"""Hermetic tests for local catalog crawl (no live Google login)."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.execution.action_firewall import VassalOpsActionFirewall
from src.execution.agent_tools import execute_loop_tool
from src.execution.internal_catalog import (
    capture_signed_in_sheet,
    extract_sheet_url,
    format_catalog_answer,
    internal_query_plan,
    looks_like_internal_query,
    parse_clipboard_table,
    parse_requirement,
    search_catalog,
    sheet_requested,
)
from src.execution.risk_tiers import tool_risk


CSV_BODY = """name,country,type,check_in,check_out,available,price
Hotel Roma,Italy,hotel,2026-06-01,2026-09-30,4,EUR 120/night
Lakeside Villa,Italy,villa,2026-06-01,2026-08-31,1,EUR 240/night
Hotel Milano Full,Italy,hotel,2026-06-01,2026-09-30,0,EUR 99/night
Casa Sol,Spain,villa,2026-09-01,2026-09-30,2,EUR 180/night
"""


def _write_pdf(path: Path, line1: str, line2: str) -> None:
    def _esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    stream = (
        f"BT /F1 10 Tf 72 720 Td ({_esc(line1)}) Tj ET\n"
        f"BT /F1 10 Tf 72 700 Td ({_esc(line2)}) Tj ET\n"
    )
    body = stream.encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
        ),
        b"<< /Length %d >>\nstream\n" % len(body) + body + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    parts = [b"%PDF-1.1\n"]
    offsets = [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(sum(len(p) for p in parts))
        parts.append(f"{i} 0 obj\n".encode("ascii") + obj + b"\nendobj\n")
    xref_at = sum(len(p) for p in parts)
    xref = [b"xref\n0 6\n0000000000 65535 f \n"]
    for off in offsets[1:]:
        xref.append(f"{off:010d} 00000 n \n".encode("ascii"))
    trailer = (
        f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n".encode("ascii")
    )
    path.write_bytes(b"".join(parts + xref + [trailer]))


class TestInternalCatalog(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.data = Path(self.root, "storage", "internal_data")
        self.data.mkdir(parents=True)
        Path(self.root, "config.json").write_text(
            json.dumps(
                {
                    "runtime_boundaries": {
                        "registration_github_token": "",
                        "internal_data_path": "storage/internal_data",
                        "internal_data_extra_roots": [],
                        "internal_sheets": [
                            {
                                "name": "Availability",
                                "url": "https://docs.google.com/spreadsheets/d/fixtureSheetId/edit",
                            }
                        ],
                    }
                }
            ),
            encoding="utf-8",
        )
        (self.data / "sample_availability.csv").write_text(CSV_BODY, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_parse_requirement_place_dates_type(self):
        req = parse_requirement("Client needs a hotel in Italy 12-15 June, 2 nights")
        self.assertEqual(req["place"], "italy")
        self.assertEqual(req["stay_type"], "hotel")
        self.assertIsNotNone(req["start"])
        self.assertIsNotNone(req["end"])
        self.assertEqual(req["start"].month, 6)
        self.assertEqual(req["end"].day, 15)

    def test_looks_like_internal_query(self):
        self.assertTrue(looks_like_internal_query("check availability: hotel in Italy"))
        self.assertTrue(
            looks_like_internal_query("Client needs a hotel in Italy 12-15 June, 2 nights")
        )
        self.assertFalse(looks_like_internal_query("hello there"))

    def test_italy_june_hotel_hits_and_zero_stock_flagged(self):
        answer = format_catalog_answer(
            "Client needs a hotel in Italy 2026-06-12 to 2026-06-15",
            root=self.root,
        )
        self.assertIn("Hotel Roma", answer)
        self.assertIn("EUR 120", answer)
        self.assertIn("Hotel Milano Full", answer)
        self.assertIn("Unavailable / full", answer)
        self.assertNotIn("Casa Sol", answer)

    def test_xlsx_docx_pdf_rows(self):
        try:
            import openpyxl
            from docx import Document
        except ImportError as exc:
            self.skipTest(f"catalog extras missing: {exc}")

        xlsx_path = self.data / "hotels.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["name", "country", "type", "check_in", "check_out", "available", "price"])
        ws.append(["Excel Inn", "Italy", "hotel", "2026-06-01", "2026-09-30", "2", "EUR 80"])
        wb.save(xlsx_path)

        doc = Document()
        table = doc.add_table(rows=2, cols=7)
        headers = ["name", "country", "type", "check_in", "check_out", "available", "price"]
        for i, h in enumerate(headers):
            table.rows[0].cells[i].text = h
        vals = ["Word Lodge", "Italy", "hotel", "2026-06-01", "2026-09-30", "1", "EUR 70"]
        for i, v in enumerate(vals):
            table.rows[1].cells[i].text = v
        doc.save(self.data / "hotels.docx")

        _write_pdf(
            self.data / "hotels.pdf",
            "name,country,type,check_in,check_out,available,price",
            "Pdf Suites,Italy,hotel,2026-06-01,2026-09-30,3,EUR 60",
        )

        result = search_catalog(
            "Check availability: hotel in Italy 2026-06-12 to 2026-06-15",
            root=self.root,
        )
        names = [r["name"] for _s, r in result["hits"]]
        self.assertIn("Excel Inn", names)
        self.assertIn("Word Lodge", names)
        blobs = " ".join(r.get("blob") or r.get("name") or "" for _s, r in result["hits"])
        self.assertTrue("Pdf Suites" in names or "pdf suites" in blobs.lower() or "Pdf Suites" in blobs)

    def test_google_url_flags_desktop_sheet_step(self):
        query = (
            "Check internal: hotel in Italy 2026-06-12 to 2026-06-15 "
            "https://docs.google.com/spreadsheets/d/abc123xyz/edit"
        )
        plan = internal_query_plan(query, root=self.root)
        self.assertIsNotNone(plan)
        self.assertEqual(plan["kind"], "sheet")
        self.assertIn("docs.google.com/spreadsheets/d/abc123xyz", plan["url"])
        self.assertEqual(tool_risk("read_internal_sheet"), "desktop")
        fw = VassalOpsActionFirewall()
        self.assertEqual(
            fw.verify_step({"type": "read_internal_sheet", "payload": plan["payload"]})["status"],
            "VERIFIED",
        )

    def test_named_config_sheet_without_url_in_chat(self):
        query = "Check internal Availability for hotel in Italy 2026-06-12 to 2026-06-15"
        self.assertTrue(sheet_requested(query, root=self.root))
        self.assertIn("fixtureSheetId", extract_sheet_url(query, root=self.root))
        plan = internal_query_plan(query, root=self.root)
        self.assertEqual(plan["kind"], "sheet")

    def test_local_query_is_instant_not_sheet(self):
        query = "Client needs a hotel in Italy 2026-06-12 to 2026-06-15"
        plan = internal_query_plan(query, root=self.root)
        self.assertEqual(plan["kind"], "instant")
        self.assertIn("Hotel Roma", plan["text"])

    def test_spreadsheet_word_alone_does_not_force_sheet(self):
        query = "Client needs a hotel in Italy 2026-06-12 to 2026-06-15 send pricing"
        plan = internal_query_plan(query, root=self.root)
        self.assertEqual(plan["kind"], "instant")

    def test_clipboard_table_merges(self):
        extra = parse_clipboard_table(
            "name\tcountry\ttype\tcheck_in\tcheck_out\tavailable\tprice\n"
            "Sheet Villa\tItaly\tvilla\t2026-06-01\t2026-09-30\t1\tEUR 300\n"
        )
        answer = format_catalog_answer(
            "villa in Italy 2026-06-12 to 2026-06-15",
            root=self.root,
            extra_rows=extra,
        )
        self.assertIn("Sheet Villa", answer)

    def test_capture_rejects_non_sheet_url(self):
        out = capture_signed_in_sheet("https://example.com/not-a-sheet")
        self.assertFalse(out["ok"])

    def test_public_config_token_still_empty(self):
        repo = Path(__file__).resolve().parents[1]
        cfg = json.loads((repo / "config.json").read_text(encoding="utf-8"))
        token = (cfg.get("runtime_boundaries") or {}).get("registration_github_token", "MISSING")
        self.assertEqual(token, "")
        sheets = (cfg.get("runtime_boundaries") or {}).get("internal_sheets")
        self.assertEqual(sheets, [])


class TestSearchInternalTool(unittest.TestCase):
    def test_loop_tool_reads_sample_csv(self):
        result = execute_loop_tool(
            "search_internal",
            "Check availability: hotel in Italy 2026-06-12 to 2026-06-15",
        )
        self.assertTrue(result["ok"])
        self.assertIn("Hotel Roma", result["observation"])
        self.assertIn("Hotel Milano Full", result["observation"])
        self.assertIn("Unavailable / full", result["observation"])


if __name__ == "__main__":
    unittest.main()
