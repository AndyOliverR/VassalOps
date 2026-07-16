import sys
import os
import re

class VassalOpsDataSorter:
    def __init__(self, target_file: str = "storage/extracted_data/session_intel_dump.txt"):
        self.target_file = target_file
        self.output_file = "storage/extracted_data/sorted_manifest.txt"
        print("[VassalOps Sorter] Algorithmic Sorting Suite Engine initialized.")

    def run_sort_and_optimize(self) -> bool:
        """Reads raw logs, tokenizes components, filters out garbage noise, and saves sorted arrays."""
        if not os.path.exists(self.target_file):
            print(f"[VassalOps Sorter] Error: Source target data log missing at {self.target_file}")
            return False

        print(f"[VassalOps Sorter] Reading metadata lines from log stream...")
        with open(self.target_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Token categorization maps
        urls = []
        emails = []
        paths = []

        # Simple string processing parsing logic to clean arrays
        for line in lines:
            cleaned = line.strip()
            if "-> " in cleaned:
                val = cleaned.split("-> ")[1]
                if "http" in val or "github" in val:
                    urls.append(val)
                elif "@" in val:
                    emails.append(val)
                elif ":\\" in val or "c:" in val.lower():
                    paths.append(val)

        # Apply strict alphabetical and deduplication array sorting routines
        urls = sorted(list(set(urls)))
        emails = sorted(list(set(emails)))
        paths = sorted(list(set(paths)))

        manifest_buffer = (
            "======================================================\n"
            "         VassalOps OPTIMIZED DATA SORTED MANIFEST         \n"
            "======================================================\n\n"
            f" [SORTED URL REPOSITORY] (Total: {len(urls)})\n"
        )
        for u in urls: manifest_buffer += f"  -> {u}\n"

        manifest_buffer += f"\n [SORTED EMAIL CONTACTS] (Total: {len(emails)})\n"
        for e in emails: manifest_buffer += f"  -> {e}\n"

        manifest_buffer += f"\n [SORTED WORKSPACE PATHS] (Total: {len(paths)})\n"
        for p in paths: manifest_buffer += f"  -> {p}\n"
        
        manifest_buffer += "\n======================================================\n"

        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write(manifest_buffer)

        print("[VassalOps Sorter] Local extraction variables successfully optimized and sorted.")
        print(f"[VassalOps Sorter] Output manifest successfully written to: {self.output_file}")
        return True

if __name__ == "__main__":
    sorter = VassalOpsDataSorter()
    # Trigger a local run test to parse and sort our logged data files
    sorter.run_sort_and_optimize()




