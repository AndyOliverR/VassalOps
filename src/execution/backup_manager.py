import sys
import os
import shutil
import time

class VassalOpsBackupManager:
    def __init__(self, source_dir: str = "storage/extracted_data", dest_dir: str = "storage/system_backups"):
        self.source_dir = source_dir
        self.dest_dir = dest_dir
        print("[VassalOps Backup] Backup Routine Manager engine initialized.")

    def execute_directory_backup(self) -> str:
        """Compresses the target extraction journals directory into a safe timestamped ZIP archive."""
        if not os.path.exists(self.source_dir):
            print(f"[VassalOps Backup] Warning: Source path '{self.source_dir}' does not exist yet.")
            return "SOURCE_MISSING"

        os.makedirs(self.dest_dir, exist_ok=True)
        timestamp = time.strftime('%Y%m%d_%H%M%S', time.localtime())
        archive_name = f"VassalOps_intel_backup_{timestamp}"
        target_zip_path = os.path.join(self.dest_dir, archive_name)

        try:
            print(f"[VassalOps Backup] Bundling file matrix blocks from '{self.source_dir}'...")
            # Automatically compress the full text journal path folder into a secure ZIP format
            shutil.make_archive(target_zip_path, 'zip', self.source_dir)
            full_output_path = f"{target_zip_path}.zip"
            print(f"[VassalOps Backup] System archive successfully compiled: {os.path.basename(full_output_path)}")
            return full_output_path
        except Exception as e:
            print(f"[VassalOps Backup Error] Safe archival run failed: {e}")
            return "ARCHIVE_FAILURE"

if __name__ == "__main__":
    manager = VassalOpsBackupManager()
    print("[VassalOps] Running local backup engine validation pass...")
    result = manager.execute_directory_backup()
    print(f"[VassalOps] Archive output verification target path: {result}")




