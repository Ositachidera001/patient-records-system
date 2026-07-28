# Q1 
#  self inside a classs method refers to the object of that class. 
#  it must be the first parameter because, it point to the object all others act on
#  no python dosen't require it to be passed.
# Q2
#  a class is a blueprint or format. e.g class of patient had the blueprint of name, age, e.t.c
#  and an instance or object is what is built based on the class (blueprint/format)
#  instance or object followed that format in giving name, age, e.t.c to each patient object created
# Q3
#  my patient class has to-dict method to help save object info into a dictionary
#  from_dict restores the diction back to cls. i dont knw d special reason 
#  but i think this is to help python know we are reserving back to class.
# Q4
#  patient(...)acts on the object in the class. we pass the object in the class,
#  to_dict returns a dictionary info of the patient. the dictionry type is stored in registry[nhis-number]
# Q5
#  inheritance is a subclass getting all the features of the main class. the subclass got name,age e.t.c only added weight and height which peculiar to pediatric.
#  ininstance(child, patient) returns true because child is a subclass of patient. by inheritance 

import os
import datetime
from pathlib import Path

def create_dummy_files(source_dir: Path):
    """Creates dummy patient files to test our organiser script."""
    source_dir.mkdir(parents=True, exist_ok=True)
    
    sample_files = [
        "blood_test_amina.pdf",
        "discharge_summary_chidi.txt",
        "chest_xray_emeka.png",
        "brain_mri_fatima.jpg",
        "unknown_document_101.xyz"
    ]
    
    for filename in sample_files:
        file_path = source_dir / filename
        if not file_path.exists():
            with open(file_path, "w") as f:
                f.write(f"Dummy content for {filename}\n")
    print("✅ Dummy test files created in source directory.\n")

def organize_hospital_files(source_dir: Path, base_reports_dir: Path):
    """Scans and organises files into categorized subfolders based on extension."""
    
    # Extension to folder mapping
    EXTENSION_MAP = {
        ".pdf": base_reports_dir / "labs",
        ".txt": base_reports_dir / "summaries",
        ".png": base_reports_dir / "imaging",
        ".jpg": base_reports_dir / "imaging"
    }
    
    unsorted_dir = base_reports_dir / "unsorted"
    
    # Category counters
    summary_counts = {
        "labs": 0,
        "summaries": 0,
        "imaging": 0,
        "unsorted": 0
    }
    
    try:
        if not source_dir.exists():
            raise FileNotFoundError(f"Source folder does not exist: {source_dir}")
        
        # Iterate over all items in the source folder
        for file_path in source_dir.glob("*"):
            if not file_path.is_file():
                continue  # Skip subfolders
            
            ext = file_path.suffix.lower()
            
            # Determine destination folder
            if ext in EXTENSION_MAP:
                dest_dir = EXTENSION_MAP[ext]
                category = dest_dir.name
            else:
                dest_dir = unsorted_dir
                category = "unsorted"
            
            # Ensure destination subfolder exists
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Target path
            destination = dest_dir / file_path.name
            
            # Move the file safely
            file_path.rename(destination)
            summary_counts[category] += 1
            print(f"📦 Moved: {file_path.name:30} ➔ {category}/")
            
        # Print summary report
        print("\n" + "="*45)
        print("📊 HOSPITAL FILE ORGANISATION SUMMARY")
        print("="*45)
        for cat, count in summary_counts.items():
            print(f"  • {cat.capitalize():12}: {count} files")
        print("="*45 + "\n")

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

def scan_report(base_dir: Path):
    """BONUS: Scans and prints a formatted inventory of all files in a directory tree."""
    print("🔍 INVENTORY SCAN REPORT")
    print("-" * 65)
    print(f"{'Filename':<30} | {'Size (KB)':<10} | {'Last Modified':<20}")
    print("-" * 65)
    
    # Recursively find all files
    for path in base_dir.glob("**/*"):
        if path.is_file():
            stat_info = path.stat()
            size_kb = stat_info.st_size / 1024
            mod_time = datetime.datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            print(f"{path.name:<30} | {size_kb:<10.2f} | {mod_time:<20}")
    print("-" * 65 + "\n")

# ── RUN SCRIPT ──────────────────────────────────────────────────
if __name__ == "__main__":
    BASE_PATH = Path.cwd() / "data"
    INCOMING_DIR = BASE_PATH / "incoming_drop"
    REPORTS_DIR = BASE_PATH / "reports"
    
    # Step 1: Create sample test files
    create_dummy_files(INCOMING_DIR)
    
    # Step 2: Run organisation process
    organize_hospital_files(INCOMING_DIR, REPORTS_DIR)
    
    # Step 3: Run bonus inventory scan
    scan_report(REPORTS_DIR)