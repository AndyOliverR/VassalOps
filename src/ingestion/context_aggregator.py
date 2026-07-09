import os
import fnmatch
from typing import List, Set

class WorkspaceContextAggregator:
    def __init__(self, root_dir: str = "c:\\VassalOps"):
        self.root_dir = os.path.abspath(root_dir)
        self.allowed_extensions: Set[str] = {'.py', '.json', '.html', '.txt', '.bat', '.sh'}
        self.ignored_dirs: Set[str] = {'.git', '__pycache__', 'cache', '.pytest_cache', 'venv', 'env'}
        self.gitignore_rules: List[str] = self._load_gitignore_rules()

    def _load_gitignore_rules(self) -> List[str]:
        """Reads a local .gitignore file if it exists and extracts active exclusion strings."""
        rules = []
        gitignore_path = os.path.join(self.root_dir, ".gitignore")
        if os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        # Ignore comments and blank entries
                        if line and not line.startswith('#'):
                            rules.append(line)
            except Exception:
                print("[VassalOps Warning] Found .gitignore file but failed to read entry indices.")
        return rules

    def _is_ignored_by_gitignore(self, relative_path: str) -> bool:
        """Evaluates whether a relative path matches any active .gitignore pattern."""
        normalized_path = relative_path.replace('\\', '/')
        for rule in self.gitignore_rules:
            # Match directly or match directory children sequences
            if fnmatch.fnmatch(normalized_path, rule) or fnmatch.fnmatch(normalized_path, f"*{rule}*"):
                return True
        return False

    def scan_workspace_text(self) -> str:
        aggregated_payload = []
        print(f"[VassalOps Brain] Recursively digesting code structures inside: {self.root_dir}")

        for root, dirs, files in os.walk(self.root_dir):
            # Enforce core directory pruners
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]

            for file in files:
                filename_root, ext_raw = os.path.splitext(file)
                ext = ext_raw.lower()

                if ext not in self.allowed_extensions:
                    continue

                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, self.root_dir)

                # Check structural .gitignore rules dynamically before processing text content
                if self._is_ignored_by_gitignore(relative_path):
                    continue

                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().strip()
                        if content:
                            file_block = f"--- FILE START: {relative_path} ---\n{content}\n--- FILE END: {relative_path} ---\n"
                            aggregated_payload.append(file_block)
                except Exception:
                    continue

        return "\n".join(aggregated_payload)

if __name__ == "__main__":
    print("[INIT] Testing WorkspaceContextAggregator + Gitignore rules...")
    aggregator = WorkspaceContextAggregator()
    payload = aggregator.scan_workspace_text()
    
    total_characters = len(payload)
    file_count = len([line for line in payload.split('\n') if "--- FILE START:" in line])
    
    print(f"[SUCCESS] Gitignore checks complete. Tracked {file_count} active text modules.")
    print(f"[METRICS] Filtered context snapshot size: {total_characters} characters.")

