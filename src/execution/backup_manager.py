import sys
import os
import shutil
import time

class GMAIBackupManager:
    def __init__(self, source_dir: str = "storage/extracted_data", dest_dir: str = "storage/system_backups"):
        self.source_dir = source_dir
        self.dest_dir = dest_dir
        print("[GM AI Backup] Backup Routine Manager engine initialized.")

    def execute_directory_backup(self) -> str:
        """Compresses the target extraction journals directory into a safe timestamped ZIP archive."""
        if not os.path.exists(self.source_dir):
            print(f"[GM AI Backup] Warning: Source path '{self.source_dir}' does not exist yet.")
            return "SOURCE_MISSING"

        os.makedirs(self.dest_dir, exist_ok=True)
        timestamp = time.strftime('%Y%m%d_%H%M%S', time.localtime())
        archive_name = f"gmai_intel_backup_{timestamp}"
        target_zip_path = os.path.join(self.dest_dir, archive_name)

        try:
            print(f"[GM AI Backup] Bundling file matrix blocks from '{self.source_dir}'...")
            # Automatically compress the full text journal path folder into a secure ZIP format
            shutil.make_archive(target_zip_path, 'zip', self.source_dir)
            full_output_path = f"{target_zip_path}.zip"
            print(f"[GM AI Backup] System archive successfully compiled: {os.path.basename(full_output_path)}")
            return full_output_path
        except Exception as e:
            print(f"[GM AI Backup Error] Safe archival run failed: {e}")
            return "ARCHIVE_FAILURE"

if __name__ == "__main__":
    manager = GMAIBackupManager()
    print("[GM AI] Running local backup engine validation pass...")
    result = manager.execute_directory_backup()
    print(f"[GM AI] Archive output verification target path: {result}")



