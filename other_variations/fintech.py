"""
fintech.py — Financial Statement Archival System
Demonstrates copytree, make_archive, and disk usage checks on dummy PDF records.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path


def run_statement_backup():
    base_dir = Path(__file__).parent
    statements_dir = base_dir / "statements"
    backup_root = base_dir / "fintech_backups"

    # Step 1: Initialize dummy PDF files
    statements_dir.mkdir(parents=True, exist_ok=True)
    dummy_files = [
        "customer_john_doe_jan.pdf",
        "customer_jane_smith_jan.pdf",
        "customer_acme_corp_feb.pdf",
        "customer_global_tech_feb.pdf"
    ]
    
    for filename in dummy_files:
        file_path = statements_dir / filename
        if not file_path.exists():
            file_path.write_text(f"Dummy statement content for {filename}\n")

    print(f"📄 Created/Verified {len(dummy_files)} dummy statements in '{statements_dir.name}/'.")

    # Step 2: Full directory backup with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d")
    backup_dest = backup_root / f"statements_backup_{timestamp}"
    
    try:
        shutil.copytree(statements_dir, backup_dest, dirs_exist_ok=True)
        print(f"✅ [Copytree] Folder backed up to: {backup_dest.name}")
    except Exception as err:
        print(f"❌ Directory copy failed: {err}")
        return

    # Step 3: Archive into ZIP format
    archive_base = backup_root / f"statements_archive_{timestamp}"
    archive_path_str = shutil.make_archive(
        base_name=str(archive_base),
        format="zip",
        root_dir=str(backup_root),
        base_dir=backup_dest.name
    )
    
    archive_path = Path(archive_path_str)

    # Step 4: Summary & Metrics Printing
    copied_files = list(backup_dest.glob("*.pdf"))
    archive_size_kb = archive_path.stat().st_size / 1024
    disk_info = shutil.disk_usage(base_dir)

    print("\n📊 --- BACKUP WORKFLOW METRICS ---")
    print(f" Files Backed Up : {len(copied_files)}")
    print(f" Archive Created : {archive_path.name}")
    print(f" Archive Size    : {archive_size_kb:.2f} KB")
    print(f" Available Space : {disk_info.free / (1024**3):.2f} GB")
    print("----------------------------------")


if __name__ == "__main__":
    run_statement_backup()